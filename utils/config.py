import os

import dotenv
from pydantic_settings import BaseSettings

dotenv.load_dotenv()


class EnvConfig(BaseSettings):
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "")
    BASIC_MODEL: str = os.getenv("BASIC_MODEL", "")
    ADVAN_MODEL: str = os.getenv("ADVAN_MODEL", OPENAI_MODEL)
    PAINT_MODEL: str = os.getenv("PAINT_MODEL", "")

    NASA_API_KEY: str = os.getenv("NASA_API_KEY", "DEMO_KEY")
    GITHUB_PAT = os.getenv("GITHUB_PAT", "")

    RAW_MESSAGE_GROUP_ID: str = os.getenv("RAW_MESSAGE_GROUP_ID", "")
    TEST_GROUP_ID: str = os.getenv("TEST_GROUP_ID", "")
    ANNOUNCE_GROUP_ID: str = os.getenv("ANNOUNCE_GROUP_ID", TEST_GROUP_ID)
    APOD_GROUP_ID: str = os.getenv("APOD_GROUP_ID", TEST_GROUP_ID)
    EARTH_NOW_GROUP_ID: str = os.getenv("EARTH_NOW_GROUP_ID", TEST_GROUP_ID)
    NEWS_SUMMARY_GROUP_ID: str = os.getenv("NEWS_SUMMARY_GROUP_ID", TEST_GROUP_ID)
    EARTHQUAKE_GROUP_ID: str = os.getenv("EARTHQUAKE_GROUP_ID", TEST_GROUP_ID)

    AGENT_DEBUG_MODE: bool = os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true"
