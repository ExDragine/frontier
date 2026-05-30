"""个性化与长期用户记忆 — 从对话中提取用户偏好并注入上下文。

设计原理：
- 利用 Agent 交互的副产物 — chat_agent 返回后异步提取画像，不阻塞回复
- 画像持久化到 SQLite，重启不丢失
- 按相关性分级注入上下文，避免 prompt 膨胀
- 数据最小化：只存储偏好/兴趣/事实，不存储完整对话
"""

from __future__ import annotations

import time
from typing import Any

from nonebot import logger
from pydantic import BaseModel
from sqlmodel import Column, Field, JSON, Session, SQLModel, select

from utils.database import get_engine


class UserProfile(SQLModel, table=True):
    """用户长期画像 — 从对话中提取的结构化信息。"""

    __tablename__: str = "user_profile"

    # group_id=0 表示私聊画像（无群组上下文），这样避免 composite PK 中 nullable 列的 SQLAlchemy 限制
    user_id: int = Field(primary_key=True)
    group_id: int = Field(default=0, primary_key=True)

    nickname_preference: str | None = Field(default=None)
    language_style: str | None = Field(default=None)
    response_length_preference: str | None = Field(default=None)

    interests: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    facts: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))

    total_interactions: int = Field(default=0)
    last_interaction_at: int = Field(default=0)
    preferred_topics: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))


class ProfileExtractionResult(BaseModel):
    """LLM 从对话中提取的画像片段。"""

    nickname: str | None = None
    interests_to_add: list[str] = Field(default_factory=list)
    facts_to_update: dict[str, str] = Field(default_factory=dict)
    language_style: str | None = None
    response_length: str | None = None


class ProfileManager:
    """管理用户画像的存储、合并和上下文注入。"""

    def __init__(self) -> None:
        self._engine = get_engine()
        UserProfile.metadata.create_all(self._engine)
        self._cache: dict[str, UserProfile | None] = {}

    def get_profile(self, user_id: int, group_id: int | None = None) -> UserProfile | None:
        gid = group_id or 0
        cache_key = f"{user_id}:{gid}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        with Session(self._engine) as session:
            stmt = select(UserProfile).where(
                UserProfile.user_id == user_id,
                UserProfile.group_id == gid,
            )
            profile = session.exec(stmt).first()
            self._cache[cache_key] = profile
            return profile

    def upsert_profile(self, profile: UserProfile) -> None:
        profile.updated_at = int(time.time())
        cache_key = f"{profile.user_id}:{profile.group_id}"
        with Session(self._engine) as session:
            existing = session.exec(
                select(UserProfile).where(
                    UserProfile.user_id == profile.user_id,
                    UserProfile.group_id == profile.group_id,
                )
            ).first()
            if existing:
                existing.nickname_preference = profile.nickname_preference
                existing.language_style = profile.language_style
                existing.response_length_preference = profile.response_length_preference
                existing.interests = profile.interests
                existing.facts = profile.facts
                existing.total_interactions = profile.total_interactions
                existing.last_interaction_at = profile.last_interaction_at
                existing.preferred_topics = profile.preferred_topics
                existing.updated_at = profile.updated_at
                session.add(existing)
            else:
                session.add(profile)
            session.commit()
        self._cache[cache_key] = profile

    def record_interaction(
        self, user_id: int, group_id: int | None, topics: list[str] | None = None
    ) -> None:
        gid = group_id or 0
        profile = self.get_profile(user_id, group_id) or UserProfile(
            user_id=user_id, group_id=gid
        )
        profile.total_interactions += 1
        profile.last_interaction_at = int(time.time() * 1000)
        if topics:
            for topic in topics:
                if topic not in profile.preferred_topics:
                    profile.preferred_topics.append(topic)
            profile.preferred_topics = profile.preferred_topics[-20:]
        self.upsert_profile(profile)

    def build_context_injection(
        self, user_id: int, group_id: int | None = None, max_tokens: int = 300
    ) -> str:
        profile = self.get_profile(user_id, group_id)
        if profile is None:
            return ""
        parts: list[str] = []
        if profile.nickname_preference:
            parts.append(f"- 称呼偏好：{profile.nickname_preference}")
        if profile.facts:
            facts_str = "，".join(f"{k}: {v}" for k, v in profile.facts.items())
            parts.append(f"- 已知信息：{facts_str}")
        if profile.interests:
            interests_str = "、".join(profile.interests[:10])
            parts.append(f"- 兴趣领域：{interests_str}")
        if profile.language_style:
            style_map = {"casual": "轻松随意", "formal": "正式", "technical": "技术化"}
            parts.append(f"- 交流风格：{style_map.get(profile.language_style, profile.language_style)}")
        if profile.preferred_topics:
            parts.append(f"- 常聊话题：{'、'.join(profile.preferred_topics[:5])}")
        if not parts:
            return ""
        return "## 用户画像\n" + "\n".join(parts)

    async def maybe_extract_from_interaction(
        self,
        user_id: int,
        group_id: int | None,
        user_message: str,
        assistant_response: str,
    ) -> None:
        gid = group_id or 0
        profile = self.get_profile(user_id, group_id)
        if profile and profile.total_interactions % 10 != 0:
            return
        try:
            result = await self._extract_with_llm(user_message, assistant_response)
        except Exception as exc:
            logger.debug(f"画像提取失败 user={user_id}: {exc}")
            return
        if result is None:
            return
        profile = profile or UserProfile(user_id=user_id, group_id=gid)
        if result.nickname:
            profile.nickname_preference = result.nickname
        if result.language_style:
            profile.language_style = result.language_style
        if result.response_length:
            profile.response_length_preference = result.response_length
        for interest in result.interests_to_add:
            if interest not in profile.interests:
                profile.interests.append(interest)
        profile.interests = profile.interests[-30:]
        for k, v in result.facts_to_update.items():
            profile.facts[k] = v
        self.upsert_profile(profile)
        logger.info(f"画像已更新 user={user_id} interests={len(profile.interests)} facts={len(profile.facts)}")

    async def _extract_with_llm(
        self, user_message: str, assistant_response: str
    ) -> ProfileExtractionResult | None:
        from utils.configs import EnvConfig
        from utils.signal_llm import SignalLLM

        prompt = (
            "从以下对话中提取用户信息。仅提取明确陈述的内容，不要推测。\n\n"
            f"用户消息：{user_message[:500]}\n"
            f"助手回复：{assistant_response[:300]}\n\n"
            "返回 JSON：{\"nickname\": null, \"interests_to_add\": [], "
            "\"facts_to_update\": {}, \"language_style\": null, \"response_length\": null}\n"
            "language_style: casual/formal/technical\n"
            "response_length: brief/detailed\n"
        )
        signal = SignalLLM(model=EnvConfig.SIGNAL_MODEL, timeout=30)
        try:
            return await signal.structured(
                system_prompt="你是一个用户画像提取工具。只提取明确信息，不推测。",
                user_prompt=prompt,
                schema=ProfileExtractionResult,
            )
        except Exception:
            return None


_profile_manager: ProfileManager | None = None


def get_profile_manager() -> ProfileManager:
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager
