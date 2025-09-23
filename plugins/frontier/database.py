from sqlmodel import Field, Session, SQLModel, create_engine

databases = {"users": "users"}


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    model: str


async def init():
    for i in databases.values():
        database_name = f"{i}.db"
        engine = create_engine(f"sqlite:///{database_name}")
        SQLModel.metadata.create_all(engine)


class UserDatabase:
    def __init__(self):
        self.engine = create_engine("")

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
