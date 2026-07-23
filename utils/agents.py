import asyncio
import base64
import json
import os
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend
from deepagents.graph import DeepAgentState
from langchain.agents import create_agent
from langchain.agents.middleware import (
    FilesystemFileSearchMiddleware,
    ModelRetryMiddleware,
    PIIMiddleware,
    ToolRetryMiddleware,
)
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_quickjs import CodeInterpreterMiddleware
from nonebot import logger
from pydantic import BaseModel, Field, ValidationError

from tools import agent_tools
from utils.agent_context import FrontierRuntimeContext
from utils.configs import EnvConfig
from utils.harness_profiles import register_frontier_harness_profiles
from utils.llm_factory import create_llm, model_supports, provider_uses_responses_api
from utils.message import extract_message_text
from utils.progress_messages import subagent_message as _subagent_message
from utils.progress_messages import tool_message as _tool_message
from utils.subagents import build_earth_data_subagent, build_memory_subagent

ProgressReporter = Callable[["ProgressEvent"], Awaitable[None]]


@dataclass
class ProgressEvent:
    """agent 执行过程中的用户可读进度事件。

    reporter 层根据 type 决定是否向用户展示。当前私聊 reporter 消费
    thinking / subagent_start / tool_call，其余类型预留。
    """

    type: Literal[
        "thinking",  # Agent 开始思考（stream.messages 首个 LLM 消息）
        "tool_call",  # 工具开始执行（stream.tool_calls 新条目）
        "tool_result",  # 工具执行完成或失败
        "subagent_start",  # 子代理启动（stream.subagents 新条目）
        "subagent_done",  # 子代理完成或失败
        "text_delta",  # 段落级文本增量（预留，markdown 结构不能拆）
        "done",  # Agent 执行完成或出错
    ]
    message: str  # 用户可读的中文描述
    detail: dict[str, Any] | None = None  # 结构化附加信息


VISION_OMITTED_NOTICE = "[图片已省略：当前模型不支持视觉输入]"
SKILLS_BACKEND_PATH = "/skills"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY_BACKEND_PATH = "/memory"

register_frontier_harness_profiles()


# 截图/录屏工具硬门控：通过 Signal LLM 判断用户原始意图，仅当用户明确想"看网页外观"时才暴露对应工具
class BrowserCaptureIntent(BaseModel):
    """Signal LLM 对用户消息的截图/录屏意图判断结果。"""

    screenshot: bool = Field(
        description="用户是否要求查看某个网页的可视化外观（截图/拍照/快照/看看长啥样/打开看看等）"
    )
    recording: bool = Field(description="用户是否要求录制网页视频（录屏/录制/录视频等）")


async def _detect_browser_capture_intent(user_text: str | None) -> set[str]:
    """使用 Signal LLM 检测用户消息是否明确请求截图或录屏。

    仅判断用户的原始意图 —— 用户没说要"看网页长什么样"，工具就不暴露。
    Agent 无法在工作流中把截图/录屏当作其他工具失败后的"兜底方案"。
    """
    if not user_text:
        return set()
    from utils.signal_llm import signal_structured

    try:
        result: BrowserCaptureIntent = await signal_structured(
            system_prompt=(
                '判断用户消息是否明确表达了"想看到某个网页的可视化外观"的意图。\n\n'
                "以下情况 screenshot 应为 True：\n"
                "- 明确说截图、拍照、快照、截屏、screenshot\n"
                '- "来张XX看看"、"打开XX看看"、"看看XX长啥样"、"XX首页什么样的"\n'
                '- "帮我打开XX网站"、"访问XX页面"并带有查看意图\n\n'
                "以下情况 recording 应为 True：\n"
                "- 明确说录屏、录制、录视频、record/recording\n"
                '- "把XX录下来"、"录一段XX"\n\n'
                "以下情况应返回 False：\n"
                '- 用户只是提到"截图"但不是要求截图（如"你看这个截图"、"截图里的内容"）\n'
                "- 普通问答、搜索、查数据、天气等不涉及网页外观的请求\n"
                '- 模糊回应如"好"、"可以"、"行"\n'
                "- 台风、雷达图、云图、卫星云图、天气图等气象数据可视化请求——这些是数据产品，不是网页截图\n"
                '- "叠加雷达""叠加云图""看看雷达""看看云图"等台风工具内的图层叠加选项'
            ),
            user_prompt=user_text,
            schema=BrowserCaptureIntent,
        )
    except Exception:
        logger.warning("Signal LLM 截图/录屏意图检测失败，默认不暴露工具")
        return set()

    tools: set[str] = set()
    if result.screenshot:
        tools.add("webpage_screenshot")
    if result.recording:
        tools.add("webpage_recording")
    return tools


def _configured_model_route(model: str, role: Literal["basic", "signal", "advanced"] | None = None) -> dict[str, str]:
    if role == "basic":
        return {"provider": EnvConfig.BASIC_MODEL_PROVIDER}
    if role == "signal":
        return {"provider": EnvConfig.SIGNAL_MODEL_PROVIDER}
    if role == "advanced":
        return {"provider": EnvConfig.ADVAN_MODEL_PROVIDER}
    if model == EnvConfig.BASIC_MODEL:
        return {"provider": EnvConfig.BASIC_MODEL_PROVIDER}
    if model == EnvConfig.ADVAN_MODEL:
        return {"provider": EnvConfig.ADVAN_MODEL_PROVIDER}
    if model == EnvConfig.SIGNAL_MODEL:
        return {"provider": EnvConfig.SIGNAL_MODEL_PROVIDER}
    return {}


def _append_vision_notice(text: str) -> str:
    return f"{text}\n\n{VISION_OMITTED_NOTICE}" if text else VISION_OMITTED_NOTICE


def _build_user_content(text: str, images: list[bytes] | None, supports_vision: bool = True) -> str | list:
    if not images:
        return text
    if not supports_vision:
        return _append_vision_notice(text)
    return [{"type": "text", "text": text}] + [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(b).decode()}"}}
        for b in images
    ]


def _filter_content_parts_for_text_model(content: list) -> list:
    filtered = [part for part in content if not (isinstance(part, dict) and part.get("type") == "image_url")]
    if len(filtered) == len(content):
        return content
    for index, part in enumerate(filtered):
        if isinstance(part, dict) and part.get("type") == "text":
            updated_part = dict(part)
            updated_part["text"] = _append_vision_notice(str(part.get("text", "")))
            return [*filtered[:index], updated_part, *filtered[index + 1 :]]
    return [{"type": "text", "text": VISION_OMITTED_NOTICE}, *filtered]


def _filter_messages_for_model_capabilities(
    messages: list[dict],
    model: str,
    *,
    role: Literal["basic", "signal", "advanced"] | None = None,
) -> list[dict]:
    if model_supports(model, "vision", role=role):
        return messages
    filtered_messages = []
    for message in messages:
        if not isinstance(message, dict):
            filtered_messages.append(message)
            continue
        content = message.get("content")
        if isinstance(content, list):
            filtered_messages.append({**message, "content": _filter_content_parts_for_text_model(content)})
        else:
            filtered_messages.append(message)
    return filtered_messages


def _json_document_candidates(text: str, *, prefer_object: bool = False) -> list[str]:
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        text = fenced_match.group(1).strip()

    decoder = json.JSONDecoder()
    candidates = []
    for index, char in enumerate(text):
        if char not in ("{" if prefer_object else "{["):
            continue
        try:
            _, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        candidates.append(text[index : index + end])
    return candidates or [text]


def _parse_structured_response_from_messages(messages: list, response_format):
    for message in reversed(messages):
        if getattr(message, "type", None) != "ai":
            continue
        text = extract_message_text(message).strip()
        if not text:
            continue
        if hasattr(response_format, "model_validate_json"):
            last_error = None
            for candidate in _json_document_candidates(text, prefer_object=True):
                try:
                    return response_format.model_validate_json(candidate)
                except ValidationError as e:
                    last_error = e
            if last_error is not None:
                raise last_error
        break
    raise KeyError("structured_response")


async def _emit_progress(reporter: ProgressReporter | None, event: ProgressEvent) -> None:
    """安全调用 reporter —— reporter 自身异常不中断 agent 执行。"""
    if reporter is None:
        return
    try:
        await reporter(event)
    except Exception as e:
        logger.warning(f"Progress reporter 调用失败: {type(e).__name__}: {e}")


async def _collect_progress(stream, reporter: ProgressReporter | None) -> None:  # noqa: C901
    """消费 astream_events v3 的三个 projection，生成 ProgressEvent。

    优化点: 连续重复工具/子代理去重 — 相同 name 连续出现时只播报第一条。

    独立任务运行，异常不传播到 output 收集路径。
    每个 projection consumer 有独立的 try/except 保护。
    """

    async def consume_subagents() -> None:
        last_subagent_event: tuple[str, str] | None = None
        async for subagent in stream.subagents:
            name = subagent.name
            raw_status = getattr(subagent, "status", None)
            status = raw_status.lower() if isinstance(raw_status, str) else "started"
            terminal = status in {"completed", "complete", "done", "failed", "error"}
            phase = "done" if terminal else "start"
            event_key = (name, phase)
            if event_key == last_subagent_event:
                continue
            last_subagent_event = event_key
            if terminal:
                failed = status in {"failed", "error"}
                await _emit_progress(
                    reporter,
                    ProgressEvent(
                        type="subagent_done",
                        message=f"{name} {'执行失败' if failed else '已完成'}",
                        detail={"name": name, "status": status},
                    ),
                )
                continue
            await _emit_progress(
                reporter,
                ProgressEvent(
                    type="subagent_start",
                    message=_subagent_message(name),
                    detail={"name": name},
                ),
            )

    async def consume_tool_calls() -> None:
        last_tool_name: str | None = None
        async for tool_call in stream.tool_calls:
            tool_name = tool_call.tool_name
            if tool_name != last_tool_name:
                last_tool_name = tool_name
                await _emit_progress(
                    reporter,
                    ProgressEvent(
                        type="tool_call",
                        message=_tool_message(tool_name),
                        detail={"tool_name": tool_name},
                    ),
                )
            completed = getattr(tool_call, "completed", None)
            error = getattr(tool_call, "error", None)
            failed = isinstance(error, BaseException) or (isinstance(error, str) and bool(error))
            if completed is True or failed:
                await _emit_progress(
                    reporter,
                    ProgressEvent(
                        type="tool_result",
                        message=f"{tool_name} {'执行失败' if failed else '已完成'}",
                        detail={"tool_name": tool_name, "success": not failed},
                    ),
                )

    async def consume_messages() -> None:
        first_message = True
        text_buffer: str = ""
        async for message in stream.messages:
            if first_message:
                await _emit_progress(
                    reporter,
                    ProgressEvent(type="thinking", message="正在思考…"),
                )
                first_message = False
            # text_delta 累积并按段落切分（代码保留，reporter 层暂不消费）
            async for chunk in message.text:
                text_buffer += chunk
                while "\n\n" in text_buffer:
                    idx = text_buffer.index("\n\n")
                    paragraph = text_buffer[:idx].strip()
                    text_buffer = text_buffer[idx + 2 :]
                    if paragraph:
                        await _emit_progress(
                            reporter,
                            ProgressEvent(type="text_delta", message=paragraph),
                        )

    async def _safe(coro) -> None:
        try:
            await coro
        except Exception as e:
            logger.warning(f"Progress collector 异常: {type(e).__name__}: {e}")

    await asyncio.gather(
        _safe(consume_subagents()),
        _safe(consume_tool_calls()),
        _safe(consume_messages()),
    )


async def _finish_progress_collection(progress_task: asyncio.Task) -> None:
    """Drain closed projections briefly, then stop a stuck collector."""
    try:
        await asyncio.wait_for(progress_task, timeout=1)
    except TimeoutError:
        logger.debug("Progress projections 未在响应完成后及时关闭，已停止收集")
    finally:
        if not progress_task.done():
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass


async def assistant_agent(
    system_prompt: str = "",
    user_prompt: str = "",
    use_model: str | None = None,
    model_role: Literal["basic", "signal", "advanced"] | None = None,
    tools=None,
    response_format=None,
    middleware=None,
    images: list[bytes] | None = None,
    reasoning_effort: str | None = None,
    temperature: float | None = None,
    model_kwargs: dict | None = None,
) -> Any:
    if use_model is None:
        use_model = EnvConfig.BASIC_MODEL
        model_role = model_role or "basic"
    route = _configured_model_route(use_model, model_role)
    llm_kwargs: dict[str, Any] = {
        "model": use_model,
        "streaming": False,
        "max_retries": 2,
        "timeout": 300,
        **route,
    }
    if reasoning_effort is not None and provider_uses_responses_api(use_model, route.get("provider")):
        llm_kwargs["reasoning_effort"] = reasoning_effort
    if temperature is not None:
        llm_kwargs["temperature"] = temperature
    if model_kwargs is not None:
        llm_kwargs["model_kwargs"] = model_kwargs
    model = create_llm(**llm_kwargs)
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=middleware or [],
        response_format=response_format,
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": _build_user_content(
                        user_prompt,
                        images,
                        supports_vision=model_supports(use_model, "vision", role=model_role),
                    ),
                }
            ]
        }
    )
    if response_format:
        if "structured_response" in result:
            return result["structured_response"]
        return _parse_structured_response_from_messages(result.get("messages", []), response_format)
    content = ""
    for msg in result["messages"]:
        if msg.type == "ai" and msg.text:
            content += str(msg.text)
    return content


class FrontierAgentState(DeepAgentState):
    """Mutable graph state; identity fields remain as a compatibility bridge for tools."""

    user_id: str
    group_id: int | None
    image_inputs: list[bytes]
    video_inputs: list[bytes]


def _agent_thread_id(user_id: str, group_id: int | None) -> uuid.UUID:
    scope = f"group:{group_id}:user:{user_id}" if group_id is not None else f"dm:{user_id}"
    return uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=scope)


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _build_agent_backend(working_dir: str, workspace_key: str) -> CompositeBackend:
    workspace_dir = _ensure_dir(os.path.join(working_dir, "workspaces", workspace_key))
    skills_dir = str(PROJECT_ROOT / "skills")
    memory_dir = _ensure_dir(os.path.join(working_dir, "memory", workspace_key))
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


def _load_base_system_prompt(group_id: int | None, wake_word: str | None) -> str:
    toml_prompt = EnvConfig.SYSTEM_PROMPT.strip()
    if not toml_prompt:
        logger.error("❌ env.toml 中未配置 bot.system_prompt")
        return f"You are {EnvConfig.BOT_NAME}, a helpful assistant. [配置错误: system prompt未配置]"

    name = EnvConfig.BOT_NAME
    if wake_word:
        name = wake_word
    elif group_id is not None:
        try:
            from utils.database import GroupSettingsManager, get_engine

            words = GroupSettingsManager(get_engine()).get(group_id, "wake_word")
            if words:
                name = words[0]
        except Exception as exc:
            logger.debug("Wake word injection skipped: %s: %s", type(exc).__name__, exc)

    try:
        return toml_prompt.format(name=name)
    except KeyError as exc:
        logger.error("❌ system prompt 模板变量缺失: %s", exc)
        return f"You are {name}, a helpful assistant. [配置错误: 模板变量缺失]"


def _load_prompt_fragment(filename: str, description: str) -> str:
    try:
        return (PROJECT_ROOT / "prompts" / filename).read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("读取%s失败: %s", description, exc)
        return ""


class FrontierCognitive:
    def __init__(self):
        self.tools = agent_tools.main_tools
        self.memory_subagent = build_memory_subagent(agent_tools.subagent_tools["memory"])
        self.earth_data_subagent = build_earth_data_subagent(agent_tools.earth_query_tools)

    @staticmethod
    def load_system_prompt(
        group_id: int | None = None,
        wake_word: str | None = None,
        workspace_key: str | None = None,
    ):
        """组合基础人设、全局操作规范和渲染规范，注入当前触发的名称。

        {name}: 优先使用当前触发的唤醒词，其次群自定义，最后 fallback BOT_NAME。
        """
        prompt = _load_base_system_prompt(group_id, wake_word)
        prompt_fragments = (
            ("AGENTS.md", "Agent 操作规范"),
            ("rendering.md", "Markdown 渲染规范"),
        )
        for filename, description in prompt_fragments:
            if fragment := _load_prompt_fragment(filename, description):
                prompt += f"\n\n{fragment}"
        if workspace_key is not None:
            prompt += (
                "\n\n【当前 Workspace SOUL】"
                f"动态人设文件路径为 `/memory/{workspace_key}/SOUL.md`。"
                "需要持久化稳定人设或长期偏好时，只更新该文件。"
            )
        return prompt

    @staticmethod
    async def extract_uni_messages(response):
        """直接从响应中提取 UniMessage 对象"""
        if not response or not isinstance(response, dict):
            logger.warning("⚠️ extract_uni_messages: response 为空或不是字典类型")
            return []

        uni_messages = []
        for message in response.get("messages", []):
            if getattr(message, "type", None) == "tool" and getattr(message, "artifact", None) is not None:
                tool_name = getattr(message, "name", "unknown")
                uni_messages.append(message.artifact)
                logger.info(f"📤 提取 UniMessage: {tool_name} - 类型: {type(message.artifact)}")

        logger.info(f"📨 总共提取到 {len(uni_messages)} 个 UniMessage")
        return uni_messages

    async def chat_agent(
        self,
        messages,
        user_id,
        user_name,
        capability: str = "none",
        group_id: int | None = None,
        image_inputs: list[bytes] | None = None,
        video_inputs: list[bytes] | None = None,
        thread_id_override: uuid.UUID | str | None = None,
        wake_word: str | None = None,
        group_member_role: str | None = None,
        progress_reporter: ProgressReporter | None = None,
        user_text: str | None = None,
    ):
        uses_responses_api = provider_uses_responses_api(
            EnvConfig.ADVAN_MODEL,
            EnvConfig.ADVAN_MODEL_PROVIDER,
        )
        model_kwargs: dict = {
            "model": EnvConfig.ADVAN_MODEL,
            "streaming": False,
            "max_retries": 2,
            "timeout": EnvConfig.AGENT_LLM_TIMEOUT_SECONDS,
            "provider": EnvConfig.ADVAN_MODEL_PROVIDER,
        }
        if uses_responses_api:
            model_kwargs["reasoning_effort"] = capability
            model_kwargs["verbosity"] = "low"
        model = create_llm(**model_kwargs)
        messages = _filter_messages_for_model_capabilities(
            messages,
            EnvConfig.ADVAN_MODEL,
            role="advanced",
        )
        working_dir = getattr(self, "working_dir", os.path.join(os.getcwd(), "cache", "sandbox"))
        thread_id = thread_id_override or _agent_thread_id(user_id, group_id)
        if not isinstance(thread_id, uuid.UUID):
            thread_id = uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=str(thread_id))
        workspace_key = str(group_id) if group_id is not None else str(user_id)
        backend = _build_agent_backend(working_dir, workspace_key)
        workspace_dir = os.path.join(working_dir, "workspaces", workspace_key)
        system_prompt = self.load_system_prompt(group_id, wake_word, workspace_key)
        # ── 硬门控：仅当用户明确请求截图/录屏时才暴露对应工具 ──
        effective_tools = list(self.tools)
        allowed_capture_tools = await _detect_browser_capture_intent(user_text)
        if allowed_capture_tools:
            for rt in agent_tools.restricted_tools:
                if rt.name in allowed_capture_tools:
                    effective_tools.append(rt)
                    logger.info(f"用户明确请求浏览器捕获工具，已暴露: {rt.name}")
        else:
            logger.debug("用户未请求截图/录屏，restricted 工具未暴露")
        # ENS 工具始终可用（具体调用场景由 system prompt 规则控制）
        for rt in agent_tools.restricted_tools:
            if rt.name in ("ens_normal", "ens_professional"):
                effective_tools.append(rt)
        # ── 提取 PTC 工具名列表 ──
        ptc_tool_names: list = [tool.name for tool in effective_tools] if effective_tools else []
        memory_subagent = getattr(self, "memory_subagent", None) or build_memory_subagent(
            agent_tools.subagent_tools["memory"]
        )
        earth_data_subagent = getattr(self, "earth_data_subagent", None) or build_earth_data_subagent(
            agent_tools.earth_query_tools
        )
        middleware: list = []
        middleware.extend(
            [
                PIIMiddleware(
                    "api_key",
                    detector=r"sk-[a-zA-Z0-9]{32}",
                    strategy="mask",
                ),
                ToolRetryMiddleware(),
                ModelRetryMiddleware(),
                FilesystemFileSearchMiddleware(root_path=workspace_dir),
                CodeInterpreterMiddleware(ptc=ptc_tool_names),
            ]
        )
        agent = create_deep_agent(
            name=EnvConfig.BOT_NAME,
            model=model,
            system_prompt=system_prompt,
            tools=effective_tools,
            subagents=[memory_subagent, earth_data_subagent],
            middleware=middleware,
            skills=[SKILLS_BACKEND_PATH],
            memory=[f"/memory/{workspace_key}/SOUL.md"],
            permissions=[
                FilesystemPermission(
                    operations=["write"],
                    paths=[f"{SKILLS_BACKEND_PATH}", f"{SKILLS_BACKEND_PATH}/**"],
                    mode="deny",
                )
            ],
            backend=backend,
            state_schema=FrontierAgentState,
            context_schema=FrontierRuntimeContext,
            debug=EnvConfig.AGENT_DEBUG_MODE,
        )
        start_time = time.time()
        logger.info(f"Agent烧烤中~🍖 思考等级: {capability} 用户: {user_name} (ID: {user_id})")
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
                "group_id": group_id,
                "group_member_role": group_member_role,
                "workspace_dir": workspace_dir,
            }
        }
        runtime_context = FrontierRuntimeContext(
            user_id=str(user_id),
            group_id=group_id,
            group_member_role=group_member_role,
            workspace_dir=workspace_dir,
        )
        try:
            input_data: Any = {
                "messages": messages,
                "user_id": user_id,
                "group_id": group_id,
                "image_inputs": image_inputs or [],
                "video_inputs": video_inputs or [],
            }
            stream = await agent.astream_events(
                input_data,
                config=config,
                context=runtime_context,
                version="v3",
            )
            progress_task = asyncio.create_task(_collect_progress(stream, progress_reporter))
            try:
                response = await stream.output()
            finally:
                await _finish_progress_collection(progress_task)
        except Exception as e:
            # 其他意外错误，记录详细信息
            logger.error(f"❌ Agent执行出现意外错误 用户{user_id}: {type(e).__name__}")
            logger.exception("完整错误堆栈:")
            await _emit_progress(
                progress_reporter,
                ProgressEvent(type="done", message="Agent 执行失败", detail={"success": False}),
            )
            return {
                "response": {"messages": [AIMessage("💥 服务暂时不可用，请稍后重试。")]},
                "total_time": time.time() - start_time,
                "uni_messages": [],
                "error": str(e),
            }

        uni_messages = await FrontierCognitive.extract_uni_messages(response)
        ai_messages = [msg for msg in response.get("messages", []) if getattr(msg, "type", None) == "ai"]
        final_response = ai_messages[-1] if ai_messages else AIMessage("智能代理处理完成，但没有生成响应。")

        processing_time = time.time() - start_time
        logger.info(f"Agent烤熟了~🥓 (耗时: {processing_time:.2f}s)")
        await _emit_progress(
            progress_reporter,
            ProgressEvent(type="done", message="Agent 已完成", detail={"success": True}),
        )

        return {
            "response": {"messages": [final_response]},
            "total_time": processing_time,
            "uni_messages": uni_messages,
        }


_agent_locks: dict[str, asyncio.Lock] = {}


async def run_serialized(thread_id: str, coro, *, timeout: float | None = None):
    """同一 conversation 内序列化 Agent 执行：同 key 互斥，不同 key 并发。"""
    key = str(thread_id)
    lock = _agent_locks.setdefault(key, asyncio.Lock())
    async with lock:
        if timeout is not None:
            return await asyncio.wait_for(coro, timeout=timeout)
        return await coro
