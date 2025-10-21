import json
from datetime import datetime

from langchain.tools import tool
from langchain_community.document_loaders import BiliBiliLoader


@tool(response_format="content")
async def get_bilibili_video_info(url: str):
    """
    获取B站视频信息
    从B站视频链接中提取视频的详细信息，包括标题、链接、封面、简介、分区、发布时间、时长、UP主信息等。

    Args:
    url: 网页URL

    Returns:
        提取的信息
    """
    # 创建BiliBiliLoader实例，传入视频链接
    loader = BiliBiliLoader([url])
    docs = loader.load()

    meta = docs[0].metadata
    info = extract_info(meta)
    return json.dumps(info, indent=4, ensure_ascii=False)


# 整理有用信息
def extract_info(meta):
    pubdate = meta.get("pubdate")
    pubdate_str = datetime.fromtimestamp(pubdate).strftime("%Y-%m-%d %H:%M:%S") if pubdate else ""
    info = {
        "标题": meta.get("title"),
        "视频链接": meta.get("url"),
        "封面图片": meta.get("pic"),
        "简介": meta.get("desc"),
        "分区": f"{meta.get('tname', '')}（{meta.get('tname_v2', '')}）",
        "发布时间": f"{pubdate_str}（时间戳：{pubdate}）",
        "时长": f"{meta.get('duration', 0)} 秒",
        "UP主": f"{meta.get('owner', {}).get('name', '')}（mid: {meta.get('owner', {}).get('mid', '')}）",
        "UP主头像": meta.get("owner", {}).get("face", ""),
        "播放量": meta.get("stat", {}).get("view", 0),
        "点赞数": meta.get("stat", {}).get("like", 0),
        "投币数": meta.get("stat", {}).get("coin", 0),
        "收藏数": meta.get("stat", {}).get("favorite", 0),
        "评论数": meta.get("stat", {}).get("reply", 0),
        "分享数": meta.get("stat", {}).get("share", 0),
        "视频分辨率": f"{meta.get('dimension', {}).get('width', 0)}x{meta.get('dimension', {}).get('height', 0)}",
        "视频页数": len(meta.get("pages", [])),
        "分P信息": [p.get("part", "") for p in meta.get("pages", [])],
    }
    return info
