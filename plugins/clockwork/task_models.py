import datetime
from dataclasses import dataclass
from typing import Literal

from sqlmodel import Field, SQLModel


class TaskConfig(SQLModel, table=True):
    """定时任务配置表"""

    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    description: str | None = Field(default=None)

    handler_module: str
    handler_function: str

    trigger_type: str
    trigger_args: str

    enabled: bool = Field(default=True, index=True)
    misfire_grace_time: int = Field(default=60)

    created_at: int = Field(default_factory=lambda: int(datetime.datetime.now().timestamp()))
    updated_at: int = Field(default_factory=lambda: int(datetime.datetime.now().timestamp()))

    last_run_time: int | None = Field(default=None)
    next_run_time: int | None = Field(default=None)
    total_runs: int = Field(default=0)
    success_runs: int = Field(default=0)
    failed_runs: int = Field(default=0)


class TaskGroupMapping(SQLModel, table=True):
    """任务与群组的多对多关联表"""

    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(index=True)
    group_id: int = Field(index=True)

    enabled: bool = Field(default=True)
    created_at: int = Field(default_factory=lambda: int(datetime.datetime.now().timestamp()))


class TaskExecutionHistory(SQLModel, table=True):
    """任务执行历史记录表"""

    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(index=True)

    execution_time: int = Field(index=True)
    status: str

    duration_ms: int | None = Field(default=None)
    error_message: str | None = Field(default=None)
    error_traceback: str | None = Field(default=None)
    output_summary: str | None = Field(default=None)

    groups_sent: str | None = Field(default=None)
    messages_sent: int = Field(default=0)

    scheduled_time: int | None = Field(default=None)


class ScheduledTaskMetadata(SQLModel, table=True):
    """用户自动任务元数据。

    TaskConfig 仍负责 APScheduler 调度，ScheduledTaskMetadata 保存普通用户
    自动任务需要的 owner、投递目标和 Agent prompt。
    """

    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(unique=True, index=True)
    owner_user_id: str = Field(index=True)
    target_type: str = Field(index=True)
    target_id: str = Field(index=True)
    prompt: str
    archived: bool = Field(default=False, index=True)
    archived_at: int | None = Field(default=None, index=True)
    created_from: str = Field(default="tool", index=True)
    delivery_mode: str = Field(default="final")
    created_at: int = Field(default_factory=lambda: int(datetime.datetime.now().timestamp()))
    updated_at: int = Field(default_factory=lambda: int(datetime.datetime.now().timestamp()))


@dataclass(slots=True)
class TaskRunResult:
    """任务 handler 返回给 TaskExecutor 的结构化结果。"""

    groups_sent: list[int] | None = None
    messages_sent: int = 0
    output_summary: str | None = None
    status: Literal["success", "failed"] = "success"
