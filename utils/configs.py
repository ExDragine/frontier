import tomllib

import dotenv
from pydantic import SecretStr

dotenv.load_dotenv()


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

    OPENAI_BASE_URL: str = endpoint["openai_base_url"]
    BASIC_MODEL: str = endpoint["basic_model"]
    BASIC_MODEL_PROVIDER: str = endpoint.get("basic_model_provider", "")
    BASIC_MODEL_ENDPOINT: str = endpoint.get("basic_model_endpoint", "")
    BASIC_MODEL_CAPABILITIES: list[str] = endpoint.get("basic_model_capabilities", [])
    ADVAN_MODEL: str = endpoint["advan_model"]
    ADVAN_MODEL_PROVIDER: str = endpoint.get("advan_model_provider", "")
    ADVAN_MODEL_ENDPOINT: str = endpoint.get("advan_model_endpoint", "")
    ADVAN_MODEL_CAPABILITIES: list[str] = endpoint.get("advan_model_capabilities", [])
    PAINT_MODEL: str = endpoint["paint_model"]
    PAINT_BASE_URL: str = endpoint.get("paint_base_url") or OPENAI_BASE_URL
    BASIC_MODEL_USE_RESPONSES_API: bool = endpoint.get("basic_model_use_responses_api", True)
    ADVAN_MODEL_USE_RESPONSES_API: bool = endpoint.get("advan_model_use_responses_api", True)

    OPENAI_API_KEY: SecretStr = SecretStr(key["openai_api_key"])
    PAINT_API_KEY: SecretStr = SecretStr(key.get("paint_api_key") or key["openai_api_key"])
    NASA_API_KEY: SecretStr = SecretStr(key["nasa_api_key"])
    GITHUB_PAT: SecretStr = SecretStr(key["github_pat"])
    GOOGLE_API_KEY: SecretStr = SecretStr(key.get("google_api_key", ""))
    ANTHROPIC_API_KEY: SecretStr = SecretStr(key.get("anthropic_api_key", ""))
    ANTHROPIC_BASE_URL: str = key.get("anthropic_base_url", "")
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

    RAW_MESSAGE_GROUP_ID: list = message["raw_message_group_id"]
    TEST_GROUP_ID: list = message["test_group_id"]
    ANNOUNCE_GROUP_ID: list = message.get("announce_group_id", TEST_GROUP_ID)
    APOD_GROUP_ID: list = message.get("apod_group_id", TEST_GROUP_ID)
    EARTH_NOW_GROUP_ID: list = message.get("earth_now_group_id", TEST_GROUP_ID)
    NEWS_SUMMARY_GROUP_ID: list = message.get("news_summary_group_id", TEST_GROUP_ID)
    EARTHQUAKE_GROUP_ID: list = message.get("earthquake_group_id", TEST_GROUP_ID)

    QUERY_MESSAGE_NUMBERS: int = database["query_message_numbers"]

    AGENT_DEBUG_MODE: bool = debug["agent_debug_mode"]

    DASHBOARD_PASSWORD: str = dashboard.get("password", "admin")
    DASHBOARD_JWT_SECRET: str = dashboard.get("jwt_secret", "frontier-dashboard-default-secret")
    DASHBOARD_JWT_EXPIRE_HOURS: int = int(dashboard.get("jwt_expire_hours", 24))

    IMAGE_ENABLED: bool = image_memory.get("enabled", True)
    IMAGE_TTL_DAYS: int = int(image_memory.get("ttl_days", 30))
    IMAGE_AUTO_CLEANUP: bool = image_memory.get("auto_cleanup", True)

    CONTENT_CHECK_ENABLED: bool = content_check.get("enabled", False)
