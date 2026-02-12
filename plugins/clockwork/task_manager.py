import asyncio
import importlib
import json
import time
import traceback
from typing import Any

from apscheduler.events import EVENT_JOB_MISSED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import logger
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from .task_models import TaskConfig, TaskExecutionHistory, TaskGroupMapping


class TaskManager:
    """定时任务管理器 - 统一管理所有定时任务"""

    def __init__(self, scheduler: AsyncIOScheduler, engine: Engine):
        self.scheduler = scheduler
        self.engine = engine
        self.logger = logger
        self._job_func = None  # 由 TaskExecutor 设置

        # 只监听 missed 事件（成功/失败由 TaskExecutor 处理）
        self.scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)

    def set_job_func(self, func):
        """设置任务执行函数（由 TaskExecutor.execute 提供）"""
        self._job_func = func

    def add_job_to_scheduler(self, task: "TaskConfig"):
        """将任务添加到 APScheduler"""
        if not self._job_func:
            raise RuntimeError("TaskExecutor 未设置，请先调用 set_job_func()")

        trigger_args = json.loads(task.trigger_args)
        self.scheduler.add_job(
            func=self._job_func,
            trigger=task.trigger_type,
            id=task.job_id,
            args=[task.job_id],
            misfire_grace_time=task.misfire_grace_time,
            replace_existing=True,
            **trigger_args,
        )

        if not task.enabled:
            self.scheduler.pause_job(task.job_id)

    # ==================== 任务配置管理 ====================

    async def register_task(
        self,
        job_id: str,
        name: str,
        handler_module: str,
        handler_function: str,
        trigger_type: str,
        trigger_args: dict,
        group_ids: list[int],
        description: str | None = None,
        enabled: bool = True,
        misfire_grace_time: int = 60,
    ) -> TaskConfig:
        """注册新任务到数据库和调度器"""
        with Session(self.engine) as session:
            # 检查任务是否已存在
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)
            existing_task = session.exec(statement).first()

            if existing_task:
                self.logger.info(f"任务 {job_id} 已存在，跳过注册")
                return existing_task

            # 创建任务配置
            task = TaskConfig(
                job_id=job_id,
                name=name,
                description=description,
                handler_module=handler_module,
                handler_function=handler_function,
                trigger_type=trigger_type,
                trigger_args=json.dumps(trigger_args),
                enabled=enabled,
                misfire_grace_time=misfire_grace_time,
            )
            session.add(task)
            session.commit()
            session.refresh(task)

            # 添加群组映射
            for group_id in group_ids:
                mapping = TaskGroupMapping(
                    job_id=job_id,
                    group_id=group_id,
                )
                session.add(mapping)
            session.commit()

            self.logger.info(f"任务 {job_id} 注册成功")
            return task

    async def update_task_trigger(self, job_id: str, trigger_type: str, trigger_args: dict) -> bool:
        """修改任务触发器"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)

            task = session.exec(statement).first()
            if not task:
                self.logger.warning(f"任务 {job_id} 不存在")
                return False

            # 更新数据库
            task.trigger_type = trigger_type
            task.trigger_args = json.dumps(trigger_args)
            task.updated_at = int(time.time())
            session.add(task)
            session.commit()

            # 更新APScheduler
            try:
                self.scheduler.reschedule_job(job_id, trigger=trigger_type, **trigger_args)
                self.logger.info(f"任务 {job_id} 触发器已更新")
                return True
            except Exception as e:
                self.logger.error(f"更新任务 {job_id} 触发器失败: {e}")
                return False

    async def update_task_groups(self, job_id: str, group_ids: list[int]) -> bool:
        """修改任务推送群组"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)

            task = session.exec(statement).first()
            if not task:
                self.logger.warning(f"任务 {job_id} 不存在")
                return False

            # 删除旧的群组映射
            statement = select(TaskGroupMapping).where(TaskGroupMapping.job_id == job_id)
            old_mappings = session.exec(statement).all()
            for mapping in old_mappings:
                session.delete(mapping)

            # 添加新的群组映射
            for group_id in group_ids:
                mapping = TaskGroupMapping(job_id=job_id, group_id=group_id)
                session.add(mapping)

            task.updated_at = int(time.time())
            session.add(task)
            session.commit()

            self.logger.info(f"任务 {job_id} 群组配置已更新")
            return True

    async def enable_task(self, job_id: str) -> bool:
        """启用任务"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)

            task = session.exec(statement).first()
            if not task:
                self.logger.warning(f"任务 {job_id} 不存在")
                return False

            task.enabled = True
            task.updated_at = int(time.time())
            session.add(task)
            session.commit()

            # 恢复或重新添加到 APScheduler
            try:
                self.scheduler.resume_job(job_id)
                self.logger.info(f"任务 {job_id} 已启用")
            except Exception:
                # 任务不在 scheduler 中，重新添加
                try:
                    session.refresh(task)
                    self.add_job_to_scheduler(task)
                    self.logger.info(f"任务 {job_id} 已重新添加到调度器并启用")
                except Exception as e:
                    self.logger.error(f"无法将任务 {job_id} 添加到调度器: {e}")

            return True

    async def disable_task(self, job_id: str) -> bool:
        """禁用任务（暂停）"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)

            task = session.exec(statement).first()
            if not task:
                self.logger.warning(f"任务 {job_id} 不存在")
                return False

            task.enabled = False
            task.updated_at = int(time.time())
            session.add(task)
            session.commit()

            # 暂停APScheduler任务
            try:
                self.scheduler.pause_job(job_id)
                self.logger.info(f"任务 {job_id} 已禁用")
            except Exception as e:
                # 任务可能还未注册到 scheduler，这是正常的
                self.logger.warning(f"无法在 scheduler 中暂停任务 {job_id}: {e}")

            return True

    async def delete_task(self, job_id: str) -> bool:
        """删除任务"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)

            task = session.exec(statement).first()
            if not task:
                self.logger.warning(f"任务 {job_id} 不存在")
                return False

            # 删除群组映射
            statement = select(TaskGroupMapping).where(TaskGroupMapping.job_id == job_id)
            mappings = session.exec(statement).all()
            for mapping in mappings:
                session.delete(mapping)

            # 删除任务配置
            session.delete(task)
            session.commit()

            # 从APScheduler中移除
            try:
                self.scheduler.remove_job(job_id)
            except Exception as e:
                self.logger.warning(f"任务 {job_id} 不在调度器中: {e}")

            self.logger.info(f"任务 {job_id} 已删除")
            return True

    # ==================== 任务查询 ====================

    async def get_task(self, job_id: str) -> TaskConfig | None:
        """获取任务配置"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)
            return session.exec(statement).first()

    async def list_tasks(self, enabled: bool | None = None, keyword: str | None = None) -> list[TaskConfig]:
        """列出任务。enabled=True 只返回启用的，enabled=False 只返回禁用的，enabled=None 返回全部"""
        with Session(self.engine) as session:
            statement = select(TaskConfig)

            if enabled is not None:
                statement = statement.where(TaskConfig.enabled == enabled)

            if keyword:
                statement = statement.where(
                    (TaskConfig.name.contains(keyword)) | (TaskConfig.job_id.contains(keyword))  # type: ignore
                )

            results = session.exec(statement).all()
            return list(results)

    async def get_task_groups(self, job_id: str) -> list[int]:
        """获取任务的推送群组"""
        with Session(self.engine) as session:
            statement = select(TaskGroupMapping).where(TaskGroupMapping.job_id == job_id)
            mappings = session.exec(statement).all()
            return [mapping.group_id for mapping in mappings]

    # ==================== 执行历史 ====================

    async def log_execution(
        self,
        job_id: str,
        status: str,
        execution_time: int,
        duration_ms: int | None = None,
        error_message: str | None = None,
        error_traceback: str | None = None,
        groups_sent: list[int] | None = None,
        messages_sent: int = 0,
        scheduled_time: int | None = None,
    ) -> None:
        """记录任务执行历史"""
        with Session(self.engine) as session:
            history = TaskExecutionHistory(
                job_id=job_id,
                execution_time=execution_time,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message,
                error_traceback=error_traceback,
                groups_sent=json.dumps(groups_sent) if groups_sent else None,
                messages_sent=messages_sent,
                scheduled_time=scheduled_time,
            )
            session.add(history)

            # 更新任务统计信息
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)

            task = session.exec(statement).first()
            if task:
                task.last_run_time = execution_time
                task.total_runs += 1
                if status == "success":
                    task.success_runs += 1
                elif status == "failed":
                    task.failed_runs += 1

                # 从 APScheduler 同步 next_run_time
                try:
                    job = self.scheduler.get_job(job_id)
                    if job and job.next_run_time:
                        task.next_run_time = int(job.next_run_time.timestamp())
                    else:
                        task.next_run_time = None
                except Exception:
                    pass

                session.add(task)

            session.commit()

    async def get_execution_history(
        self,
        job_id: str | None = None,
        limit: int = 50,
        status: str | None = None,
    ) -> list[TaskExecutionHistory]:
        """查询执行历史"""
        with Session(self.engine) as session:
            statement = select(TaskExecutionHistory)

            if job_id:
                statement = statement.where(TaskExecutionHistory.job_id == job_id)

            if status:
                statement = statement.where(TaskExecutionHistory.status == status)

            statement = statement.order_by(TaskExecutionHistory.execution_time.desc()).limit(limit)  # type: ignore
            results = session.exec(statement).all()
            return list(results)

    async def get_task_statistics(self, job_id: str) -> dict[str, Any]:
        """获取任务统计信息"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)

            task = session.exec(statement).first()
            if not task:
                return {}

            # 获取最近执行记录
            statement = (
                select(TaskExecutionHistory)
                .where(TaskExecutionHistory.job_id == job_id)
                .order_by(TaskExecutionHistory.execution_time.desc())  # type: ignore
                .limit(10)
            )
            recent_history = session.exec(statement).all()

            return {
                "job_id": task.job_id,
                "name": task.name,
                "enabled": task.enabled,
                "total_runs": task.total_runs,
                "success_runs": task.success_runs,
                "failed_runs": task.failed_runs,
                "success_rate": task.success_runs / task.total_runs if task.total_runs > 0 else 0,
                "last_run_time": task.last_run_time,
                "next_run_time": task.next_run_time,
                "recent_history": [
                    {"execution_time": h.execution_time, "status": h.status, "duration_ms": h.duration_ms}
                    for h in recent_history
                ],
            }

    # ==================== 事件监听 ====================

    def _on_job_missed(self, event):
        """APScheduler missed事件回调 - 任务因超过 misfire_grace_time 被跳过"""
        job_id = event.job_id
        asyncio.create_task(
            self.log_execution(
                job_id=job_id,
                status="missed",
                execution_time=int(time.time() * 1000),
                scheduled_time=int(event.scheduled_run_time.timestamp() * 1000)
                if event.scheduled_run_time
                else None,
            )
        )
        self.logger.warning(f"任务 {job_id} 执行被跳过 (missed)")

    # ==================== 任务初始化 ====================

    async def initialize(self):
        """初始化时同步群组配置到EnvConfig"""
        from utils.configs import EnvConfig

        # job_id 到 EnvConfig 键名的映射
        JOB_ID_TO_CONFIG_KEY = {
            "apod_everyday": "APOD_GROUP_ID",
            "earth_now": "EARTH_NOW_GROUP_ID",
            "eq_cenc": "EARTHQUAKE_GROUP_ID",
            "eq_usgs": "EARTHQUAKE_GROUP_ID",
            "daily_news": "NEWS_SUMMARY_GROUP_ID",
            "happy_new_year": None,  # 特殊处理：发送所有群
        }

        tasks = await self.list_tasks()

        for task in tasks:
            group_ids = await self.get_task_groups(task.job_id)
            config_key = JOB_ID_TO_CONFIG_KEY.get(task.job_id)
            if config_key:
                setattr(EnvConfig, config_key, group_ids)
                self.logger.info(f"同步群组配置: {config_key} = {group_ids}")


class TaskExecutor:
    """任务执行器 - 包装原始任务函数，添加监控和群组管理"""

    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager

    async def execute(self, job_id: str) -> None:
        """
        执行任务的统一入口
        1. 检查任务是否启用
        2. 获取任务配置和群组列表
        3. 执行原始任务函数
        4. 记录执行结果
        """
        start_time = time.time()
        execution_time = int(start_time * 1000)

        try:
            # 获取任务配置
            task = await self.task_manager.get_task(job_id)
            if not task or not task.enabled:
                await self.task_manager.log_execution(job_id, "skipped", execution_time)
                return

            # 动态导入任务处理函数
            handler = self._load_handler(task.handler_module, task.handler_function)

            # 获取推送群组
            group_ids = await self.task_manager.get_task_groups(job_id)

            # 执行任务（原始函数内部会读取EnvConfig）
            await handler()

            # 记录成功
            duration = int((time.time() - start_time) * 1000)
            await self.task_manager.log_execution(
                job_id=job_id,
                status="success",
                execution_time=execution_time,
                duration_ms=duration,
                groups_sent=group_ids,
                messages_sent=len(group_ids),
            )

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            await self.task_manager.log_execution(
                job_id=job_id,
                status="failed",
                execution_time=execution_time,
                duration_ms=duration,
                error_message=str(e),
                error_traceback=traceback.format_exc(),
            )
            self.task_manager.logger.error(f"任务 {job_id} 执行失败: {e}")

    def _load_handler(self, module_name: str, function_name: str):
        """动态加载任务处理函数"""
        module = importlib.import_module(module_name)
        return getattr(module, function_name)
