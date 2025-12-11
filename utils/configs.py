import tomllib

import dotenv
from pydantic import SecretStr

dotenv.load_dotenv()


with open("env.toml", "rb") as f:
    config = tomllib.load(f)

information: dict = config.get("information", {})
endpoint: dict = config.get("endpoint", {})
key: dict = config.get("key", {})
function_list = config.get("function", {})
message: dict = config.get("message", {})
database: dict = config.get("database", {})
debug: dict = config.get("debug", {})


class EnvConfig:
    BOT_NAME: str = information["name"]

    AGENT_MODULE_ENABLED: bool = function_list["agent_module_enabled"]
    PAINT_MODULE_ENABLED: bool = function_list["paint_module_enabled"]

    OPENAI_BASE_URL: str = endpoint["openai_base_url"]
    BASIC_MODEL: str = endpoint["basic_model"]
    ADVAN_MODEL: str = endpoint["advan_model"]
    PAINT_MODEL: str = endpoint["paint_model"]

    OPENAI_API_KEY: SecretStr = SecretStr(key["openai_api_key"])
    NASA_API_KEY: SecretStr = SecretStr(key["nasa_api_key"])
    GITHUB_PAT: SecretStr = SecretStr(key["github_pat"])

    AGENT_CAPABILITY = function_list["agent_capability"]
    AGENT_WITHELIST_MODE: bool = function_list["agent_whitelist_mode"]
    AGENT_WITHELIST_PERSON_LIST: list = function_list["agent_whitelist_person_list"]
    AGENT_BLACKLIST_GROUP_LIST: list = function_list["agent_whitelist_group_list"]
    AGENT_BLACKLIST_PERSON_LIST: list = function_list["agent_blacklist_person_list"]
    AGENT_WITHELIST_GROUP_LIST: list = function_list["agent_blacklist_group_list"]
    PAINT_WITHELIST_MODE: bool = function_list["paint_whitelist_mode"]
    PAINT_WITHELIST_PERSON_LIST: list = function_list["paint_whitelist_person_list"]
    PAINT_WITHELIST_GROUP_LIST: list = function_list["paint_whitelist_group_list"]
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
