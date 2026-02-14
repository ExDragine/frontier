from fastapi import APIRouter

from .auth_routes import router as auth_router
from .messages_routes import router as messages_router
from .settings_routes import router as settings_router
from .status_routes import router as status_router
from .tasks_routes import router as tasks_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(status_router, prefix="/status", tags=["status"])
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(messages_router, prefix="/messages", tags=["messages"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])
