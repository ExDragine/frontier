"""Validate, deduplicate, render, and deliver Wolfx CENC reports."""

import asyncio
import datetime
import json
import traceback
import zoneinfo
from dataclasses import dataclass

from nonebot import logger
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from utils.alconna import Target, UniMessage
from utils.configs import EnvConfig
from utils.database import EventDatabase
from utils.markdown_render import playwright_render

CENC_EVENT_NAME = "eq_cenc"
CENC_MINIMUM_MAGNITUDE = 3.0
CENC_SNAPSHOT_MAX_AGE = datetime.timedelta(minutes=10)
CENC_SNAPSHOT_MAX_FUTURE = datetime.timedelta(minutes=5)
CENC_TIMEZONE = zoneinfo.ZoneInfo("Asia/Shanghai")

event_database = EventDatabase()
_cenc_event_lock = asyncio.Lock()


class CencEewPayload(BaseModel):
    """Validated Wolfx CENC EEW payload."""

    model_config = ConfigDict(populate_by_name=True)

    report_id: str = Field(alias="ID")
    event_id: str = Field(alias="EventID")
    report_time: str = Field(alias="ReportTime")
    report_num: int = Field(alias="ReportNum")
    origin_time: str = Field(alias="OriginTime")
    hypocenter: str = Field(alias="HypoCenter")
    latitude: float = Field(alias="Latitude")
    longitude: float = Field(alias="Longitude")
    magnitude: float = Field(alias="Magnitude")
    depth: float | None = Field(default=None, alias="Depth")
    max_intensity: float | str | None = Field(default=None, alias="MaxIntensity")


@dataclass(frozen=True)
class CencEventResult:
    groups_sent: list[int]
    messages_sent: int
    output_summary: str


def _parse_report_time(value: str) -> datetime.datetime | None:
    cleaned = value.strip()
    candidates = [cleaned, cleaned.replace("/", "-")]
    for candidate in candidates:
        try:
            parsed = datetime.datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=CENC_TIMEZONE)
        return parsed.astimezone(CENC_TIMEZONE)
    return None


def _is_fresh_snapshot(payload: CencEewPayload, now_cn: datetime.datetime | None = None) -> bool:
    report_time = _parse_report_time(payload.report_time)
    if report_time is None:
        return False
    current = now_cn or datetime.datetime.now(CENC_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=CENC_TIMEZONE)
    else:
        current = current.astimezone(CENC_TIMEZONE)
    age = current - report_time
    return -CENC_SNAPSHOT_MAX_FUTURE <= age <= CENC_SNAPSHOT_MAX_AGE


def _load_event_ids(stored_value: str | None) -> list[str]:
    if not stored_value:
        return []
    try:
        parsed = json.loads(stored_value)
    except json.JSONDecodeError:
        # 兼容旧 HTTP 轮询实现保存的单个 report ID。
        return [stored_value]
    if not isinstance(parsed, list):
        return [stored_value]
    return list(dict.fromkeys(str(event_id) for event_id in parsed if str(event_id)))


async def _store_event_id(event_id: str, stored_value: str | None, processed_event_ids: list[str]) -> None:
    serialized = json.dumps([*processed_event_ids, event_id], ensure_ascii=False)
    if stored_value is None:
        await event_database.insert(CENC_EVENT_NAME, serialized)
    else:
        await event_database.update(CENC_EVENT_NAME, serialized)


async def process_cenc_event(
    data: dict,
    *,
    is_snapshot: bool = False,
    now_cn: datetime.datetime | None = None,
) -> CencEventResult:
    """Process one CENC report without coupling it to the scheduler plugin."""
    try:
        payload = CencEewPayload.model_validate(data)
    except ValidationError as exc:
        logger.warning("忽略字段无效的 CENC 地震预警: %s", exc)
        return CencEventResult([], 0, "cenc ignored: invalid payload")

    async with _cenc_event_lock:
        stored_value = await event_database.select(CENC_EVENT_NAME)
        processed_event_ids = _load_event_ids(stored_value)
        if payload.event_id in processed_event_ids:
            logger.debug(
                "CENC 地震已推送过 (event_id=%s, report_num=%s)，跳过",
                payload.event_id,
                payload.report_num,
            )
            return CencEventResult([], 0, "cenc ignored: duplicate event")

        if payload.magnitude < CENC_MINIMUM_MAGNITUDE:
            logger.debug(
                "CENC 地震震级 %.1f 低于 %.1f，等待后续修订",
                payload.magnitude,
                CENC_MINIMUM_MAGNITUDE,
            )
            return CencEventResult([], 0, "cenc ignored: below threshold")

        if is_snapshot and not _is_fresh_snapshot(payload, now_cn):
            await _store_event_id(payload.event_id, stored_value, processed_event_ids)
            logger.info("CENC 快照已过期，仅建立去重基线 (event_id=%s)", payload.event_id)
            return CencEventResult([], 0, "cenc snapshot baseline stored")

        # 先持久化 EventID，确保同一次地震的后续报次不会重复推送。
        await _store_event_id(payload.event_id, stored_value, processed_event_ids)
        logger.info(
            "检测到%s发生%.1f级地震 (event_id=%s, report_num=%s)",
            payload.hypocenter,
            payload.magnitude,
            payload.event_id,
            payload.report_num,
        )

        detail = [
            {"label": "⏱️发震时间", "value": payload.origin_time},
            {"label": "🗺️震中位置", "value": payload.hypocenter},
            {"label": "🌐纬度", "value": payload.latitude},
            {"label": "🌐经度", "value": payload.longitude},
        ]
        if payload.max_intensity is not None:
            detail.append({"label": "💢最大烈度", "value": str(payload.max_intensity)})

        image = await playwright_render(
            CENC_EVENT_NAME,
            {
                "title": "CENC地震速报",
                "detail": detail,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "magnitude": payload.magnitude,
                "depth": payload.depth,
            },
        )
        if not image:
            return CencEventResult([], 0, "cenc render returned no image")

        message = UniMessage().image(raw=image)
        groups_sent: list[int] = []
        for group in EnvConfig.EARTHQUAKE_GROUP_ID:
            try:
                await message.send(target=Target.group(str(group)))
                groups_sent.append(int(group))
            except Exception as exc:
                error_traceback = "".join(traceback.format_exception(exc))
                logger.error("CENC 地震预警推送到群 %s 失败:\n%s", group, error_traceback)

        return CencEventResult(
            groups_sent=groups_sent,
            messages_sent=len(groups_sent),
            output_summary=f"cenc sent {len(groups_sent)} group(s)",
        )
