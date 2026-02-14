from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from utils.database import Message

from ..auth import require_auth
from ..db import engine

router = APIRouter()


@router.get("/")
async def list_messages(
    group_id: Optional[int] = None,
    user_id: Optional[int] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    user: dict = Depends(require_auth),
):
    """分页查询消息列表"""
    with Session(engine) as session:
        statement = select(Message)

        if group_id is not None:
            statement = statement.where(Message.group_id == group_id)
        if user_id is not None:
            statement = statement.where(Message.user_id == user_id)
        if role:
            statement = statement.where(Message.role == role)
        if search:
            statement = statement.where(Message.content.contains(search))  # type: ignore
        if start_time is not None:
            statement = statement.where(Message.time >= start_time)
        if end_time is not None:
            statement = statement.where(Message.time <= end_time)

        # 总数
        count_stmt = select(func.count()).select_from(statement.subquery())
        total = session.exec(count_stmt).one()

        # 分页查询
        statement = (
            statement.order_by(Message.time.desc())  # type: ignore
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        messages = session.exec(statement).all()

        return {
            "messages": [
                {
                    "time": m.time,
                    "msg_id": m.msg_id,
                    "user_id": m.user_id,
                    "group_id": m.group_id,
                    "user_name": m.user_name,
                    "role": m.role,
                    "content": m.content,
                }
                for m in messages
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        }


@router.get("/groups")
async def list_groups(user: dict = Depends(require_auth)):
    """获取所有群组及其消息数量"""
    with Session(engine) as session:
        statement = (
            select(Message.group_id, func.count().label("count"))
            .where(Message.group_id.is_not(None))  # type: ignore
            .group_by(Message.group_id)
            .order_by(func.count().desc())
        )
        results = session.exec(statement).all()

        return {"groups": [{"group_id": row[0], "message_count": row[1]} for row in results if row[0] is not None]}


@router.get("/users")
async def list_users(user: dict = Depends(require_auth)):
    """获取所有用户及其消息数量"""
    with Session(engine) as session:
        statement = (
            select(Message.user_id, Message.user_name, func.count().label("count"))
            .group_by(Message.user_id)
            .order_by(func.count().desc())
            .limit(200)
        )
        results = session.exec(statement).all()

        return {
            "users": [
                {
                    "user_id": row[0],
                    "user_name": row[1],
                    "message_count": row[2],
                }
                for row in results
            ]
        }
