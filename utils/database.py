import base64
import datetime
import os
import time
import zoneinfo

from sqlmodel import Field, Session, SQLModel, col, create_engine, desc, select

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


class MessageImage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    msg_time: int = Field(index=True)
    user_id: int = Field(index=True)
    group_id: int | None = None
    index: int = 0
    file_path: str
    file_size: int | None = None
    created_at: int
    expires_at: int


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
        MessageImage.metadata.create_all(self.engine)

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

    async def select(
        self,
        user_id: int | None = None,
        group_id: int | None = None,
        query_numbers: int = 20,
        before_time: int | None = None,
    ):
        with Session(self.engine) as session:
            if group_id:
                statement = select(Message).where(Message.group_id == group_id)
            elif user_id:
                statement = select(Message).where(Message.user_id == user_id)
            else:
                return None
            if before_time is not None:
                statement = statement.where(Message.time < before_time)
            statement = statement.order_by(desc(Message.time)).limit(query_numbers)
            results = session.exec(statement)
            return results.all()

    async def select_by_msg_id(self, *, msg_id: int, group_id: int | None) -> Message | None:
        with Session(self.engine) as session:
            statement = select(Message).where(Message.msg_id == msg_id)
            if group_id is None:
                statement = statement.where(Message.group_id.is_(None))  # type: ignore
            else:
                statement = statement.where(Message.group_id == group_id)
            statement = statement.order_by(desc(Message.time)).limit(1)
            return session.exec(statement).first()

    async def select_images_by_msg_time(self, msg_time: int) -> list[MessageImage]:
        with Session(self.engine) as session:
            statement = select(MessageImage).where(MessageImage.msg_time == msg_time).order_by(MessageImage.index)
            return session.exec(statement).all()

    @staticmethod
    def _load_image_files(image_records: list[MessageImage]) -> tuple[list[bytes], int]:
        file_images: list[bytes] = []
        missing_images = 0
        for img in sorted(image_records, key=lambda x: x.index):
            full_path = os.path.join(os.getcwd(), img.file_path)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    file_images.append(f.read())
            else:
                missing_images += 1
        return file_images, missing_images

    def load_image_files(self, image_records: list[MessageImage]) -> tuple[list[bytes], int]:
        return self._load_image_files(image_records)

    async def prepare_message(
        self,
        user_id: int | None = None,
        group_id: int | None = None,
        query_numbers: int = 20,
        before_time: int | None = None,
    ):
        messages = await self.select(
            user_id=user_id,
            group_id=group_id,
            query_numbers=query_numbers,
            before_time=before_time,
        )
        if not messages:
            return []
        messages_seq = []
        messages = list(reversed(messages))
        if before_time is None:
            messages = messages[:-1]
        if not messages:
            return []

        all_msg_times = [m.time for m in messages]

        images_by_time: dict[int, list[MessageImage]] = {}
        with Session(self.engine) as session:
            stmt = select(MessageImage).where(col(MessageImage.msg_time).in_(all_msg_times))
            for img in session.exec(stmt).all():
                images_by_time.setdefault(img.msg_time, []).append(img)

        for message in messages:
            msg_images = images_by_time.get(message.time, [])
            content_text = message.content
            file_images: list[bytes] = []

            if msg_images:
                file_images, missing_images = self._load_image_files(msg_images)
                if missing_images:
                    content_text += "\n" + " ".join("[图片]" for _ in range(missing_images))

            text_str = str(
                {
                    "metadata": {
                        "time": datetime.datetime.fromtimestamp(int(message.time / 1000))
                        .astimezone(zoneinfo.ZoneInfo("Asia/Shanghai"))
                        .strftime("%Y-%m-%d %H:%M:%S"),
                        "user_name": message.user_name,
                    },
                    "content": content_text,
                }
            )

            if file_images:
                content = [{"type": "text", "text": text_str}] + [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(b).decode()}"},
                    }
                    for b in file_images
                ]
            else:
                content = text_str

            if not messages_seq:
                messages_seq.append({"role": message.role, "content": content})
                continue

            last = messages_seq[-1]
            if message.role == last["role"] and isinstance(content, str) and isinstance(last["content"], str):
                last["content"] += f"\n{content}"
            else:
                messages_seq.append({"role": message.role, "content": content})

        return messages_seq

    async def insert_images(self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes]) -> list[str]:
        from utils.configs import EnvConfig

        now_ms = int(time.time() * 1000)
        expires_ms = now_ms + EnvConfig.IMAGE_TTL_DAYS * 86400 * 1000
        dir_path = os.path.join(os.getcwd(), "cache", "images", str(user_id))
        os.makedirs(dir_path, exist_ok=True)
        paths = []
        with Session(self.engine) as session:
            for i, image_bytes in enumerate(images):
                file_path = os.path.join("cache", "images", str(user_id), f"{msg_time}_{i}.jpg")
                with open(os.path.join(os.getcwd(), file_path), "wb") as f:
                    f.write(image_bytes)
                record = session.exec(
                    select(MessageImage).where(MessageImage.msg_time == msg_time).where(MessageImage.index == i)
                ).first()
                if record:
                    record.file_path = file_path
                    record.file_size = len(image_bytes)
                    record.expires_at = expires_ms
                else:
                    record = MessageImage(
                        msg_time=msg_time,
                        user_id=user_id,
                        group_id=group_id,
                        index=i,
                        file_path=file_path,
                        file_size=len(image_bytes),
                        created_at=now_ms,
                        expires_at=expires_ms,
                    )
                session.add(record)
                paths.append(file_path)
            session.commit()
        return paths

    async def cleanup_expired_images(self) -> int:
        now_ms = int(time.time() * 1000)
        cleaned = 0
        with Session(self.engine) as session:
            expired = session.exec(select(MessageImage).where(MessageImage.expires_at < now_ms)).all()
            for record in expired:
                full_path = os.path.join(os.getcwd(), record.file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                session.delete(record)
                cleaned += 1
            session.commit()
        return cleaned

    async def select_by_time_range(
        self,
        start_time: int,
        end_time: int,
        group_id: int | None = None,
        user_id: int | None = None,
        limit: int = 500,
    ) -> list[Message]:
        with Session(self.engine) as session:
            statement = select(Message).where(Message.time >= start_time).where(Message.time <= end_time)
            if group_id is not None:
                statement = statement.where(Message.group_id == group_id)
                if user_id is not None:
                    statement = statement.where(Message.user_id == user_id)
            elif user_id is not None:
                statement = statement.where(Message.user_id == user_id).where(Message.group_id.is_(None))  # type: ignore
            statement = statement.order_by(Message.time).limit(limit)
            return session.exec(statement).all()

    @staticmethod
    def format_for_llm(messages: list[Message]) -> str:
        """将 Message 列表格式化为 LLM 可读的纯文本。

        格式：[时间] 角色(显示名): 消息内容
        """
        tz = zoneinfo.ZoneInfo("Asia/Shanghai")
        lines = []
        for msg in messages:
            ts = datetime.datetime.fromtimestamp(msg.time / 1000, tz=tz).strftime("%Y-%m-%d %H:%M:%S")
            name = msg.user_name or ("助手" if msg.role == "assistant" else str(msg.user_id))
            role_label = "助手" if msg.role == "assistant" else "用户"
            lines.append(f"[{ts}] {role_label}({name}): {msg.content}")
        return "\n".join(lines)


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
                session.delete(target)
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
