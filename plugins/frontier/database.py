from sqlmodel import Field, Session, SQLModel, create_engine, delete, select


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    model: str


class Message(SQLModel, table=True):
    time: int
    msg_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    group_id: int | None = Field(default=None, index=True)
    user_name: str
    role: str
    content: str


class UserDatabase:
    def __init__(self):
        self.engine = create_engine("sqlite:///user_settings.db")
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
        self.engine = create_engine("sqlite:///messages.db")
        Message.metadata.create_all(self.engine)

    async def insert(
        self,
        time: int,
        msg_id: int | None,
        user_id: int,
        group_id: int | None,
        user_name: str,
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

    async def select(self, user_id: int):
        with Session(self.engine) as session:
            statement = select(Message).where(Message.user_id == user_id)
            results = session.exec(statement)
            return results.all()

    async def delete(self, user_id: int):
        with Session(self.engine) as session:
            statement = delete(Message).where(Message.user_id == user_id)
            session.exec(statement)
            session.commit()
