import asyncio
import re
import shutil
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import chromadb
import uuid_utils
from langchain_huggingface import HuggingFaceEmbeddings
from nonebot import logger

from utils.configs import EnvConfig
from utils.memory_types import (
    MemoryAnalyzeResult,
    MemoryCategory,
    MemoryRecord,
    MemoryScope,
    MemorySearchItem,
    MemoryStatus,
)

HIGH_SENSITIVE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|pwd|密码)\s*[:=]\s*[^\s]+"),
    re.compile(r"\b\d{16,19}\b"),
]
MEDIUM_SENSITIVE_PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
MEDIUM_SENSITIVE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MEDIUM_SENSITIVE_ADDRESS = re.compile(r"(地址|住址|address)\s*[:：]\s*[^\n,，]{4,}")
GROUP_FACT_HINT_PATTERN = re.compile(r"(本群|群里|群规|我们组|我们团队|大家约定|群项目|这个群)")
DATE_PATTERN = re.compile(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b")


class MemoryServiceV2:
    def __init__(self) -> None:
        self.enabled = EnvConfig.MEMORY_ENABLED
        self.model_name = EnvConfig.MEMORY_EMBEDDING_MODEL.strip() or "sentence-transformers/all-MiniLM-L6-v2"
        self.base_path = Path("./cache/chroma")
        self.schema_file = self.base_path / ".schema_version"
        self.schema_version = str(EnvConfig.MEMORY_SCHEMA_VERSION)
        self.default_task_ttl_days = max(1, int(EnvConfig.MEMORY_DEFAULT_TASK_TTL_DAYS))
        self.max_injected_memories = max(1, int(EnvConfig.MEMORY_MAX_INJECTED_MEMORIES))
        self.retrieval_user_k = max(1, int(EnvConfig.MEMORY_RETRIEVAL_USER_K))
        self.retrieval_group_k = max(1, int(EnvConfig.MEMORY_RETRIEVAL_GROUP_K))
        self.privacy_mode = EnvConfig.MEMORY_PRIVACY_MODE.strip().lower() or "balanced"
        self._persistent_client = None
        self._embeddings = None
        if self.enabled:
            self.base_path.mkdir(parents=True, exist_ok=True)

    @property
    def persistent_client(self):
        if self._persistent_client is None:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self._persistent_client = chromadb.PersistentClient(path=str(self.base_path))
        return self._persistent_client

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
        return self._embeddings

    @staticmethod
    def now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _scope_from_value(value: str | None) -> MemoryScope:
        if value == MemoryScope.GROUP.value:
            return MemoryScope.GROUP
        return MemoryScope.USER

    @staticmethod
    def _category_from_value(value: str | None) -> MemoryCategory:
        if value is None:
            return MemoryCategory.OTHER
        for category in MemoryCategory:
            if category.value == value:
                return category
        return MemoryCategory.OTHER

    @staticmethod
    def _status_from_value(value: str | None) -> MemoryStatus:
        if value == MemoryStatus.SUPERSEDED.value:
            return MemoryStatus.SUPERSEDED
        if value == MemoryStatus.DELETED.value:
            return MemoryStatus.DELETED
        return MemoryStatus.ACTIVE

    @staticmethod
    def _clamp_score(value: Any, default: float = 0.5) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            score = default
        return max(0.0, min(1.0, score))

    @staticmethod
    def _to_int(value: Any, default: int | None = None) -> int | None:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _read_schema_version(self) -> str:
        if self.schema_file.exists():
            try:
                return self.schema_file.read_text(encoding="utf-8").strip()
            except OSError:
                return ""
        return ""

    def _write_schema_version(self, version: str):
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.schema_file.write_text(version, encoding="utf-8")

    def ensure_schema_ready(self):
        if not self.enabled:
            return
        self.base_path.mkdir(parents=True, exist_ok=True)
        current = self._read_schema_version()
        expected = self.schema_version
        if current == expected:
            return
        if not EnvConfig.MEMORY_AUTO_REBUILD_ON_STARTUP:
            logger.warning(f"⚠️ memory schema mismatch: current={current or 'none'} expected={expected}")
            self._write_schema_version(expected)
            return

        backup_path = self.base_path.parent / f"chroma_backup_{int(time.time())}"
        try:
            logger.info(f"♻️ memory schema rebuilding: {current or 'none'} -> {expected}")
            if self.base_path.exists() and any(self.base_path.iterdir()):
                shutil.copytree(self.base_path, backup_path)
            if self.base_path.exists():
                shutil.rmtree(self.base_path)
            self.base_path.mkdir(parents=True, exist_ok=True)
            self._persistent_client = chromadb.PersistentClient(path=str(self.base_path))
            self._write_schema_version(expected)
            logger.info("✅ memory schema rebuild complete")
        except Exception as e:
            logger.error(f"❌ memory schema rebuild failed: {type(e).__name__}: {e}")
            try:
                if self.base_path.exists():
                    shutil.rmtree(self.base_path)
                if backup_path.exists():
                    shutil.copytree(backup_path, self.base_path)
                    self._persistent_client = chromadb.PersistentClient(path=str(self.base_path))
                    logger.warning("⚠️ memory schema rollback complete")
            except Exception as rollback_error:
                logger.error(f"❌ memory rollback failed: {type(rollback_error).__name__}: {rollback_error}")

    @staticmethod
    def user_collection_name(user_id: str) -> str:
        return f"mem_user_{user_id}"

    @staticmethod
    def group_collection_name(group_id: int) -> str:
        return f"mem_group_{group_id}"

    def _get_or_create_collection(self, collection_name: str):
        return self.persistent_client.get_or_create_collection(collection_name)

    def _get_collection_if_exists(self, collection_name: str):
        try:
            return self.persistent_client.get_collection(collection_name)
        except Exception:
            return None

    def normalize_slot_key(self, slot_key: str, category: MemoryCategory, content: str) -> str:
        key = (slot_key or "").strip().lower()
        if not key:
            short_content = re.sub(r"\s+", " ", content.strip().lower())[:40]
            key = f"{category.value}:{short_content or 'general'}"
        key = re.sub(r"[^a-z0-9._:-]+", "_", key)
        return key[:96]

    def is_explicit_group_fact(self, text: str) -> bool:
        return bool(GROUP_FACT_HINT_PATTERN.search(text))

    def should_store_group_memory(self, text: str, is_group_fact: bool) -> bool:
        return bool(is_group_fact or self.is_explicit_group_fact(text))

    def _parse_explicit_deadline(self, text: str) -> int | None:
        match = DATE_PATTERN.search(text)
        if not match:
            return None
        year, month, day = match.groups()
        try:
            dt = datetime(int(year), int(month), int(day), 23, 59, 59, tzinfo=UTC)
        except ValueError:
            return None
        return int(dt.timestamp() * 1000)

    def default_expires_at(self, category: MemoryCategory, text: str) -> int | None:
        if category in {MemoryCategory.PROFILE, MemoryCategory.PREFERENCE, MemoryCategory.GROUP_RULE}:
            return None
        if explicit_date := self._parse_explicit_deadline(text):
            return explicit_date
        return self.now_ms() + int(timedelta(days=self.default_task_ttl_days).total_seconds() * 1000)

    def is_expired(self, expires_at: int | None) -> bool:
        if expires_at is None or expires_at < 0:
            return False
        return expires_at < self.now_ms()

    def _contains_high_sensitive(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in HIGH_SENSITIVE_PATTERNS)

    def _contains_medium_sensitive(self, text: str) -> bool:
        return bool(
            MEDIUM_SENSITIVE_PHONE.search(text)
            or MEDIUM_SENSITIVE_EMAIL.search(text)
            or MEDIUM_SENSITIVE_ADDRESS.search(text)
        )

    def _mask_medium_sensitive(self, text: str) -> str:
        text = MEDIUM_SENSITIVE_PHONE.sub(lambda m: f"{m.group(0)[:3]}****{m.group(0)[-4:]}", text)
        text = MEDIUM_SENSITIVE_EMAIL.sub(lambda m: self._mask_email(m.group(0)), text)
        text = MEDIUM_SENSITIVE_ADDRESS.sub(r"\1: [已脱敏]", text)
        return text

    @staticmethod
    def _mask_email(email: str) -> str:
        parts = email.split("@", maxsplit=1)
        if len(parts) != 2:
            return "[已脱敏邮箱]"
        name, domain = parts
        if not name:
            return f"[已脱敏]@{domain}"
        return f"{name[0]}***@{domain}"

    def apply_privacy_filter(self, text: str) -> tuple[bool, str, str]:
        content = (text or "").strip()
        if not content:
            return False, "", "empty"
        if self._contains_high_sensitive(content):
            return False, "", "high_sensitive"
        if self.privacy_mode == "strict" and self._contains_medium_sensitive(content):
            return False, "", "medium_sensitive"
        if self.privacy_mode == "balanced" and self._contains_medium_sensitive(content):
            return True, self._mask_medium_sensitive(content), "masked"
        return True, content, "ok"

    def _supersede_slot_records(self, collection, scope: MemoryScope, slot_key: str, now_ms: int):
        existing = collection.get(
            where={
                "$and": [
                    {"status": {"$eq": MemoryStatus.ACTIVE.value}},
                    {"scope": {"$eq": scope.value}},
                    {"slot_key": {"$eq": slot_key}},
                ]
            },
            include=["metadatas", "documents"],
        )
        ids = existing.get("ids", [])
        if not ids:
            return
        metadatas = existing.get("metadatas", [])
        documents = existing.get("documents", [])
        updated_metadatas = []
        for metadata in metadatas:
            metadata = dict(metadata or {})
            metadata["status"] = MemoryStatus.SUPERSEDED.value
            metadata["updated_at"] = now_ms
            updated_metadatas.append(metadata)
        collection.update(ids=ids, metadatas=updated_metadatas, documents=documents)

    async def upsert_memory_record(
        self,
        scope: MemoryScope,
        owner_user_id: str,
        group_id: int | None,
        content: str,
        category: MemoryCategory,
        slot_key: str,
        importance: float,
        confidence: float,
        source_msg_id: int | None = None,
    ) -> str | None:
        if not self.enabled:
            return None
        return await asyncio.to_thread(
            self._upsert_memory_record_sync,
            scope,
            owner_user_id,
            group_id,
            content,
            category,
            slot_key,
            importance,
            confidence,
            source_msg_id,
        )

    def _upsert_memory_record_sync(
        self,
        scope: MemoryScope,
        owner_user_id: str,
        group_id: int | None,
        content: str,
        category: MemoryCategory,
        slot_key: str,
        importance: float,
        confidence: float,
        source_msg_id: int | None,
    ) -> str | None:
        collection_name = (
            self.group_collection_name(group_id)
            if scope == MemoryScope.GROUP and group_id is not None
            else self.user_collection_name(owner_user_id)
        )
        collection = self._get_or_create_collection(collection_name)
        now = self.now_ms()
        normalized_slot = self.normalize_slot_key(slot_key, category, content)
        self._supersede_slot_records(collection, scope, normalized_slot, now)

        memory_id = str(uuid_utils.uuid7())
        metadata = {
            "memory_id": memory_id,
            "scope": scope.value,
            "owner_user_id": owner_user_id,
            "group_id": group_id if group_id is not None else -1,
            "category": category.value,
            "slot_key": normalized_slot,
            "importance": self._clamp_score(importance),
            "confidence": self._clamp_score(confidence),
            "created_at": now,
            "updated_at": now,
            "expires_at": self.default_expires_at(category, content) or -1,
            "status": MemoryStatus.ACTIVE.value,
            "source_msg_id": source_msg_id if source_msg_id is not None else -1,
        }
        collection.add(ids=[memory_id], documents=[content], metadatas=[metadata])
        return memory_id

    async def persist_from_analysis(
        self,
        analysis: MemoryAnalyzeResult,
        raw_user_text: str,
        user_id: str,
        group_id: int | None,
        source_msg_id: int | None = None,
    ) -> list[str]:
        if not self.enabled or not analysis.should_memory or not analysis.memory_content:
            return []
        allow_content, sanitized_content, _ = self.apply_privacy_filter(analysis.memory_content)
        if not allow_content or not sanitized_content:
            return []

        saved_ids: list[str] = []
        user_memory_id = await self.upsert_memory_record(
            scope=MemoryScope.USER,
            owner_user_id=user_id,
            group_id=group_id,
            content=sanitized_content,
            category=analysis.category,
            slot_key=analysis.slot_key,
            importance=analysis.importance,
            confidence=analysis.confidence,
            source_msg_id=source_msg_id,
        )
        if user_memory_id:
            saved_ids.append(user_memory_id)

        if group_id is not None and self.should_store_group_memory(raw_user_text, analysis.is_group_fact):
            group_memory_id = await self.upsert_memory_record(
                scope=MemoryScope.GROUP,
                owner_user_id=user_id,
                group_id=group_id,
                content=sanitized_content,
                category=analysis.category,
                slot_key=analysis.slot_key,
                importance=analysis.importance,
                confidence=analysis.confidence,
                source_msg_id=source_msg_id,
            )
            if group_memory_id:
                saved_ids.append(group_memory_id)
        return saved_ids

    def _extract_items_from_query(self, payload: dict, fallback_scope: MemoryScope) -> list[MemorySearchItem]:
        ids = payload.get("ids", [[]])
        docs = payload.get("documents", [[]])
        metadatas = payload.get("metadatas", [[]])
        distances = payload.get("distances", [[]])

        if not ids:
            return []
        rows = zip(ids[0], docs[0], metadatas[0], distances[0], strict=False)
        result: list[MemorySearchItem] = []
        for memory_id, content, metadata, distance in rows:
            metadata = metadata or {}
            if metadata.get("status") != MemoryStatus.ACTIVE.value:
                continue
            expires_at = self._to_int(metadata.get("expires_at"))
            if self.is_expired(expires_at):
                continue
            updated_at = self._to_int(metadata.get("updated_at"), self.now_ms()) or self.now_ms()
            importance = self._clamp_score(metadata.get("importance"))
            confidence = self._clamp_score(metadata.get("confidence"))
            safe_distance = 1.0 if distance is None else float(distance)
            similarity = 1.0 / (1.0 + max(safe_distance, 0.0))
            age_days = max((self.now_ms() - updated_at) / 86_400_000, 0.0)
            freshness = 1.0 / (1.0 + age_days / 15)
            score = 0.55 * similarity + 0.2 * freshness + 0.15 * importance + 0.1 * confidence

            scope = self._scope_from_value(metadata.get("scope")) if metadata.get("scope") else fallback_scope
            category = self._category_from_value(metadata.get("category"))
            slot_key = str(metadata.get("slot_key") or f"{category.value}:general")

            result.append(
                MemorySearchItem(
                    memory_id=str(memory_id),
                    content=str(content),
                    scope=scope,
                    category=category,
                    slot_key=slot_key,
                    updated_at=updated_at,
                    importance=importance,
                    confidence=confidence,
                    score=score,
                )
            )
        return result

    def _dedupe_by_slot_latest(self, items: list[MemorySearchItem]) -> list[MemorySearchItem]:
        latest_by_slot: dict[str, MemorySearchItem] = {}
        for item in items:
            key = f"{item.scope.value}:{item.slot_key}"
            existing = latest_by_slot.get(key)
            if existing is None or item.updated_at > existing.updated_at:
                latest_by_slot[key] = item
        return sorted(latest_by_slot.values(), key=lambda x: x.score, reverse=True)

    def _query_collection_sync(
        self,
        collection_name: str,
        query_embedding: list[float],
        n_results: int,
        fallback_scope: MemoryScope,
    ) -> list[MemorySearchItem]:
        collection = self._get_collection_if_exists(collection_name)
        if collection is None:
            return []
        payload = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, n_results * 2),
            where={"status": {"$eq": MemoryStatus.ACTIVE.value}},
            include=["metadatas", "documents", "distances"],
        )
        return self._dedupe_by_slot_latest(self._extract_items_from_query(payload, fallback_scope))

    def _allocate_budget(
        self,
        user_items: list[MemorySearchItem],
        group_items: list[MemorySearchItem],
        max_items: int,
    ) -> list[MemorySearchItem]:
        if not group_items:
            return user_items[:max_items]
        selected: list[MemorySearchItem] = []
        selected.extend(user_items[:3])
        selected.extend(group_items[:1])
        remain = user_items[3:] + group_items[1:]
        remain.sort(key=lambda x: x.score, reverse=True)
        for item in remain:
            if len(selected) >= max_items:
                break
            selected.append(item)
        return sorted(selected[:max_items], key=lambda x: x.score, reverse=True)

    async def retrieve_for_injection(
        self,
        query: str,
        user_id: str,
        group_id: int | None,
        max_items: int | None = None,
    ) -> list[MemorySearchItem]:
        if not self.enabled or not query.strip():
            return []

        query_embedding = await asyncio.to_thread(self.embeddings.embed_query, query)
        user_collection = self.user_collection_name(user_id)
        tasks = [
            asyncio.to_thread(
                self._query_collection_sync,
                user_collection,
                query_embedding,
                self.retrieval_user_k,
                MemoryScope.USER,
            )
        ]
        if group_id is not None:
            group_collection = self.group_collection_name(group_id)
            tasks.append(
                asyncio.to_thread(
                    self._query_collection_sync,
                    group_collection,
                    query_embedding,
                    self.retrieval_group_k,
                    MemoryScope.GROUP,
                )
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        user_items: list[MemorySearchItem] = []
        group_items: list[MemorySearchItem] = []
        if results:
            if isinstance(results[0], Exception):
                logger.warning(f"⚠️ user memory retrieval failed: {results[0]}")
            else:
                user_items = results[0]
        if len(results) > 1:
            if isinstance(results[1], Exception):
                logger.warning(f"⚠️ group memory retrieval failed: {results[1]}")
            else:
                group_items = results[1]

        max_budget = max_items or self.max_injected_memories
        return self._allocate_budget(user_items, group_items, max_budget)

    def format_for_injection(self, items: list[MemorySearchItem]) -> str:
        if not items:
            return ""
        lines = [
            "Memory Context:",
            "Use only if relevant. Do not repeat this block verbatim.",
        ]
        for item in items:
            lines.append(
                f"- [{item.scope.value}|{item.category.value}|slot={item.slot_key}|id={item.memory_id}] {item.content}"
            )
        return "\n".join(lines)

    def format_memory_list(self, records: list[MemoryRecord]) -> str:
        if not records:
            return "暂无可用记忆。"
        lines = []
        for item in records:
            expires = (
                "never"
                if item.expires_at is None
                else datetime.fromtimestamp(item.expires_at / 1000).strftime("%Y-%m-%d")
            )
            lines.append(
                f"- id={item.memory_id} | {item.scope.value}/{item.category.value} | expires={expires} | {item.content}"
            )
        return "\n".join(lines)

    def _build_record(self, memory_id: str, content: str, metadata: dict[str, Any]) -> MemoryRecord:
        group_id_value = self._to_int(metadata.get("group_id"))
        if group_id_value == -1:
            group_id_value = None
        source_msg_id = self._to_int(metadata.get("source_msg_id"))
        if source_msg_id == -1:
            source_msg_id = None
        return MemoryRecord(
            memory_id=str(memory_id),
            content=str(content),
            scope=self._scope_from_value(str(metadata.get("scope"))),
            owner_user_id=str(metadata.get("owner_user_id") or ""),
            group_id=group_id_value,
            category=self._category_from_value(str(metadata.get("category"))),
            slot_key=str(metadata.get("slot_key") or "general"),
            importance=self._clamp_score(metadata.get("importance")),
            confidence=self._clamp_score(metadata.get("confidence")),
            created_at=self._to_int(metadata.get("created_at"), self.now_ms()) or self.now_ms(),
            updated_at=self._to_int(metadata.get("updated_at"), self.now_ms()) or self.now_ms(),
            expires_at=None if self._to_int(metadata.get("expires_at")) == -1 else self._to_int(metadata.get("expires_at")),
            status=self._status_from_value(str(metadata.get("status"))),
            source_msg_id=source_msg_id,
        )

    def _list_collection_sync(self, collection_name: str, limit: int) -> list[MemoryRecord]:
        collection = self._get_collection_if_exists(collection_name)
        if collection is None:
            return []
        payload = collection.get(
            where={"status": {"$eq": MemoryStatus.ACTIVE.value}},
            include=["metadatas", "documents"],
            limit=max(1, limit * 3),
        )
        ids = payload.get("ids", [])
        docs = payload.get("documents", [])
        metadatas = payload.get("metadatas", [])
        records: list[MemoryRecord] = []
        for memory_id, content, metadata in zip(ids, docs, metadatas, strict=False):
            metadata = metadata or {}
            expires_at = self._to_int(metadata.get("expires_at"))
            if self.is_expired(expires_at):
                continue
            records.append(self._build_record(str(memory_id), str(content), metadata))
        records.sort(key=lambda x: x.updated_at, reverse=True)
        return records[:limit]

    async def list_memories(
        self,
        scope: MemoryScope,
        user_id: str,
        group_id: int | None,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        if not self.enabled:
            return []
        collection_name = (
            self.group_collection_name(group_id)
            if scope == MemoryScope.GROUP and group_id is not None
            else self.user_collection_name(user_id)
        )
        return await asyncio.to_thread(self._list_collection_sync, collection_name, max(1, limit))

    def _get_record_payload_sync(self, collection_name: str, memory_id: str) -> tuple[Any, dict | None]:
        collection = self._get_collection_if_exists(collection_name)
        if collection is None:
            return None, None
        payload = collection.get(ids=[memory_id], include=["metadatas", "documents"])
        ids = payload.get("ids", [])
        if not ids:
            return collection, None
        metadata = (payload.get("metadatas") or [{}])[0] or {}
        document = (payload.get("documents") or [""])[0] or ""
        return collection, {"metadata": metadata, "document": document}

    def _soft_delete_in_collection(self, collection, memory_id: str, payload: dict) -> bool:
        metadata = dict(payload["metadata"])
        document = payload["document"]
        metadata["status"] = MemoryStatus.DELETED.value
        metadata["updated_at"] = self.now_ms()
        collection.update(ids=[memory_id], metadatas=[metadata], documents=[document])
        return True

    def _soft_delete_sync(
        self,
        memory_id: str,
        user_id: str,
        group_id: int | None,
        allow_group_delete: bool,
        preferred_scope: MemoryScope | None = None,
    ) -> tuple[bool, str]:
        if preferred_scope != MemoryScope.GROUP:
            user_collection = self.user_collection_name(user_id)
            collection, payload = self._get_record_payload_sync(user_collection, memory_id)
            if payload is not None:
                owner = str(payload["metadata"].get("owner_user_id") or "")
                if owner != user_id:
                    return False, "无权限删除该个人记忆。"
                self._soft_delete_in_collection(collection, memory_id, payload)
                return True, "已删除个人记忆。"

        if group_id is not None and preferred_scope != MemoryScope.USER:
            group_collection = self.group_collection_name(group_id)
            collection, payload = self._get_record_payload_sync(group_collection, memory_id)
            if payload is not None:
                if not allow_group_delete:
                    return False, "无权限删除群记忆。"
                self._soft_delete_in_collection(collection, memory_id, payload)
                return True, "已删除群记忆。"
        return False, "未找到对应记忆 ID。"

    async def soft_delete_memory(
        self,
        memory_id: str,
        user_id: str,
        group_id: int | None,
        allow_group_delete: bool = False,
        preferred_scope: MemoryScope | None = None,
    ) -> tuple[bool, str]:
        if not self.enabled:
            return False, "记忆系统未启用。"
        return await asyncio.to_thread(
            self._soft_delete_sync,
            memory_id,
            user_id,
            group_id,
            allow_group_delete,
            preferred_scope,
        )

    def _clear_scope_sync(self, collection_name: str) -> int:
        collection = self._get_collection_if_exists(collection_name)
        if collection is None:
            return 0
        payload = collection.get(
            where={"status": {"$eq": MemoryStatus.ACTIVE.value}},
            include=["metadatas", "documents"],
        )
        ids = payload.get("ids", [])
        if not ids:
            return 0
        metadatas = payload.get("metadatas", [])
        documents = payload.get("documents", [])
        now = self.now_ms()
        updated = []
        for metadata in metadatas:
            metadata = dict(metadata or {})
            metadata["status"] = MemoryStatus.DELETED.value
            metadata["updated_at"] = now
            updated.append(metadata)
        collection.update(ids=ids, metadatas=updated, documents=documents)
        return len(ids)

    async def clear_memories(
        self,
        scope: MemoryScope,
        user_id: str,
        group_id: int | None,
        allow_group_delete: bool = False,
    ) -> tuple[int, str]:
        if not self.enabled:
            return 0, "记忆系统未启用。"
        if scope == MemoryScope.GROUP:
            if group_id is None:
                return 0, "当前不在群聊中。"
            if not allow_group_delete:
                return 0, "无权限清空群记忆。"
            count = await asyncio.to_thread(self._clear_scope_sync, self.group_collection_name(group_id))
            return count, f"已清空 {count} 条群记忆。"

        count = await asyncio.to_thread(self._clear_scope_sync, self.user_collection_name(user_id))
        return count, f"已清空 {count} 条个人记忆。"

    async def search_scope_raw(self, collection_name: str, query: str, result_number: int = 3) -> str:
        if not self.enabled:
            return ""
        query_embedding = await asyncio.to_thread(self.embeddings.embed_query, query)
        result = await asyncio.to_thread(
            self._query_collection_sync,
            collection_name,
            query_embedding,
            result_number,
            MemoryScope.USER,
        )
        return "".join(f"* {item.content}\n" for item in result[:result_number])

    async def add(self, collection_name: str, documents: list, uuids: list):
        if not self.enabled:
            return
        await asyncio.to_thread(self._add_sync, collection_name, documents, uuids)

    def _add_sync(self, collection_name: str, documents: list, uuids: list):
        collection = self._get_or_create_collection(collection_name)
        now = self.now_ms()
        metadatas = []
        for memory_id in uuids:
            metadatas.append(
                {
                    "memory_id": str(memory_id),
                    "scope": MemoryScope.USER.value,
                    "owner_user_id": collection_name,
                    "group_id": -1,
                    "category": MemoryCategory.OTHER.value,
                    "slot_key": f"legacy:{memory_id}",
                    "importance": 0.5,
                    "confidence": 0.5,
                    "created_at": now,
                    "updated_at": now,
                    "expires_at": -1,
                    "status": MemoryStatus.ACTIVE.value,
                    "source_msg_id": -1,
                }
            )
        collection.add(ids=[str(x) for x in uuids], documents=[str(x) for x in documents], metadatas=metadatas)

    async def delete(self, collection_name: str, ids: list):
        if not self.enabled:
            return
        await asyncio.to_thread(self._delete_sync, collection_name, ids)

    def _delete_sync(self, collection_name: str, ids: list):
        collection = self._get_collection_if_exists(collection_name)
        if collection is None:
            return
        collection.delete(ids=[str(x) for x in ids])

    async def similarity_search(self, collection_name: str, query: str, filter: dict):
        _ = filter
        return await self.search_scope_raw(collection_name, query, result_number=2)

    async def mmr_search(self, collection_name: str, query: str, result_number: int, filter: dict):
        _ = filter
        return await self.search_scope_raw(collection_name, query, result_number=result_number)


_memory_service: MemoryServiceV2 | None = None


def get_memory_service() -> MemoryServiceV2:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryServiceV2()
    return _memory_service


MemoryStore = MemoryServiceV2
