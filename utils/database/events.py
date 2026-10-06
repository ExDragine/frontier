"""Named key/value event store shared by clockwork and wolfx."""

from sqlmodel import Session

from .engine import _run_database, get_engine
from .models import TimeStamp


class EventDatabase:
    def __init__(self):
        self.engine = get_engine()
        TimeStamp.metadata.create_all(self.engine)

    async def insert(self, name, id: str | None = None):
        def _do():
            with Session(self.engine) as session:
                target = TimeStamp(name=name, id=id)
                session.add(target)
                session.commit()

        await _run_database(self.engine, _do)

    async def delete(self, name):
        def _do():
            with Session(self.engine) as session:
                target = session.get(TimeStamp, name)
                if target:
                    session.delete(target)
                    session.commit()

        await _run_database(self.engine, _do)

    async def update(self, name, id):
        def _do():
            with Session(self.engine) as session:
                target = session.get(TimeStamp, name)
                if target:
                    target.id = id
                    session.add(target)
                    session.commit()

        await _run_database(self.engine, _do)

    async def select(self, name):
        def _do():
            with Session(self.engine) as session:
                target = session.get(TimeStamp, name)
                if target:
                    return target.id
                return None

        return await _run_database(self.engine, _do)
