"""Group-scoped key/value settings (one row per value)."""

import time

from sqlmodel import Session, col, select

from .models import GroupSettings


class GroupSettingsManager:
    """群级别 key-value 设置管理器。同一 key 允许多行（支持多唤醒词等）。"""

    def __init__(self, engine):
        self.engine = engine

    def get(self, group_id: int, key: str) -> list[str]:
        def _do():
            with Session(self.engine) as session:
                rows = session.exec(
                    select(GroupSettings).where(
                        GroupSettings.group_id == group_id,
                        GroupSettings.key == key,
                    ).order_by(col(GroupSettings.id))
                ).all()
                return [row.value for row in rows]

        return _do()

    def set(self, group_id: int, key: str, value: str) -> None:
        def _do():
            now_ms = int(time.time() * 1000)
            with Session(self.engine) as session:
                row = GroupSettings(
                    group_id=group_id,
                    key=key,
                    value=value,
                    updated_at=now_ms,
                )
                session.add(row)
                session.commit()

        _do()

    def remove(self, group_id: int, key: str, value: str) -> bool:
        def _do():
            with Session(self.engine) as session:
                row = session.exec(
                    select(GroupSettings).where(
                        GroupSettings.group_id == group_id,
                        GroupSettings.key == key,
                        GroupSettings.value == value,
                    )
                ).first()
                if row is None:
                    return False
                session.delete(row)
                session.commit()
                return True

        return _do()

    def clear(self, group_id: int, key: str) -> int:
        def _do():
            with Session(self.engine) as session:
                rows = session.exec(
                    select(GroupSettings).where(
                        GroupSettings.group_id == group_id,
                        GroupSettings.key == key,
                    )
                ).all()
                count = len(rows)
                for row in rows:
                    session.delete(row)
                session.commit()
                return count

        return _do()
