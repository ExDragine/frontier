"""工具名 / 子代理名 → 中文进度消息映射。

工具新增时在此文件添加映射即可，无需修改 agents.py。

查找规则：精确匹配 → 前缀模式 → "正在调用工具：{name}"。
"""

from __future__ import annotations

# ── 精确映射 ──────────────────────────────────────────────────────────────
# 覆盖不符合前缀模式或需要定制文案的工具。
_TOOL_MESSAGE_EXACT: dict[str, str] = {
    # Agent 内置工具
    "search": "正在搜索相关信息…",
    "read_file": "正在读取文件…",
    "write_file": "正在写入文件…",
    "edit_file": "正在编辑文件…",
    "execute": "正在执行代码…",
    "shell": "正在执行 shell 命令…",
    # 记忆
    "summarize_messages": "正在总结聊天记录…",
    "search_messages": "正在搜索历史消息…",
    # 天气 / 地球
    "ens_normal": "🌐 正在查询…",
    "ens_professional": "🌐 正在专业地构建地球可视化数据中…",
    "mars_weather": "正在获取火星天气…",
    "get_wind_map": "正在获取风向图…",
    "get_static_china_radar": "正在获取雷达图…",
    "get_china_earthquake": "正在查询中国地震信息…",
    "get_japan_earthquake": "正在查询日本地震信息…",
    # 空间 / 天文
    "solar_flare": "正在查询太阳耀斑…",
    "realtime_solarwind": "正在获取实时太阳风数据…",
    "soho_realtime_solarwind": "正在获取 SOHO 太阳风数据…",
    "noaa_enlil_predict": "正在获取 ENLIL 预测…",
    "solar_image": "正在获取太阳图像…",
    "goes_suvi": "正在获取 GOES 太阳图像…",
    "sunspot": "正在查询太阳黑子…",
    "swpc_page": "正在获取空间天气预报…",
    "planets_weather": "正在查询行星天气…",
    "geospace": "正在获取地球空间环境…",
    "comet_information": "正在查询彗星信息…",
    "comet_list": "正在获取彗星列表…",
    "aurora_live": "正在获取极光直播…",
    "station_location": "正在查询空间站位置…",
    "get_launches": "正在查询火箭发射…",
    # 占卜
    "iching_divination": "正在易经占卜…",
    "list_iching_hexagrams": "正在查询卦象列表…",
    "get_hexagram_detail": "正在查看卦象详情…",
    "tarot_reading": "正在塔罗占卜…",
    "list_tarot_spreads": "正在查询牌阵…",
    # 媒体生成
    "get_paint": "正在生成绘图…",
    "get_video": "正在处理视频…",
    # API
    "get_deepseek_api_balance": "正在查询 API 余额…",
    # 台风
    "get_typhoon_info": "🌀 正在查询台风信息…",
    # 浏览器捕获
    "webpage_screenshot": "正在截取网页截图…",
    "webpage_recording": "正在录制网页视频…",
    # NRC / 洛克王国
    "get_nrc_merchant_current": "🛒正在打开远行商人货架…",
    "get_nrc_eggs_details": "🥚正在感受精灵蛋…",
    "get_nrc_eggs_groups": "📚正在查询精灵蛋组手册…",
    "get_nrc_event_calendar": "🚪正在踹开魔方大门…",
}

# ── 前缀模式 ──────────────────────────────────────────────────────────────
# 按优先级排列，命中第一个后停止。
_TOOL_MESSAGE_PATTERNS: list[tuple[str, str]] = [
    # ── 适配器发送类 ──
    ("send_image", "正在发送图片…"),
    ("send_audio", "正在发送音频…"),
    ("send_voice", "正在发送语音…"),
    ("send_video", "正在发送视频…"),
    ("send_emoji", "正在发送表情…"),
    ("send_file", "正在发送文件…"),
    ("send_at_all", "正在 @全体成员…"),
    ("send_at", "正在 @成员…"),
    ("send_text_with_at", "正在发送 @消息…"),
    ("send_private_message", "正在发送私聊消息…"),
    ("send_group_message", "正在发送群聊消息…"),
    ("send_friend_nudge", "正在戳一戳好友…"),
    ("send_profile_like", "正在点赞…"),
    ("send_group_nudge", "正在戳一戳群聊…"),
    ("send_group_message_reaction", "正在发送表情回应…"),
    ("send_group_announcement", "正在发布群公告…"),
    # ── 获取类 ──
    ("get_private_file_download_url", "正在获取文件下载链接…"),
    ("get_group_file_download_url", "正在获取文件下载链接…"),
    ("get_group_files", "正在获取群文件列表…"),
    ("get_friend_requests", "正在获取好友申请…"),
    ("get_group_announcements", "正在获取群公告…"),
    ("get_group_essence_messages", "正在获取精华消息…"),
    ("get_group_notifications", "正在获取群通知…"),
    ("get_history_messages", "正在获取历史消息…"),
    ("get_resource_temp_url", "正在获取资源链接…"),
    ("get_forwarded_messages", "正在获取合并转发消息…"),
    ("get_message", "正在获取消息…"),
    # ── 卫星图 (必须在通用 get_ 之前) ──
    ("get_fy4b_geos_cloud_map", "正在获取 FY-4B 卫星云图…"),
    ("get_fy4b_cloud_map", "正在获取 FY-4B 云图…"),
    ("get_himawari_satellite_image", "正在获取 Himawari 卫星图…"),
    # ── 通用 get_ / set_ / download_ / upload_ ──
    ("get_custom_face_url_list", "正在获取表情列表…"),
    ("get_friend_list", "正在获取好友列表…"),
    ("get_friend_info", "正在获取好友信息…"),
    ("get_group_list", "正在获取群列表…"),
    ("get_group_info", "正在获取群信息…"),
    ("get_group_member_list", "正在获取群成员列表…"),
    ("get_group_member_info", "正在获取群成员信息…"),
    ("get_peer_pins", "正在获取置顶列表…"),
    ("get_login_info", "正在获取登录信息…"),
    ("get_impl_info", "正在获取实现信息…"),
    ("get_user_profile", "正在获取用户资料…"),
    ("get_cookies", "正在获取 Cookies…"),
    ("get_csrf_token", "正在获取 CSRF Token…"),
    # ── 上传 ──
    ("upload_private_file", "正在上传私聊文件…"),
    ("upload_group_file", "正在上传群文件…"),
    # ── 删除 / 撤回 ──
    ("delete_friend", "正在删除好友…"),
    ("delete_group_file", "正在删除群文件…"),
    ("delete_group_folder", "正在删除群文件夹…"),
    ("delete_group_announcement", "正在删除群公告…"),
    ("recall_private_message", "正在撤回私聊消息…"),
    ("recall_group_message", "正在撤回群消息…"),
    # ── 创建 ──
    ("create_reminder", "正在创建提醒…"),
    ("create_scheduled_task", "正在创建定时任务…"),
    ("create_group_folder", "正在创建群文件夹…"),
    # ── 设置类 ──
    ("set_group_name", "正在修改群名称…"),
    ("set_group_avatar", "正在设置群头像…"),
    ("set_group_member_card", "正在设置群名片…"),
    ("set_group_member_special_title", "正在设置群头衔…"),
    ("set_group_member_admin", "正在设置管理员…"),
    ("set_group_member_mute", "正在设置禁言…"),
    ("set_group_whole_mute", "正在设置全员禁言…"),
    ("set_group_essence_message", "正在设置精华消息…"),
    ("set_avatar", "正在设置头像…"),
    ("set_nickname", "正在设置昵称…"),
    ("set_bio", "正在设置简介…"),
    ("set_peer_pin", "正在设置置顶…"),
    # ── 其他动作 ──
    ("kick_group_member", "正在踢出群成员…"),
    ("quit_group", "正在退出群聊…"),
    ("move_group_file", "正在移动群文件…"),
    ("rename_group_file", "正在重命名群文件…"),
    ("rename_group_folder", "正在重命名群文件夹…"),
    ("mark_message_as_read", "正在标记已读…"),
    ("accept_friend_request", "正在处理好友申请…"),
    ("reject_friend_request", "正在处理好友申请…"),
    ("accept_group_request", "正在处理加群申请…"),
    ("reject_group_request", "正在处理加群申请…"),
    ("accept_group_invitation", "正在处理群邀请…"),
    ("reject_group_invitation", "正在处理群邀请…"),
    # ── 定时任务管理 ──
    ("list_my_scheduled_tasks", "正在查询定时任务…"),
    ("cancel_my_scheduled_task", "正在取消定时任务…"),
    ("pause_my_scheduled_task", "正在暂停定时任务…"),
    ("resume_my_scheduled_task", "正在恢复定时任务…"),
    # ── MCP: Playwright 浏览器自动化 ──
    ("browser_navigate_back", "正在返回上一页…"),
    ("browser_console_messages", "正在获取控制台日志…"),
    ("browser_handle_dialog", "正在处理浏览器对话框…"),
    ("browser_evaluate", "正在执行页面脚本…"),
    ("browser_file_upload", "正在上传文件…"),
    ("browser_drop", "正在拖放文件…"),
    ("browser_fill_form", "正在填写表单…"),
    ("browser_press_key", "正在按下键盘…"),
    ("browser_type", "正在输入文本…"),
    ("browser_network_requests", "正在查看网络请求…"),
    ("browser_network_request", "正在查看请求详情…"),
    ("browser_run_code_unsafe", "正在执行 Playwright 代码…"),
    ("browser_take_screenshot", "正在截取页面截图…"),
    ("browser_snapshot", "正在捕获页面快照…"),
    ("browser_wait_for", "正在等待页面加载…"),
    ("browser_tabs", "正在管理浏览器标签页…"),
    ("browser_close", "正在关闭浏览器…"),
    ("browser_resize", "正在调整窗口大小…"),
    ("browser_click", "正在点击页面元素…"),
    ("browser_drag", "正在拖拽元素…"),
    ("browser_hover", "正在悬停元素…"),
    ("browser_select_option", "正在选择下拉选项…"),
    ("browser_navigate", "正在导航到新页面…"),
    # ── MCP: 时间 ──
    ("get_current_time", "正在获取当前时间…"),
    ("convert_time", "正在转换时区…"),
    # ── MCP: 高德地图 ──
    ("maps_regeocode", "正在逆地理编码…"),
    ("maps_geo", "正在地理编码…"),
    ("maps_ip_location", "正在 IP 定位…"),
    ("maps_search_detail", "正在查询地点详情…"),
    ("maps_bicycling", "正在规划骑行路线…"),
    ("maps_direction_walking", "正在规划步行路线…"),
    ("maps_direction_driving", "正在规划驾车路线…"),
    ("maps_direction_transit_integrated", "正在规划公交路线…"),
    ("maps_distance", "正在计算距离…"),
    ("maps_text_search", "正在搜索地点…"),
    ("maps_around_search", "正在搜索周边…"),
    ("maps_weather", "正在查询天气…"),
    # ── MCP: 中国节日 ──
    ("holiday_info", "正在查询节日信息…"),
    ("current_year_holidays", "正在查询今年节假日…"),
    ("current_year_work_days", "正在查询工作日…"),
    ("next_holiday", "正在查询下一个节日…"),
    ("gregorian_to_lunar", "正在转换农历…"),
    ("lunar_to_gregorian", "正在转换公历…"),
    ("get_lunar_string", "正在查询农历信息…"),
    ("get_24_lunar_feast", "正在查询二十四节气…"),
    ("get_8zi", "正在排八字…"),
    ("get_weekday", "正在查询星期…"),
    # ── MCP: Exa 搜索 ──
    ("web_search_exa", "正在搜索网络信息…"),
    ("web_fetch_exa", "正在获取网页内容…"),
]

# ── 子代理消息映射 ─────────────────────────────────────────────────────────
_SUBAGENT_MESSAGE_MAP: dict[str, str] = {
    "code-explorer": "启动代码探索子代理…",
    "code-reviewer": "启动代码审查子代理…",
    "feature-dev": "启动功能开发子代理…",
}


def tool_message(tool_name: str) -> str:
    """返回工具名对应的中文进度描述。

    查找顺序：精确映射 → 前缀模式 → 通用回退。
    """
    if msg := _TOOL_MESSAGE_EXACT.get(tool_name):
        return msg
    for prefix, msg in _TOOL_MESSAGE_PATTERNS:
        if tool_name.startswith(prefix):
            return msg
    return f"正在调用工具：{tool_name}"


def subagent_message(subagent_name: str) -> str:
    """返回子代理名对应的中文进度描述，未匹配时返回通用模板。"""
    return _SUBAGENT_MESSAGE_MAP.get(subagent_name, f"{subagent_name} 已启动")
