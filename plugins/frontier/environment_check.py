import platform
import subprocess
import sys

from nonebot import logger


def cpu_check():
    try:
        import cpuinfo  # type: ignore  # noqa: I001

        brand = (cpuinfo.get_cpu_info().get("brand_raw", "") or "").lower()
        if "intel" in brand or "amd" in brand:
            return "intel" if "intel" in brand else "amd"
        return "unknown"
    except ImportError:
        pass
    try:
        if sys.platform == "win32":
            out = (
                subprocess.check_output(["wmic", "cpu", "get", "name"], stderr=subprocess.DEVNULL)
                .decode(errors="ignore")
                .lower()
            )
            if "intel" in out or "amd" in out:
                return "intel" if "intel" in out else "amd"
            return "unknown"
        elif sys.platform == "linux":
            with open("/proc/cpuinfo") as f:
                info = f.read().lower()
                if "intel" in info or "amd" in info:
                    return "intel" if "intel" in info else "amd"
            return "unknown"
        elif sys.platform == "darwin":
            out = (
                subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], stderr=subprocess.DEVNULL)
                .decode(errors="ignore")
                .lower()
            )
            if "intel" in out or "amd" in out:
                return "intel" if "intel" in out else "amd"
            return "unknown"
    except Exception:
        logger.warning("无法通过系统命令获取CPU信息，尝试使用platform模块", exc_info=True)
        pass
    try:
        if "intel" or "amd" in platform.processor().lower():
            return "intel" if "intel" in platform.processor().lower() else "amd"
        return "unknown"
    except Exception:
        return "unknown"


def gpu_check():
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0).lower()
            if "nvidia" in gpu_name:
                return "nvidia"
            elif "amd" in gpu_name or "radeon" in gpu_name:
                return "amd"
            elif "intel" in gpu_name:
                return "intel"
            else:
                return "unknown"
        else:
            return "none"
    except ImportError:
        pass


def system_check():
    cpu_type = cpu_check()
    gpu_type = gpu_check()
    # save to toml file
    try:
        import tomlkit

        config_path = "cache/environment.toml"
        try:
            with open(config_path, encoding="utf-8") as f:
                config = tomlkit.load(f)
        except FileNotFoundError:
            config = {}
        config["hardware"] = {"cpu": cpu_type, "gpu": gpu_type}
        with open(config_path, "w", encoding="utf-8") as f:
            tomlkit.dump(config, f)
    except ImportError:
        logger.warning("未安装tomlkit库，无法保存环境信息到配置文件", exc_info=True)
