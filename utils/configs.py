import os
import tomllib
from dataclasses import dataclass, field

import dotenv
from pydantic import SecretStr

dotenv.load_dotenv()


@dataclass
class ModelConfig:
    model: str
    provider: str = ""
    endpoint: str = ""
    capabilities: list[str] = field(default_factory=list)
    use_responses_api: bool = True


@dataclass
class AccessPolicy:
    whitelist_mode: bool = False
    whitelist_person_list: list = field(default_factory=list)
    whitelist_group_list: list = field(default_factory=list)
    blacklist_person_list: list = field(default_factory=list)
    blacklist_group_list: list = field(default_factory=list)


# ── TOML 解析 ────────────────────────────────────────────────────


with open("env.toml", "rb") as f:
    config = tomllib.load(f)

information: dict = config.get("information", {})
endpoint: dict = config.get("endpoint", {})
llm_endpoints: dict = config.get("llm_endpoints", {})
key: dict = config.get("key", {})
function_list = config.get("function", {})
message: dict = config.get("message", {})
database: dict = config.get("database", {})
debug: dict = config.get("debug", {})
dashboard: dict = config.get("dashboard", {})
image_memory: dict = config.get("image_memory", {})
content_check: dict = config.get("content_check", {})



class EnvConfig:
    BOT_NAME: str = information["name"]

    AGENT_MODULE_ENABLED: bool = function_list["agent_module_enabled"]
    PAINT_MODULE_ENABLED: bool = function_list["paint_module_enabled"]
    VIDEO_MODULE_ENABLED: bool = function_list.get("video_module_enabled", PAINT_MODULE_ENABLED)

    OPENAI_BASE_URL: str = endpoint["openai_base_url"]
    BASIC_MODEL: str = endpoint["basic_model"]
    BASIC_MODEL_PROVIDER: str = endpoint.get("basic_model_provider", "")
    BASIC_MODEL_ENDPOINT: str = endpoint.get("basic_model_endpoint", "")
    BASIC_MODEL_CAPABILITIES: list[str] = endpoint.get("basic_model_capabilities", [])
    SIGNAL_MODEL: str = endpoint.get("signal_model", "deepseek-v4-flash")
    SIGNAL_MODEL_PROVIDER: str = endpoint.get("signal_model_provider", "deepseek")
    SIGNAL_MODEL_ENDPOINT: str = endpoint.get("signal_model_endpoint", "")
    SIGNAL_MODEL_CAPABILITIES: list[str] = endpoint.get("signal_model_capabilities", ["text"])
    ADVAN_MODEL: str = endpoint["advan_model"]
    ADVAN_MODEL_PROVIDER: str = endpoint.get("advan_model_provider", "")
    ADVAN_MODEL_ENDPOINT: str = endpoint.get("advan_model_endpoint", "")
    ADVAN_MODEL_CAPABILITIES: list[str] = endpoint.get("advan_model_capabilities", [])
    PAINT_MODEL: str = endpoint["paint_model"]
    PAINT_BASE_URL: str = endpoint.get("paint_base_url") or OPENAI_BASE_URL
    VIDEO_MODEL: str = endpoint.get("video_model") or "alibaba/happyhorse-1.0"
    VIDEO_BASE_URL: str = endpoint.get("video_base_url") or "https://zenmux.ai/api/vertex-ai"
    BASIC_MODEL_USE_RESPONSES_API: bool = endpoint.get("basic_model_use_responses_api", True)
    ADVAN_MODEL_USE_RESPONSES_API: bool = endpoint.get("advan_model_use_responses_api", True)

    OPENAI_API_KEY: SecretStr = SecretStr(key["openai_api_key"])
    PAINT_API_KEY: SecretStr = SecretStr(key.get("paint_api_key") or key["openai_api_key"])
    VIDEO_API_KEY: SecretStr = SecretStr(key.get("video_api_key") or os.getenv("ZENMUX_API_KEY", ""))
    NASA_API_KEY: SecretStr = SecretStr(key["nasa_api_key"])
    GITHUB_PAT: SecretStr = SecretStr(key["github_pat"])
    GOOGLE_API_KEY: SecretStr = SecretStr(key.get("google_api_key", ""))
    ANTHROPIC_API_KEY: SecretStr = SecretStr(key.get("anthropic_api_key", ""))
    ANTHROPIC_BASE_URL: str = key.get("anthropic_base_url", "")
    DEEPSEEK_API_KEY: SecretStr = SecretStr(key.get("deepseek_api_key", ""))
    DEEPSEEK_API_BASE: str = key.get("deepseek_api_base", "")
    LLM_ENDPOINTS: dict = llm_endpoints

    AGENT_CAPABILITY = function_list["agent_capability"]
    AGENT_WHITELIST_MODE: bool = function_list["agent_whitelist_mode"]
    AGENT_WHITELIST_PERSON_LIST: list = function_list["agent_whitelist_person_list"]
    AGENT_WHITELIST_GROUP_LIST: list = function_list["agent_whitelist_group_list"]
    AGENT_BLACKLIST_PERSON_LIST: list = function_list["agent_blacklist_person_list"]
    AGENT_BLACKLIST_GROUP_LIST: list = function_list["agent_blacklist_group_list"]
    PAINT_WHITELIST_MODE: bool = function_list["paint_whitelist_mode"]
    PAINT_WHITELIST_PERSON_LIST: list = function_list["paint_whitelist_person_list"]
    PAINT_WHITELIST_GROUP_LIST: list = function_list["paint_whitelist_group_list"]
    PAINT_BLACKLIST_PERSON_LIST: list = function_list["paint_blacklist_person_list"]
    PAINT_BLACKLIST_GROUP_LIST: list = function_list["paint_blacklist_group_list"]
    PAINT_RATE_LIMIT_MAX_REQUESTS: int = int(function_list.get("paint_rate_limit_max_requests", 3))
    PAINT_RATE_LIMIT_WINDOW_SECONDS: int = int(function_list.get("paint_rate_limit_window_seconds", 600))
    VIDEO_RATE_LIMIT_MAX_REQUESTS: int = int(function_list.get("video_rate_limit_max_requests", 1))
    VIDEO_RATE_LIMIT_WINDOW_SECONDS: int = int(function_list.get("video_rate_limit_window_seconds", 900))
    VIDEO_POLL_INTERVAL_SECONDS: int = int(function_list.get("video_poll_interval_seconds", 15))
    VIDEO_POLL_TIMEOUT_SECONDS: int = int(function_list.get("video_poll_timeout_seconds", 900))
    AGENT_LLM_TIMEOUT_SECONDS: int = int(function_list.get("agent_llm_timeout_seconds", 900))
    AGENT_JOB_TIMEOUT_SECONDS: int = int(function_list.get("agent_job_timeout_seconds", 3600))

    ANNOUNCE_GROUP_ID: list = message.get("announce_group_id", [])
    APOD_GROUP_ID: list = message.get("apod_group_id", [])
    EARTH_NOW_GROUP_ID: list = message.get("earth_now_group_id", [])
    NEWS_SUMMARY_GROUP_ID: list = message.get("news_summary_group_id", [])
    EARTHQUAKE_GROUP_ID: list = message.get("earthquake_group_id", [])

    QUERY_MESSAGE_NUMBERS: int = database["query_message_numbers"]

    AGENT_DEBUG_MODE: bool = debug["agent_debug_mode"]

    DASHBOARD_PASSWORD: str = dashboard.get("password", "admin")
    DASHBOARD_JWT_SECRET: str = dashboard.get("jwt_secret", "frontier-dashboard-default-secret")
    DASHBOARD_JWT_EXPIRE_HOURS: int = int(dashboard.get("jwt_expire_hours", 24))

    # 启动时强制验证：拒绝默认 JWT secret。
    # 使用模块级缓存避免每次 import 都生成不同的临时密钥。
    if "frontier-dashboard-default-secret" == DASHBOARD_JWT_SECRET:
        import secrets
        import sys

        # 写入一个运行时缓存文件，同一进程多次 import 不会重新生成
        _cache_dir = os.path.join(os.getcwd(), "cache")
        os.makedirs(_cache_dir, exist_ok=True)
        _secret_cache = os.path.join(_cache_dir, ".runtime_jwt_secret")
        if os.path.exists(_secret_cache):
            with open(_secret_cache) as _f:
                DASHBOARD_JWT_SECRET = _f.read().strip()
        else:
            generated = secrets.token_hex(32)
            with open(_secret_cache, "w") as _f:
                _f.write(generated)
            DASHBOARD_JWT_SECRET = generated
            msg = (
                f"\n{'=' * 60}\n"
                f"  ⚠️  安全警告：Dashboard JWT secret 使用默认值！\n"
                f"  请在 env.toml 的 [dashboard] 段设置 jwt_secret。\n"
                f"  已为本次运行生成临时密钥: {generated}\n"
                f"  将以下内容添加到 env.toml 以避免下次启动再次生成:\n"
                f"\n"
                f"  [dashboard]\n"
                f'  jwt_secret = "{generated}"\n'
                f"{'=' * 60}\n"
            )
            print(msg, file=sys.stderr)

    if DASHBOARD_PASSWORD == "admin":  # noqa: S105 - explicit insecure-default warning check
        import sys

        msg = (
            f"\n{'=' * 60}\n"
            f'  ⚠️  安全警告：Dashboard 密码使用默认值 "admin"！\n'
            f"  请在 env.toml 的 [dashboard] 段设置 password。\n"
            f"  密码应使用 bcrypt 哈希存储。\n"
            f"  生成哈希: python -c 'import bcrypt; print(bcrypt.hashpw(\n"
            f'      b"你的密码", bcrypt.gensalt()).decode())\'\n'
            f"{'=' * 60}\n"
        )
        print(msg, file=sys.stderr)

    IMAGE_ENABLED: bool = image_memory.get("enabled", True)
    IMAGE_TTL_DAYS: int = int(image_memory.get("ttl_days", 30))
    IMAGE_AUTO_CLEANUP: bool = image_memory.get("auto_cleanup", True)

    CONTENT_CHECK_ENABLED: bool = content_check.get("enabled", False)


    @classmethod
    def reload(cls, config: dict) -> None:
        """从 TOML 字典热重载所有运行时配置（启动和 Dashboard 共用）。"""
        import os as _os

        from pydantic import SecretStr as _SecretStr

        ep = config.get("endpoint", {})
        key = config.get("key", {})
        fn = config.get("function", {})
        msg = config.get("message", {})

        # ── 模型角色 ──
        _ROLES = ("basic", "signal", "advan")
        _role_attrs = {
            "basic": ("BASIC_MODEL", "BASIC_MODEL_PROVIDER", "BASIC_MODEL_ENDPOINT", "BASIC_MODEL_CAPABILITIES"),
            "signal": ("SIGNAL_MODEL", "SIGNAL_MODEL_PROVIDER", "SIGNAL_MODEL_ENDPOINT", "SIGNAL_MODEL_CAPABILITIES"),
            "advan": ("ADVAN_MODEL", "ADVAN_MODEL_PROVIDER", "ADVAN_MODEL_ENDPOINT", "ADVAN_MODEL_CAPABILITIES"),
        }
        _role_defaults = {
            "basic": ("", "", "", []),
            "signal": ("deepseek-v4-flash", "deepseek", "", ["text"]),
            "advan": ("", "", "", []),
        }
        for role in _ROLES:
            defaults = _role_defaults[role]
            for i, attr in enumerate(_role_attrs[role]):
                key_name = attr.split("_", 1)[1].lower()  # e.g., "model", "model_provider", ...
                setattr(
                    cls, attr, ep.get(f"{role}_{key_name}" if key_name != "model" else f"{role}_model", defaults[i])
                )

        # ── 其他端点 ──
        cls.OPENAI_BASE_URL = ep.get("openai_base_url", cls.OPENAI_BASE_URL)
        cls.PAINT_MODEL = ep.get("paint_model", cls.PAINT_MODEL)
        cls.PAINT_BASE_URL = ep.get("paint_base_url") or cls.OPENAI_BASE_URL
        cls.VIDEO_MODEL = ep.get("video_model") or cls.VIDEO_MODEL
        cls.VIDEO_BASE_URL = ep.get("video_base_url") or cls.VIDEO_BASE_URL
        cls.LLM_ENDPOINTS = config.get("llm_endpoints", {})

        # ── API 密钥 ──
        cls.OPENAI_API_KEY = _SecretStr(key.get("openai_api_key", ""))
        cls.PAINT_API_KEY = _SecretStr(key.get("paint_api_key") or key.get("openai_api_key", ""))
        cls.VIDEO_API_KEY = _SecretStr(key.get("video_api_key") or _os.getenv("ZENMUX_API_KEY", ""))
        cls.NASA_API_KEY = _SecretStr(key.get("nasa_api_key", ""))
        cls.GITHUB_PAT = _SecretStr(key.get("github_pat", ""))
        cls.GOOGLE_API_KEY = _SecretStr(key.get("google_api_key", ""))
        cls.ANTHROPIC_API_KEY = _SecretStr(key.get("anthropic_api_key", ""))
        cls.ANTHROPIC_BASE_URL = key.get("anthropic_base_url", "")
        cls.DEEPSEEK_API_KEY = _SecretStr(key.get("deepseek_api_key", ""))
        cls.DEEPSEEK_API_BASE = key.get("deepseek_api_base", "")

        # ── 功能开关 ──
        cls.AGENT_MODULE_ENABLED = fn.get("agent_module_enabled", cls.AGENT_MODULE_ENABLED)
        cls.PAINT_MODULE_ENABLED = fn.get("paint_module_enabled", cls.PAINT_MODULE_ENABLED)
        cls.VIDEO_MODULE_ENABLED = fn.get("video_module_enabled", cls.PAINT_MODULE_ENABLED)
        cls.AGENT_CAPABILITY = fn.get("agent_capability", cls.AGENT_CAPABILITY)

        # ── 访问控制 ──
        _POLICIES = ("agent", "paint")
        _policy_fields = (
            "WHITELIST_MODE",
            "WHITELIST_PERSON_LIST",
            "WHITELIST_GROUP_LIST",
            "BLACKLIST_PERSON_LIST",
            "BLACKLIST_GROUP_LIST",
        )
        for policy in _POLICIES:
            for policy_field in _policy_fields:
                attr = f"{policy.upper()}_{policy_field}"
                key_name = f"{policy}_{policy_field.lower()}"
                setattr(cls, attr, fn.get(key_name, getattr(cls, attr)))

        # ── 限流/超时 ──
        for attr, key_name in (
            ("PAINT_RATE_LIMIT_MAX_REQUESTS", "paint_rate_limit_max_requests"),
            ("PAINT_RATE_LIMIT_WINDOW_SECONDS", "paint_rate_limit_window_seconds"),
            ("VIDEO_RATE_LIMIT_MAX_REQUESTS", "video_rate_limit_max_requests"),
            ("VIDEO_RATE_LIMIT_WINDOW_SECONDS", "video_rate_limit_window_seconds"),
            ("VIDEO_POLL_INTERVAL_SECONDS", "video_poll_interval_seconds"),
            ("VIDEO_POLL_TIMEOUT_SECONDS", "video_poll_timeout_seconds"),
            ("AGENT_LLM_TIMEOUT_SECONDS", "agent_llm_timeout_seconds"),
            ("AGENT_JOB_TIMEOUT_SECONDS", "agent_job_timeout_seconds"),
        ):
            setattr(cls, attr, int(fn.get(key_name, getattr(cls, attr))))

        # ── 群组消息 ──
        cls.ANNOUNCE_GROUP_ID = msg.get("announce_group_id", [])
        cls.APOD_GROUP_ID = msg.get("apod_group_id", [])
        cls.EARTH_NOW_GROUP_ID = msg.get("earth_now_group_id", [])
        cls.NEWS_SUMMARY_GROUP_ID = msg.get("news_summary_group_id", [])
        cls.EARTHQUAKE_GROUP_ID = msg.get("earthquake_group_id", [])

        # ── 杂项 ──
        cls.QUERY_MESSAGE_NUMBERS = config.get("database", {}).get("query_message_numbers", cls.QUERY_MESSAGE_NUMBERS)
        cls.AGENT_DEBUG_MODE = config.get("debug", {}).get("agent_debug_mode", cls.AGENT_DEBUG_MODE)
        dash = config.get("dashboard", {})
        cls.DASHBOARD_PASSWORD = dash.get("password", "admin")
        cls.DASHBOARD_JWT_SECRET = dash.get("jwt_secret", "frontier-dashboard-default-secret")
        cls.DASHBOARD_JWT_EXPIRE_HOURS = int(dash.get("jwt_expire_hours", 24))

        image_memory = config.get("image_memory", {})
        cls.IMAGE_ENABLED = bool(image_memory.get("enabled", cls.IMAGE_ENABLED))
        cls.IMAGE_TTL_DAYS = int(image_memory.get("ttl_days", cls.IMAGE_TTL_DAYS))
        cls.IMAGE_AUTO_CLEANUP = bool(image_memory.get("auto_cleanup", cls.IMAGE_AUTO_CLEANUP))

        cls.CONTENT_CHECK_ENABLED = bool(config.get("content_check", {}).get("enabled", cls.CONTENT_CHECK_ENABLED))



