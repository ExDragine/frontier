from sqlmodel import Field, Session, SQLModel, create_engine


class TimeStamp(SQLModel, table=True):
    name: str = Field(primary_key=True, index=True)
    id: str | None


class EventDatabase:
    def __init__(self):
        self.engine = create_engine("sqlite:///clockwork.db")
        TimeStamp.metadata.create_all(self.engine)

    async def insert(self, name, id: str | None = None):
        with Session(self.engine) as session:
            target = TimeStamp(name=name, id=id)
            session.add(target)
            session.commit()

    async def delete(self, name):
        with Session(self.engine) as session:
            target = session.get(TimeStamp, name)
            if target:
                session.delete(name)
                session.commit()

    async def update(self, name, id):
        with Session(self.engine) as session:
            target = session.get(TimeStamp, name)
            if target:
                target.id = id
                session.add(target)
                session.commit()

    async def select(self, name):
        with Session(self.engine) as session:
            target = session.get(TimeStamp, name)
            if target:
                return target.id
