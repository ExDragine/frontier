import asyncio
import importlib
import json
import time
import traceback
from typing import Any

from apscheduler.events import EVENT_JOB_MISSED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import logger
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from utils.database import ensure_database_performance_indexes

from .task_models import ScheduledTaskMetadata, TaskConfig, TaskExecutionHistory, TaskGroupMapping, TaskRunResult


class TaskManager:
    """定时任务管理器 - 统一管理所有定时任务"""

    AGENT_TASK_HANDLER_MODULE = "plugins.clockwork.agent_task_handler"
    AGENT_TASK_HANDLER_FUNCTION = "run_agent_task"

    JOB_ID_TO_CONFIG_KEY = {
        "apod_everyday": "APOD_GROUP_ID",
        "earth_now": "EARTH_NOW_GROUP_ID",
        "eq_usgs": "EARTHQUAKE_GROUP_ID",
        "daily_news": "NEWS_SUMMARY_GROUP_ID",
        "nrc_merchant_alert": "NRC_MERCHANT_GROUP_ID",
        "happy_new_year": None,  # 特殊处理：发送所有群
    }

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

    def ensure_schema(self) -> None:
        """补齐 create_all 不会自动添加的轻量 schema 变更。"""
        inspector = inspect(self.engine)
        table_names = set(inspector.get_table_names())
        if "taskexecutionhistory" in table_names:
            columns = {column["name"] for column in inspector.get_columns("taskexecutionhistory")}
            if "output_summary" not in columns:
                with self.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE taskexecutionhistory ADD COLUMN output_summary VARCHAR"))
        ensure_database_performance_indexes(self.engine)

    def add_job_to_scheduler(self, task: TaskConfig):
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
        metadata: ScheduledTaskMetadata | dict[str, Any] | None = None,
    ) -> TaskConfig:
        """注册新任务到数据库和调度器"""
        with Session(self.engine) as session:
            # 检查任务是否已存在
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)
            existing_task = session.exec(statement).first()

            if existing_task:
                updated = False
                new_trigger_args_str = json.dumps(trigger_args, sort_keys=True)
                old_trigger_args_str = json.dumps(
                    json.loads(existing_task.trigger_args)
                    if isinstance(existing_task.trigger_args, str)
                    else existing_task.trigger_args,
                    sort_keys=True,
                )

                if existing_task.trigger_type != trigger_type or old_trigger_args_str != new_trigger_args_str:
                    self.logger.info(
                        f"任务 {job_id} 触发器变更: {existing_task.trigger_type}/{old_trigger_args_str} → {trigger_type}/{new_trigger_args_str}"
                    )
                    try:
                        self.scheduler.reschedule_job(job_id, trigger=trigger_type, **trigger_args)
                    except Exception as e:
                        self.logger.error(f"更新调度器任务 {job_id} 失败: {e}")
                        return existing_task
                    existing_task.trigger_type = trigger_type
                    existing_task.trigger_args = new_trigger_args_str
                    existing_task.updated_at = int(time.time())
                    updated = True

                if (
                    existing_task.handler_module != handler_module
                    or existing_task.handler_function != handler_function
                ):
                    existing_task.handler_module = handler_module
                    existing_task.handler_function = handler_function
                    existing_task.updated_at = int(time.time())
                    updated = True

                # 同步群组
                old_groups = [
                    m.group_id
                    for m in session.exec(select(TaskGroupMapping).where(TaskGroupMapping.job_id == job_id)).all()
                ]
                new_groups = sorted(set(group_ids))
                if old_groups != new_groups:
                    for m in session.exec(select(TaskGroupMapping).where(TaskGroupMapping.job_id == job_id)).all():
                        session.delete(m)
                    for gid in new_groups:
                        session.add(TaskGroupMapping(job_id=job_id, group_id=gid))
                    updated = True

                if updated:
                    session.add(existing_task)
                    session.commit()
                    session.refresh(existing_task)
                    self._sync_group_config(job_id, group_ids)
                    self.logger.info(f"任务 {job_id} 已更新")
                else:
                    self.logger.info(f"任务 {job_id} 已存在且配置未变，跳过")
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

            # 添加群组映射
            for group_id in sorted(set(group_ids)):
                mapping = TaskGroupMapping(
                    job_id=job_id,
                    group_id=group_id,
                )
                session.add(mapping)

            if metadata:
                if isinstance(metadata, ScheduledTaskMetadata):
                    task_metadata = metadata
                    task_metadata.job_id = job_id
                else:
                    task_metadata = ScheduledTaskMetadata(job_id=job_id, **metadata)
                session.add(task_metadata)

            try:
                self.add_job_to_scheduler(task)
            except Exception:
                session.rollback()
                raise

            try:
                session.commit()
                session.refresh(task)
            except Exception:
                try:
                    self.scheduler.remove_job(job_id)
                except Exception as cleanup_error:
                    self.logger.warning(f"回滚调度器任务 {job_id} 失败: {cleanup_error}")
                raise

            self._sync_group_config(job_id, group_ids)

            self.logger.info(f"任务 {job_id} 注册成功")
            return task

    async def register_scheduled_task(
        self,
        *,
        job_id: str,
        name: str,
        prompt: str,
        trigger_type: str,
        trigger_args: dict,
        owner_user_id: str,
        target_type: str,
        target_id: str | int,
        description: str | None = None,
        enabled: bool = True,
        misfire_grace_time: int = 300,
        created_from: str = "tool",
        delivery_mode: str = "final",
    ) -> TaskConfig:
        """注册统一的用户自动任务。"""
        group_ids = [int(target_id)] if target_type == "group" else []
        return await self.register_task(
            job_id=job_id,
            name=name,
            handler_module=self.AGENT_TASK_HANDLER_MODULE,
            handler_function=self.AGENT_TASK_HANDLER_FUNCTION,
            trigger_type=trigger_type,
            trigger_args=trigger_args,
            group_ids=group_ids,
            description=description,
            enabled=enabled,
            misfire_grace_time=misfire_grace_time,
            metadata=ScheduledTaskMetadata(
                job_id=job_id,
                owner_user_id=str(owner_user_id),
                target_type=target_type,
                target_id=str(target_id),
                prompt=prompt,
                created_from=created_from,
                delivery_mode=delivery_mode,
            ),
        )

    async def update_task_trigger(self, job_id: str, trigger_type: str, trigger_args: dict) -> bool:
        """修改任务触发器"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)

            task = session.exec(statement).first()
            if not task:
                self.logger.warning(f"任务 {job_id} 不存在")
                return False

            # 先尝试更新 APScheduler，失败则不写入数据库
            try:
                self.scheduler.reschedule_job(job_id, trigger=trigger_type, **trigger_args)
            except Exception as e:
                self.logger.error(f"更新任务 {job_id} 触发器失败: {e}")
                session.rollback()
                return False

            task.updated_at = int(time.time())
            # 更新数据库
            task.trigger_type = trigger_type
            task.trigger_args = json.dumps(trigger_args)
            session.add(task)
            session.commit()

            self.logger.info(f"任务 {job_id} 触发器已更新")
            return True

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
            for group_id in sorted(set(group_ids)):
                mapping = TaskGroupMapping(job_id=job_id, group_id=group_id)
                session.add(mapping)

            task.updated_at = int(time.time())
            session.add(task)
            session.commit()

            self._sync_group_config(job_id, group_ids)
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
            metadata = session.exec(
                select(ScheduledTaskMetadata).where(ScheduledTaskMetadata.job_id == job_id)
            ).first()
            if metadata and metadata.archived:
                self.logger.warning(f"任务 {job_id} 已归档，不能启用")
                return False

            task.enabled = True
            task.updated_at = int(time.time())

            # 恢复或重新添加到 APScheduler
            try:
                self.scheduler.resume_job(job_id)
                self.logger.info(f"任务 {job_id} 已启用")
            except Exception:
                # 任务不在 scheduler 中，重新添加
                try:
                    self.add_job_to_scheduler(task)
                    self.logger.info(f"任务 {job_id} 已重新添加到调度器并启用")
                except Exception as e:
                    self.logger.error(f"无法将任务 {job_id} 添加到调度器: {e}")
                    session.rollback()
                    return False

            session.add(task)
            session.commit()

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

            # 暂停APScheduler任务
            try:
                self.scheduler.pause_job(job_id)
                self.logger.info(f"任务 {job_id} 已禁用")
            except Exception as e:
                # 任务可能还未注册到 scheduler，这是正常的
                self.logger.warning(f"无法在 scheduler 中暂停任务 {job_id}: {e}")

            session.add(task)
            session.commit()
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

            statement = select(ScheduledTaskMetadata).where(ScheduledTaskMetadata.job_id == job_id)
            metadata = session.exec(statement).first()
            if metadata:
                session.delete(metadata)

            # 删除任务配置
            session.delete(task)
            session.commit()

            self._sync_group_config(job_id, [])

            # 从APScheduler中移除
            try:
                self.scheduler.remove_job(job_id)
            except Exception as e:
                self.logger.warning(f"任务 {job_id} 不在调度器中: {e}")

            self.logger.info(f"任务 {job_id} 已删除")
            return True

    async def archive_task(self, job_id: str) -> bool:
        """归档任务并从 APScheduler 移除，保留配置和历史。"""
        with Session(self.engine) as session:
            task = session.exec(select(TaskConfig).where(TaskConfig.job_id == job_id)).first()
            if not task:
                self.logger.warning(f"任务 {job_id} 不存在")
                return False

            now = int(time.time())
            metadata = session.exec(
                select(ScheduledTaskMetadata).where(ScheduledTaskMetadata.job_id == job_id)
            ).first()
            if metadata:
                metadata.archived = True
                metadata.archived_at = now
                metadata.updated_at = now
                session.add(metadata)

            task.enabled = False
            task.next_run_time = None
            task.updated_at = now
            session.add(task)
            session.commit()

            try:
                self.scheduler.remove_job(job_id)
            except Exception as e:
                self.logger.debug(f"任务 {job_id} 不在调度器中，无需移除: {e}")

            self.logger.info(f"任务 {job_id} 已归档")
            return True

    async def run_task_now(self, job_id: str) -> bool:
        """立即运行任务一次。"""
        if not self._job_func:
            raise RuntimeError("TaskExecutor 未设置，请先调用 set_job_func()")
        task = await self.get_task(job_id)
        if not task:
            return False
        metadata = await self.get_task_metadata(job_id)
        if metadata and metadata.archived:
            return False
        await self._job_func(job_id)
        return True

    # ==================== 任务查询 ====================

    async def get_task(self, job_id: str) -> TaskConfig | None:
        """获取任务配置"""
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id == job_id)
            return session.exec(statement).first()

    async def list_tasks(
        self,
        enabled: bool | None = None,
        keyword: str | None = None,
        owner_user_id: str | None = None,
        include_archived: bool = False,
    ) -> list[TaskConfig]:
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
            tasks = list(results)
            if not tasks:
                return []

            metadata_items = session.exec(select(ScheduledTaskMetadata)).all()
            metadata_by_job_id = {item.job_id: item for item in metadata_items}
            filtered_tasks = []
            for task in tasks:
                metadata = metadata_by_job_id.get(task.job_id)
                if owner_user_id is not None:
                    if not metadata or metadata.owner_user_id != str(owner_user_id):
                        continue
                if not include_archived and metadata and metadata.archived:
                    continue
                filtered_tasks.append(task)
            return filtered_tasks

    async def get_task_metadata(self, job_id: str) -> ScheduledTaskMetadata | None:
        """获取统一自动任务元数据。"""
        with Session(self.engine) as session:
            statement = select(ScheduledTaskMetadata).where(ScheduledTaskMetadata.job_id == job_id)
            return session.exec(statement).first()

    async def get_task_metadata_map(self, job_ids: list[str] | None = None) -> dict[str, ScheduledTaskMetadata]:
        """批量获取任务元数据。"""
        with Session(self.engine) as session:
            statement = select(ScheduledTaskMetadata)
            if job_ids:
                statement = statement.where(ScheduledTaskMetadata.job_id.in_(job_ids))  # type: ignore[attr-defined]
            items = session.exec(statement).all()
            return {item.job_id: item for item in items}

    async def user_can_manage_task(self, job_id: str, user_id: str, is_superuser: bool = False) -> bool:
        """检查用户是否可以管理指定任务。"""
        if is_superuser:
            return await self.get_task(job_id) is not None
        metadata = await self.get_task_metadata(job_id)
        return bool(metadata and metadata.owner_user_id == str(user_id))

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
        output_summary: str | None = None,
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
                output_summary=output_summary,
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
                except Exception as e:
                    self.logger.debug(f"同步任务 {job_id} next_run_time 失败: {e}")

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
                    {
                        "execution_time": h.execution_time,
                        "status": h.status,
                        "duration_ms": h.duration_ms,
                        "output_summary": h.output_summary,
                    }
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
                execution_time=int(time.time()),
                scheduled_time=int(event.scheduled_run_time.timestamp()) if event.scheduled_run_time else None,
            )
        )
        self.logger.warning(f"任务 {job_id} 执行被跳过 (missed)")

    # ==================== 任务初始化 ====================

    async def initialize(self):
        """初始化时同步群组配置到EnvConfig"""
        from utils.configs import EnvConfig

        tasks = await self.list_tasks()

        for task in tasks:
            group_ids = await self.get_task_groups(task.job_id)
            config_key = self.JOB_ID_TO_CONFIG_KEY.get(task.job_id)
            if config_key:
                setattr(EnvConfig, config_key, group_ids)
                self.logger.info(f"同步群组配置: {config_key} = {group_ids}")

    async def migrate_legacy_reminders(self) -> int:
        """将旧 reminder_handler 任务迁移到统一 Scheduled Agent Task。"""
        migrated = 0
        with Session(self.engine) as session:
            statement = select(TaskConfig).where(TaskConfig.job_id.startswith("reminder_"))  # type: ignore[attr-defined]
            tasks = session.exec(statement).all()
            for task in tasks:
                existing = session.exec(
                    select(ScheduledTaskMetadata).where(ScheduledTaskMetadata.job_id == task.job_id)
                ).first()
                if existing:
                    continue
                if (
                    task.handler_module != "plugins.clockwork.reminder_handler"
                    or task.handler_function != "fire_reminder"
                ):
                    continue
                if not task.description:
                    continue
                try:
                    payload = json.loads(task.description)
                except json.JSONDecodeError:
                    self.logger.warning(f"旧提醒任务 {task.job_id} description 不是 JSON，跳过迁移")
                    continue

                reminder_text = str(payload.get("text") or "")
                owner_user_id = str(payload.get("user_id") or "")
                group_id = payload.get("group_id")
                private = bool(payload.get("private", False))
                if not reminder_text or not owner_user_id:
                    self.logger.warning(f"旧提醒任务 {task.job_id} 缺少 text/user_id，跳过迁移")
                    continue

                target_type = "user" if private or not group_id else "group"
                target_id = owner_user_id if target_type == "user" else str(group_id)
                metadata = ScheduledTaskMetadata(
                    job_id=task.job_id,
                    owner_user_id=owner_user_id,
                    target_type=target_type,
                    target_id=str(target_id),
                    prompt=f"在指定时间提醒用户：{reminder_text}。请生成一条简短提醒消息。",
                    created_from="legacy_reminder",
                    delivery_mode="final",
                )
                session.add(metadata)
                task.handler_module = self.AGENT_TASK_HANDLER_MODULE
                task.handler_function = self.AGENT_TASK_HANDLER_FUNCTION
                task.description = f"提醒: {reminder_text[:80]}"
                task.updated_at = int(time.time())
                session.add(task)
                migrated += 1

            session.commit()
        if migrated:
            self.logger.info(f"已迁移 {migrated} 个旧提醒任务到统一自动任务")
        return migrated

    def _sync_group_config(self, job_id: str, group_ids: list[int]) -> None:
        """运行期同步群组配置到 EnvConfig"""
        from utils.configs import EnvConfig

        config_key = self.JOB_ID_TO_CONFIG_KEY.get(job_id)
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
        execution_time = int(start_time)

        try:
            # 获取任务配置
            task = await self.task_manager.get_task(job_id)
            if not task or not task.enabled:
                await self.task_manager.log_execution(job_id, "skipped", execution_time)
                return
            metadata = await self.task_manager.get_task_metadata(job_id)
            if metadata and metadata.archived:
                await self.task_manager.log_execution(job_id, "skipped", execution_time)
                return

            # 动态导入任务处理函数
            handler = self._load_handler(task.handler_module, task.handler_function)

            # 获取推送群组
            group_ids = await self.task_manager.get_task_groups(job_id)

            # 执行任务
            result = await handler(job_id=job_id)
            if not isinstance(result, TaskRunResult):
                result = TaskRunResult(groups_sent=group_ids, messages_sent=len(group_ids))

            # 记录成功
            duration = int((time.time() - start_time) * 1000)
            await self.task_manager.log_execution(
                job_id=job_id,
                status="success",
                execution_time=execution_time,
                duration_ms=duration,
                output_summary=result.output_summary,
                groups_sent=result.groups_sent if result.groups_sent is not None else group_ids,
                messages_sent=result.messages_sent,
            )
            if task.trigger_type == "date":
                await self.task_manager.archive_task(job_id)

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            error_traceback = traceback.format_exc()
            await self.task_manager.log_execution(
                job_id=job_id,
                status="failed",
                execution_time=execution_time,
                duration_ms=duration,
                error_message=str(e),
                error_traceback=error_traceback,
            )
            self.task_manager.logger.error(f"任务 {job_id} 执行失败: {e}\n{error_traceback}")

    def _load_handler(self, module_name: str, function_name: str):
        """动态加载任务处理函数"""
        module = importlib.import_module(module_name)
        return getattr(module, function_name)
