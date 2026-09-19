"""Scheduled execution outcomes, separate from persistence and registration."""

import asyncio
import importlib
import time
import traceback

from utils.configs import EnvConfig

from .task_models import TaskRunResult


class TaskExecutor:
    """任务执行器 - 包装原始任务函数，添加监控和群组管理"""

    def __init__(self, task_manager):
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
            timeout = (
                EnvConfig.AGENT_JOB_TIMEOUT_SECONDS
                if task.handler_module == "plugins.clockwork.agent_task_handler"
                else None
            )
            async with asyncio.timeout(timeout):
                result = await handler(job_id=job_id)
            if not isinstance(result, TaskRunResult):
                result = TaskRunResult(groups_sent=group_ids, messages_sent=len(group_ids))

            # 保留 handler 的实际投递结果。
            duration = int((time.time() - start_time) * 1000)
            await self.task_manager.log_execution(
                job_id=job_id,
                status=result.status,
                execution_time=execution_time,
                duration_ms=duration,
                output_summary=result.output_summary,
                groups_sent=result.groups_sent if result.groups_sent is not None else group_ids,
                messages_sent=result.messages_sent,
            )
            if task.trigger_type == "date" and result.status == "success":
                await self.task_manager.archive_task(job_id)

        except asyncio.CancelledError:
            await self.task_manager.log_execution(job_id, "cancelled", execution_time)
            raise
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            error_traceback = traceback.format_exc()
            await self.task_manager.log_execution(
                job_id=job_id,
                status="timeout" if isinstance(e, TimeoutError) else "failed",
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
