import datetime

from sqlmodel import Field, SQLModel


class TaskConfig(SQLModel, table=True):
    """定时任务配置表"""

    # 主键和基本信息
    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(unique=True, index=True)  # APScheduler job_id
    name: str = Field(index=True)  # 任务名称（中文显示）
    description: str | None = Field(default=None)  # 任务描述

    # 任务执行配置
    handler_module: str  # 处理函数所在模块，如 "plugins.clockwork"
    handler_function: str  # 处理函数名，如 "apod_everyday"

    # 触发器配置（JSON存储）
    trigger_type: str  # "cron" | "interval" | "date"
    trigger_args: str  # JSON格式存储触发器参数
    # 示例：
    # cron: {"hour": "19", "minute": "0"}
    # interval: {"minutes": 1}
    # date: {"run_date": "2026-02-17 00:00:00"}

    # 状态和元信息
    enabled: bool = Field(default=True, index=True)  # 是否启用
    misfire_grace_time: int = Field(default=60)  # 容错时间（秒）

    # 时间戳
    created_at: int = Field(default_factory=lambda: int(datetime.datetime.now().timestamp()))
    updated_at: int = Field(default_factory=lambda: int(datetime.datetime.now().timestamp()))

    # 统计信息
    last_run_time: int | None = Field(default=None)  # 最后执行时间
    next_run_time: int | None = Field(default=None)  # 下次执行时间
    total_runs: int = Field(default=0)  # 总执行次数
    success_runs: int = Field(default=0)  # 成功次数
    failed_runs: int = Field(default=0)  # 失败次数


class TaskGroupMapping(SQLModel, table=True):
    """任务与群组的多对多关联表"""

    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(index=True)  # 关联到 TaskConfig.job_id
    group_id: int = Field(index=True)  # QQ群号

    # 群组特定配置（可选）
    enabled: bool = Field(default=True)  # 该群是否启用此任务
    created_at: int = Field(default_factory=lambda: int(datetime.datetime.now().timestamp()))


class TaskExecutionHistory(SQLModel, table=True):
    """任务执行历史记录表"""

    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(index=True)  # 关联到 TaskConfig.job_id

    # 执行信息
    execution_time: int = Field(index=True)  # 执行时间戳
    status: str  # "success" | "failed" | "missed" | "skipped"

    # 执行结果
    duration_ms: int | None = Field(default=None)  # 执行耗时（毫秒）
    error_message: str | None = Field(default=None)  # 错误信息
    error_traceback: str | None = Field(default=None)  # 错误堆栈

    # 消息推送信息
    groups_sent: str | None = Field(default=None)  # JSON数组，记录推送的群组
    messages_sent: int = Field(default=0)  # 发送的消息数量

    # APScheduler事件信息
    scheduled_time: int | None = Field(default=None)  # 计划执行时间
