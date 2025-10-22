from sqlmodel import Field, Session, SQLModel, create_engine, desc, select

DATABASE_FILE = "sqlite:///frontier.db"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    model: str


class Message(SQLModel, table=True):
    time: int = Field(primary_key=True)
    msg_id: int | None = Field(default=None)
    user_id: int = Field(index=True)
    group_id: int | None = Field(default=None, index=True)
    user_name: str | None
    role: str
    content: str


class TimeStamp(SQLModel, table=True):
    name: str = Field(primary_key=True, index=True)
    id: str | None


class UserDatabase:
    def __init__(self):
        self.engine = create_engine(DATABASE_FILE)
        User.metadata.create_all(self.engine)

    async def insert(self, user_id, user_name, custom_model):
        with Session(self.engine) as session:
            user = User(id=user_id, name=user_name, model=custom_model)
            session.add(user)
            session.commit()

    async def select(self, user_id: int):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            return user

    async def update(self, user_id):
        with Session(self.engine) as session:
            user = await self.select(user_id)
            if user:
                user.name = ""
                session.add(user)
                session.commit()

    async def delete(self, user_id):
        with Session(self.engine) as session:
            user = await self.select(user_id)
            if user:
                session.delete(user)
                session.commit()


class MessageDatabase:
    def __init__(self):
        self.engine = create_engine(DATABASE_FILE)
        Message.metadata.create_all(self.engine)

    async def insert(
        self,
        time: int,
        msg_id: int | None,
        user_id: int,
        group_id: int | None,
        user_name: str | None,
        role: str,
        content: str,
    ):
        with Session(self.engine) as session:
            message = Message(
                time=time,
                msg_id=msg_id,
                user_id=user_id,
                group_id=group_id,
                user_name=user_name,
                role=role,
                content=content,
            )
            session.add(message)
            session.commit()

    async def select(self, user_id: int | None = None, group_id: int | None = None, query_numbers: int = 20):
        with Session(self.engine) as session:
            if group_id:
                statement = (
                    select(Message)
                    .where(Message.group_id == group_id)
                    .order_by(desc(Message.time))
                    .limit(query_numbers)
                )
            elif user_id:
                statement = (
                    select(Message)
                    .where(Message.user_id == user_id and Message.group_id is None)
                    .order_by(desc(Message.time))
                    .limit(query_numbers)
                )
            else:
                return None
            results = session.exec(statement)
            return results.all()

    async def prepare_message(self, user_id: int | None = None, group_id: int | None = None, query_numbers: int = 20):
        messages = await self.select(user_id=user_id, group_id=group_id, query_numbers=query_numbers)
        if not messages:
            return []
        messages_seq = []
        messages = reversed(messages)
        messages = list(messages)[:-1]
        for message in messages:
            if not messages_seq:
                messages_seq.append({"role": message.role, "content": message.content})
                continue
            if message.role == messages_seq[-1]["role"]:
                messages_seq[-1]["content"] += f"\n{message.content}"
            else:
                messages_seq.append({"role": message.role, "content": message.content})
        return messages_seq


class EventDatabase:
    def __init__(self):
        self.engine = create_engine(DATABASE_FILE)
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
