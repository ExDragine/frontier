"""Plugin-local configuration; credentials remain in environment/provider profiles."""

import os
import tomllib
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NewsConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    enabled: bool = True
    board: str = "general"
    timezone: str = "Asia/Shanghai"
    model: str = ""
    provider: str = ""
    model_extra_body: dict = Field(default_factory=dict)
    sources: tuple[Literal["exa", "tavily"], ...] = ("exa", "tavily")
    queries: tuple[str, ...] = ("中国 今日 主要新闻", "全球 今日 主要新闻", "科技 最新消息", "经济 社会 最新消息")
    window_hours: int = Field(default=24, ge=1, le=72)
    min_stories: int = Field(default=3, ge=1, le=18)
    target_stories: int = Field(default=14, ge=1, le=18)
    source_results: int = Field(default=8, ge=1, le=20)
    generation_timeout: int = Field(default=300, ge=10, le=900)
    model_timeout: int = Field(default=90, ge=1, le=300)
    source_timeout: int = Field(default=20, ge=1, le=60)
    render_timeout: int = Field(default=30, ge=1, le=120)
    send_timeout: int = Field(default=30, ge=1, le=120)
    catchup_seconds: int = Field(default=900, ge=60, le=7200)
    retry_delay: int = Field(default=60, ge=1, le=600)
    max_generation_attempts: int = Field(default=3, ge=1, le=5)
    max_delivery_attempts: int = Field(default=3, ge=1, le=5)
    retention_days: int = Field(default=30, ge=2, le=365)
    bot_id: str = ""

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value):
        ZoneInfo(value)
        return value

    @field_validator("queries")
    @classmethod
    def bounded_queries(cls, value):
        if not 1 <= len(value) <= 6 or any(not query.strip() or len(query) > 200 for query in value):
            raise ValueError("news requires 1-6 bounded queries")
        return value

    @field_validator("model_extra_body")
    @classmethod
    def bounded_model_options(cls, value):
        # This snapshot is persisted. Never accept credentials or arbitrary request bodies here.
        if value and (set(value) != {"thinking"} or not isinstance(value["thinking"], dict)
                      or set(value["thinking"]) != {"type"}
                      or value["thinking"]["type"] not in {"enabled", "disabled"}):
            raise ValueError("news model_extra_body only supports thinking.type")
        return value

    @model_validator(mode="after")
    def coherent(self):
        if bool(self.model) != bool(self.provider):
            raise ValueError("set news model and provider together, or leave both empty")
        if self.bot_id and not self.bot_id.isdigit():
            raise ValueError("news bot_id must be numeric")
        if self.min_stories > self.target_stories:
            raise ValueError("min_stories exceeds target_stories")
        if not self.sources or len(set(self.sources)) != len(self.sources):
            raise ValueError("configure distinct search providers")
        return self


def load_news_config(path: Path | None = None) -> NewsConfig:
    path = path or Path(os.getenv("FRONTIER_NEWS_CONFIG", "news.toml"))
    if not path.exists():
        return NewsConfig()
    with path.open("rb") as file:
        data = tomllib.load(file)
    if set(data) != {"news"}:
        raise ValueError("news.toml must contain exactly one [news] section")
    return NewsConfig.model_validate(data["news"])
