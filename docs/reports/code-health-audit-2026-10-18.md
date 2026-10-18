# Frontier 代码健康审计（2026-10-18）

状态：一次性审计快照，不随代码自动更新。审计基线为删除注释、重整文档后的工作区（HEAD = `ba9be00`），只读分析，未修改任何代码。

## 结论摘要

- **没有大面积死代码**：338 个跟踪 `.py` 中不存在整片无引用的产品模块；`ruff` 的未使用导入/变量规则本身为零告警，也没有 `TODO/FIXME`、裸 `except`、长期 skip 的测试。
- **可清理项集中在重构遗留**：2 个无加载者的提示词文件、1 个仅测试引用的 `chat_context` 模块、1 个无调用者的 `TaskManager.delete_task`、1 个孤儿脚本，以及 `signal/decision` 兼容层的不可达分支。
- **维护难点不是圈复杂度，而是超长装配函数与文件职责混叠**：全仓 38 处 `# noqa: C901`（产品代码 23 处）压住了真实复杂度，`chat_agent`（McCabe 31，324 行，21 参数）与 `handle_common`（McCabe 28，291 行）是最大单点。
- **兼容层多数是活跃依赖而非死代码**：ACP v1/v2、飞书边界参考实现（约 1.2k 行，未挂载）、`signal_*` 旧配置别名、DB 旧记录兼容等均有文档/测试/数据依赖，清理需要独立决策与弃用窗口。
- **测试债很轻**：0 个长期跳过测试、0 个未使用 fixture；问题只有 2 个失效测试桩/断言和 1 组重复 fixture。真正的缺口是 `plugins/clockwork/task_commands.py`（454 行 `/task` 命令零测试）等 4 个模块。

优先级定义：**P0** = 低风险、可直接清理或收益最大；**P1** = 需要小范围测试改动或独立 PR；**P2** = 记录观察、随相关重构处理。

## 一、死代码与冗余

### P0

| 位置 | 项目 | 证据 | 建议 |
| --- | --- | --- | --- |
| `prompts/system_prompt_image.md`（25 行）、`prompts/image_summary.md`（6 行） | 孤儿提示词 | 全仓（py/toml/md/json/skills）零加载引用；`utils/agents/prompts.py` 只加载 `prompts/AGENTS.md` | 删除或移入 `docs/archive/` |
| `plugins/agent/chat_context.py`（57 行） | 重构孤立模块 | 产品代码零 import；仅 `test/integration/plugin_layout_test.py`、`plugin_entry_registration_test.py`、`test/integration/dependency_contracts_test.py`、`test/utils/chat_context_test.py` 引用 | 删除模块并同步测试；如该契约仍需保留则重新接线，勿只留文档 |

### P1

| 位置 | 项目 | 证据 | 建议 |
| --- | --- | --- | --- |
| `plugins/clockwork/task_manager.py:356` | `TaskManager.delete_task`（32 行） | 全仓仅定义处；最后调用者随 `reminder_handler.py` 删除 | 删除方法 |
| `scripts/daily_news_preview.py`（28 行） | 孤儿脚本 | 代码/文档/CI 零引用；预览能力已由 `/news` 与 `docs/news-plugin.md` 覆盖 | 删除或写入运维文档 |
| `utils/signal_llm.py:130-193` | `SignalLLM` + `signal_structured` 兼容层 | `EnvConfig.SIGNAL_*` 在 reload 时恒等于 `DECISION_*`，生产 else 分支不可达；`utils/agents/capture.py:33` 仍走弃用入口，而规范入口 `decision_structured` 无生产调用者 | 先让 `capture.py` 改调 `decision_structured`，再删 `SignalLLM`/旧分支；同步测试与文档 |
| `utils/decision_llm.py`（10 行） | 迁移倒置 shim | docstring 称实现在 `signal_llm`“暂留一个迁移周期”，但本模块只 re-export，`utils/decision/` 反向依赖旧实现 | 把实现迁入 `decision_llm.py`，`signal_llm` 只留薄 re-export |

### P2

| 位置 | 项目 | 证据 | 建议 |
| --- | --- | --- | --- |
| `utils/configs.py:96-100` | `ModelsConfig.signal` property | 全仓（含测试）零读取 | 删除（旧配置改名兼容另有 `_normalize_models` 承担） |
| `utils/llm_factory.py:442` | `provider_signal_extra_body` | 唯一消费者是待清理的 `SignalLLM` | 随上项处理 |
| `utils/http_client.py:10` | `HTTP_BACKEND_NAME` | 仅测试断言的兼容导出 | 标注为兼容标记或随测试移除 |
| `scripts/vendor_dashboard_assets.py:28` | `INDEX_HTML` | 脚本自身不用，仅测试断言路径 | 移入测试或保留 |
| `plugins/acp/server.py:353` | `main()` + `__main__` guard | 文档入口是 `python -m plugins.acp`（`__main__.py`），该入口无 importer | 删除或保留为 alias |
| `utils/agents/assistant.py:81` 等 | `assistant_agent` 的 test-only 参数/分支 | `model_role`/`use_model`/`response_format`/`middleware`/`images` 等仅测试触达；生产只传 2 个位置参或 `tools=None` | 裁剪或标注为预留 API |
| `utils/agents/neutral_core.py:216-287` | 旧 runtime 形状兼容 | 仅 `agent_neutral_core_test.py` 使用 run-only/dict 分支 | 保留或移入测试夹具 |

### 重复实现（低风险合并）

| 位置 | 类型 | 建议 |
| --- | --- | --- |
| `plugins/agent/message_normalizer.py:34` 与 `plugins/agent/reply_context.py:429` | `_forward_marker` 完全重复 | 复用 `message_normalizer` 的实现 |
| `plugins/agent/adapters/feishu.py:126` 与 `adapters/qq.py:315` | `_normalize_role` 完全重复 | 抽共享 helper |
| `utils/paint_service.py:73` 与 `utils/video_service.py:73` | `_build_openai_client` 近似重复（0.95） | 抽公共 provider helper |
| `plugins/agent/adapters/qq.py:270` 与 `feishu.py:62` | `_coerce_datetime` 跨文件近似重复（0.895） | 移入 `utils/timeutil.py` |

## 二、维护困难热点

### P0

| 位置 | 指标 | 问题 |
| --- | --- | --- |
| `utils/agents/cognitive.py:509` `FrontierCognitive.chat_agent` | 324 行，McCabe 31（`# noqa: C901`），21 参数，文件 694 行/39 import | 模型、工具、受限工具、prompt、子代理、7 层 middleware、session 快照、事件流、工件提取、用量收尾全部内联；任何一步调整都改同一个函数 |
| `plugins/agent/handlers.py:590` `handle_common` | 291 行，McCabe 28（`# noqa: C901`），14 处宽泛 `except`，文件 753 行/34 import | 消息主链路 7 个阶段内联，共享 15+ 局部变量；阶段间依赖不可见 |

改进起点（低风险、纯搬移）：`chat_agent` 先用请求对象收拢参数，再抽 `_build_middleware()`/`_settle_session_turn()`；`handle_common` 先把媒体/文件/引用并发采集与媒体持久化两段抽成 helper。

### P1

| 位置 | 指标 | 问题 |
| --- | --- | --- |
| `plugins/agent/reply_context.py:570` `load_message_context` | 229 行，McCabe 19，8 参数，嵌套 4 | 同函数混 DB 查询、Milky 远端拉取、图片缓存、附件持久化、引用格式化，两条来源分支各自分叉 |
| `utils/agents/progress.py:47` `collect_progress` | 149 行，McCabe 28 | 3 个投影消费者全是嵌套闭包，`consume_messages` 内再嵌闭包；异常按 `id(exc)` 聚合 |
| `utils/agent_orchestration.py:141` `handle` | 171 行，McCabe 13，5 处无日志 `except` | 6 个失败分支复制 `TurnOutcome`；Feishu webhook 把 `history_failed/gate_failed` 映射为 503 但不记录 `outcome.error`，该链路故障不可观测 |
| `plugins/clockwork/task_manager.py:18` `TaskManager` | 651 行 / 27 方法 | God class：SQLModel CRUD + APScheduler 调度 + 用户/群配置同步 + 执行历史统计 4 类职责 |
| `plugins/acp/service.py` | 755 行 / 11 类 / 52 函数 | acp.json 解析校验、ACP v1 客户端进度桥、子进程运行时、缓存清理同文件；`_agent_config` 84 行/13 分支 |
| `utils/configs.py:649` `EnvConfig.reload` | 112 行，手写 86 项字段映射 + 10 个动态项；文件 647 行/26 模型/128 字段 | 新增配置字段漏映射无测试兜底，运行期才缺属性 |
| `plugins/clockwork/task_commands.py` | 454 行，首行整文件 `# ruff: noqa: C901`；`handle_task_command` 84 行/20 分支 | pause/resume/cancel/run 四个 handler 相似度 0.98，enable/disable 0.976；命令分派是长 if-elif 链 |
| `utils/message.py` | 399 行 / 19 函数 | 消息段提取、媒体下载、Markdown→图片、内容安全检查、发送投递 5 类职责同模块 |
| `utils/database/search.py:147/223` | 两个搜索入口相似度 0.79，McCabe 14/14（`# noqa`） | FTS→LIKE 回退、过滤条件、排序分页复制两份，新增过滤维度要改两遍 |

### P2

- 重复代码：相似度 ≥0.85 的函数对 50 组（同文件 39 / 跨文件 11），集中在 `tools/milky_group.py`（12 组 @tool 包装）、`plugins/clockwork/task_commands.py`（7 组）、`plugins/dashboard/api/tasks_routes.py`（7 组）、`tools/milky_file.py`（5 组）；`aurora.py:10` 与 `satellite.py:138` 0.966、`tarot.py:14` 与 `_iching_reader.py` 0.963。
- 宽泛 `except Exception` 共 196 处（`handlers.py` 14、`utils/message.py` 12、`task_manager.py` 11、`reply_context.py` 7），其中 25 处无日志；多数是主流程 best-effort 降级设计，仅 Feishu 链路建议补可观测性。
- 分层反向依赖：`utils/agents/cognitive.py:36` 顶层 `from plugins.acp.subagent import build_acp_subagents`（utils → plugins 唯一反向边）；`tools/milky_message.py:187-216` 延迟 import `plugins.agent.*` 并直接 `MessageDatabase()`。
- 测试文件规模：`test/utils/agents_test.py` 1,661 行、`test/plugins/agent_image_memory_test.py` 1,619 行，建议按场景拆分。

## 三、兼容层与配置字段：保留 vs 清理

**明确保留（有文档/测试/数据依赖，不应按死代码删除）**

- ACP v1/v2 双协议：`docs/acp.md`、`plugins/acp/README.md`、两套协议测试与 `frontier_acp.py` 兼容入口。
- 飞书边界参考实现：`plugins/agent/adapters/feishu*.py` + `plugins/agent/feishu*.py` 共约 1.2k 行，未挂载、仅契约测试；`docs/agent-platform-separation.md` 明确声明保留。
- `signal_*` 旧配置别名、`qq_text_canary_enabled`、`test_group_id`、`daily_news` 旧 handler 迁移包装、Dashboard 明文密码迁移兼容、DB 旧记录/旧附件字段。
- 默认关闭但已接线的休眠功能（sessions / Laya / speech recognition）。

**配置死字段（解析 + Dashboard 展示，业务代码零读取）**

| 字段 | 现状 | 建议 |
| --- | --- | --- |
| `[key].github_pat` | 产品零读取，仅解析/Dashboard 脱敏/测试 | 因 `extra="forbid"` 不能直接删；标 deprecated，下个 minor 从 example/docs 移除 |
| `[models].paint_size` | 绘图固定 `size="auto"`，仅 `PAINT_SIZE` 导出被测试断言 | 删除导出，TOML 字段保留并标注 |
| `[notifications].test_group_id` | 零读取，但 CHANGELOG 已声明保留 | 保留；下个大版本再评估 |
| `[features].qq_text_canary_enabled` | 零读取，文档声明仅兼容 | 保留至兼容窗口结束 |
| `[platforms.feishu]` + `FEISHU_*` | 仅未挂载的飞书模块读取 | 随飞书重启/退役决策处理 |
| `image_ttl_days` | 仅作为 `media_ttl_days` 缺省回退 | 保留；`docs/configuration.md:142` 需注明旧默认语义 |

另：`plugins/dashboard/api/status_routes.py:81` 硬编码 `"driver": "fastapi+websockets"`，与实际 `.env` 的 `DRIVER` 无关，建议改读真实 driver 或去掉该字段。

## 四、测试债与测试缺口

**测试缺口（应补但缺失）**

| 模块 | 规模 | 现状 |
| --- | --- | --- |
| `plugins/clockwork/task_commands.py` | 454 行 | `/task` 用户命令零测试（manager/executor 有测试）；P1 |
| `tools/NRCeggs_details.py` | 156 行 | 无测试引用，仅注册；可仿 `domain_tool_contracts_test.py` 用 mock 补契约测试 |
| `tools/NRCevent_calendar.py` | 53 行 | 无测试引用 |
| `tools/webpage_recording.py` | 57 行 | 仅工具名字符串断言，模块未执行；建议参数/回退单测 + Playwright 集成标记 |

**测试债（低风险）**

- `test/stubs/install.py:173-190` 仍为已不存在模块 `tools.agent_tools` 安装桩，且该桩顺带创建的空 `tools` 包被 `conftest.py:127-147` 依赖；应改为 `install_stub("tools", agent_tools=...)` 形式，勿直接删。
- `test/plugins/agent_image_memory_test.py:298` 对不存在的 `schedule_image_summary_write` 做 `raising=False` monkeypatch，347 行附近断言恒真；删除或恢复功能。
- `test/integration/rubric_middleware_test.py` 测的是上游 DeepAgents `RubricMiddleware` 契约，属有意保留的依赖契约测试，**不是** 死代码。
- 重复 fixture：`memory_engine` 同时在 `test/utils/database_test.py:33` 与 `test/utils/message_test.py:168` 定义，可收敛到 `test/utils/conftest.py`。

## 五、文档漂移（已核验）

| 文档 | 现状 | 建议 |
| --- | --- | --- |
| `AGENTS.md:77`、`docs/architecture.md:13/24/37` | 仍把 `plugins/agent/chat_context.py` 描述为活跃组件（实际已是 test-only） | 随模块删除/接线决策同步修正 |
| `AGENTS.md:102` | 称 `signal_llm.py` “仅保留兼容导出”，但实现实际在 `signal_llm`，`decision_llm` 才是薄 shim | 待 signal 兼容层收尾时一并修正 |
| `docs/configuration.md:142` | `image_ttl_days` 现仅作旧默认回退，表述可更精确 | 小幅修文 |
| 运维脚本 | `scripts/` 共 10 个：3 个 CI、6 个文档化手工工具、1 个子进程测试用；仅 `daily_news_preview.py` 完全无引用 | 见 §一 P1 |

## 六、建议处理顺序

1. **零风险清理**（1 个 PR）：删除 2 个孤儿提示词、`daily_news_preview.py`、`TaskManager.delete_task`、test-only 常量；合并 `_forward_marker`/`_normalize_role` 重复实现。
2. **chat_context 决策**（1 个 PR）：确认 `build_chat_context` 契约是否仍需要——需要则重新接线并补调用点，不需要则删模块 + test + 修文档。
3. **signal/decision 兼容层收尾**（1 个 PR）：`capture.py` 改调 `decision_structured`，实现迁到 `decision_llm`，删 `SignalLLM`/不可达分支；同步测试与 `AGENTS.md`。
4. **复杂函数搬移**（2 个独立 PR，纯搬移 + 行为测试）：`chat_agent`（参数对象 + middleware/session 收尾抽取）、`handle_common`（媒体阶段抽取）；随后 `load_message_context`、`iter_progress`。
5. **测试补齐**：`task_commands.py` 命令与权限测试优先，其次 3 个 NRC/录屏工具。
6. **配置弃用窗口**（下个 minor）：`github_pat`、`paint_size`、`image_ttl_days` 文档与 example 标注弃用；同步修 `status_routes.py` 硬编码 driver。

## 七、方法与局限

- 三个独立只读审计并行：死代码（AST 全仓引用索引 + 真实入口可达性 BFS + `git log -S` 溯源）、可维护性（规模/参数/嵌套/McCabe/归一化 AST 重复检测/宽泛异常统计）、遗留与测试（96 个 `EnvConfig` 字段逐一核对读取点、测试 import 图、fixture/模板/静态资源核对）。
- 所有高置信死代码候选均由 Lead 二次 grep/读码核验（如 `chat_context` 产品零 import、`delete_task` 零引用、`signal_structured` 分支可达性、`github_pat` 仅配置/Dashboard 读取）。
- 局限：字符串拼接/getattr 变量名无法完全静态归一；未做运行时覆盖率；`rubric_middleware_test` 等上游契约测试与默认关闭功能按“有意保留”处理；`feishu` 相关行数包含文档声明的参考实现。

附录：审计原始材料位于工作区 `.temp/audit-dead/`、`.temp/audit-complexity/`、`.temp/audit-legacy/`（gitignored，可复跑）。核验命令示例：

```bash
uv run --locked ruff check . --select C901 --config "lint.mccabe.max-complexity=10" --ignore-noqa
git grep -n "build_chat_context\|delete_task\|signal_structured\|github_pat" -- "*.py"
```
