"""Deep Agent workspace and filesystem backend construction."""

import os
import time
from pathlib import Path

from deepagents.backends import CompositeBackend, FilesystemBackend
from nonebot import logger

SKILLS_BACKEND_PATH = "/skills"
MEMORY_BACKEND_PATH = "/memory"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def build_agent_backend(working_dir: str, workspace_key: str) -> CompositeBackend:
    workspace_dir = ensure_dir(os.path.join(working_dir, "workspaces", workspace_key))
    skills_dir = str(PROJECT_ROOT / "skills")
    memory_dir = ensure_dir(os.path.join(working_dir, "memory", workspace_key))
    soul_md = os.path.join(memory_dir, "SOUL.md")
    if os.path.exists(soul_md):
        try:
            with open(soul_md, encoding="utf-8") as existing_memory:
                existing_memory.read()
        except UnicodeDecodeError as exc:
            backup_path = f"{soul_md}.corrupt-{time.time_ns()}"
            os.replace(soul_md, backup_path)
            logger.warning(f"检测到非 UTF-8 的 SOUL memory，已备份并恢复空文件: {soul_md} -> {backup_path} ({exc})")
    if not os.path.exists(soul_md):
        with open(soul_md, "w", encoding="utf-8"):
            pass

    return CompositeBackend(
        default=FilesystemBackend(root_dir=workspace_dir, virtual_mode=True),
        routes={
            f"{SKILLS_BACKEND_PATH}/": FilesystemBackend(root_dir=skills_dir, virtual_mode=True),
            f"{MEMORY_BACKEND_PATH}/{workspace_key}/": FilesystemBackend(root_dir=memory_dir, virtual_mode=True),
        },
    )
