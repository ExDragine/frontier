from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class MemoryScope(str, Enum):
    USER = "user"
    GROUP = "group"


class MemoryCategory(str, Enum):
    PROFILE = "profile"
    PREFERENCE = "preference"
    GROUP_RULE = "group_rule"
    TASK = "task"
    PLAN = "plan"
    PROJECT = "project"
    DEADLINE = "deadline"
    OTHER = "other"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DELETED = "deleted"


class MemoryAnalyzeResult(BaseModel):
    should_memory: bool = Field(default=False)
    memory_content: str = Field(default="")
    category: MemoryCategory = Field(default=MemoryCategory.OTHER)
    slot_key: str = Field(default="general")
    importance: float = Field(default=0.5)
    confidence: float = Field(default=0.5)
    is_group_fact: bool = Field(default=False)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if isinstance(value, MemoryCategory):
            return value
        if value is None:
            return MemoryCategory.OTHER
        value_str = str(value).strip().lower()
        for category in MemoryCategory:
            if category.value == value_str:
                return category
        return MemoryCategory.OTHER

    @field_validator("importance", "confidence", mode="before")
    @classmethod
    def normalize_score(cls, value):
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, score))

    @model_validator(mode="after")
    def normalize_content(self):
        if not self.should_memory:
            self.memory_content = ""
            self.slot_key = "general"
            self.is_group_fact = False
        self.memory_content = self.memory_content.strip()
        self.slot_key = self.slot_key.strip() or "general"
        return self


class MemoryRecord(BaseModel):
    memory_id: str
    content: str
    scope: MemoryScope
    owner_user_id: str
    group_id: int | None = None
    category: MemoryCategory
    slot_key: str
    importance: float = 0.5
    confidence: float = 0.5
    created_at: int
    updated_at: int
    expires_at: int | None = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    source_msg_id: int | None = None


class MemorySearchItem(BaseModel):
    memory_id: str
    content: str
    scope: MemoryScope
    category: MemoryCategory
    slot_key: str
    updated_at: int
    importance: float
    confidence: float
    score: float
