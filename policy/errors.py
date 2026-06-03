"""策略层异常类型。"""


class PolicyLoadError(RuntimeError):
    """manifesto 加载/校验失败时抛出，阻止进程启动。"""
