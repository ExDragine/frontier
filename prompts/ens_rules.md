【气象查询规则】
- 用户要查新的气象数据 → 调 ens_normal(no_video=True)，只返文字。
- 用户追问/评价/对比之前查过的数据（含 BAA、珊瑚白化等）→ 先用 get_history_messages 或 search_messages 翻聊天记录，数据已翻成中文在记录里，直接引用评价，禁止重调 ens_normal。记录里找不到才调工具。
- 用户要看视频 → 翻记录找参数 → ens_normal(no_video=False)。
- 多地点用 queries 参数（最多3个），超过3个告知用户精简。
