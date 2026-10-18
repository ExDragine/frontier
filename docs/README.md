# 文档索引

本页是 Frontier 全部项目文档的导航入口。项目入口和快速开始见 [README](../README.md)；配置字段以 `env.toml.example` 和 `utils/configs.py` 为准，行为以代码和测试为准。新增 `docs/*.md` 时请同时在此登记。

## 入门

| 文档 | 说明 |
| --- | --- |
| [README](../README.md) | 项目入口：简介、能力概览、架构流程图、技术栈、快速开始、配置概览与文档导航。 |
| [AGENTS.md](../AGENTS.md) | 面向 Agent 与贡献者的项目全景：请求生命周期、模块地图、关键约定、配置要点与测试方式。 |
| [配置参考](configuration.md) | `.env` / `env.toml` / `mcp.json` / `acp.json` 的职责，配置段、供应商 profile、模型路由、访问策略、Dashboard 保存与重载语义。 |
| [CONTRIBUTING](../CONTRIBUTING.md) | 本地开发、提交前检查清单和提交/PR 描述约定。 |
| [SECURITY](../SECURITY.md) | 漏洞私密报告流程，以及分享日志前必须移除的敏感数据。 |
| [CHANGELOG](../CHANGELOG.md) | 未发布变更和按主题记录的历史实现说明。 |

## 架构与运行时

| 文档 | 说明 |
| --- | --- |
| [运行与维护边界](architecture.md) | 当前运行边界：插件组件归属、请求生命周期、结果与错误、初始化、持久化和验证入口。 |
| [Agent 与平台解耦设计](agent-platform-separation.md) | 目标架构、统一领域模型、应用层端口、Conversation Orchestrator、迁移阶段与飞书方案。 |
| [消息、上下文与投递边界](message_flow.md) | 消息归一化、存储、门控与媒体下载顺序，当前请求/历史边界、两级队列锁和投递结果。 |
| [Agent 执行控制](agent-execution-controls.md) | 主图模型/工具调用预算、用量统计口径、工具错误分类和 Decision 结构化输出策略。 |
| [QQ 会话缓存](agent-sessions.md) | 有界 checkpoint 会话缓存的开关、参数、容量与媒体语义、投递结算和观测指标。 |
| [DeepSeek 网页搜索](deepseek-web-search.md) | 独立 Search/Fetch 工具的配置、调用契约、正文预算、工作区落盘、重试与限速。 |
| [Laya 决策 Provider](laya-decision-provider.md) | 可选 Laya 候选预筛的本地 SDK/HTTP 后端、DecisionProvider 契约与门控边界。 |
| [消息媒体网络](message-media-network.md) | 媒体加载的公开地址校验，以及 Clash TUN / Fake-IP 环境下的 DNS 回退规则。 |
| [本地语音识别](local-speech.md) | SenseVoiceSmall Q8 的 Windows 安装、子进程识别行为、消息语义与资源复测。 |
| [模型目录](../models/README.md) | `models/` 模型元数据：模型卡字段、能力与生命周期、LobeHub 名称同步、更新流程。 |
| [渲染器开发说明](../renderer/README.md) | Markdown 渲染器的 React/TypeScript 组件、构建、类型生成与截图验证。 |
| [富文本排版技能](../skills/rich-markdown/SKILL.md) | QQ 回复的 Markdown 与轻量组件语法；详细字段契约位于其 `references/` 目录。 |
| 其他内置技能 | [eli5](../skills/eli5/SKILL.md)（分层通俗解释）、[ens-weather](../skills/ens-weather/SKILL.md)（ENS 气象工作流）、[qq-operation-safety](../skills/qq-operation-safety/SKILL.md)（QQ 平台写操作前检查）。 |

## 平台与集成

| 文档 | 说明 |
| --- | --- |
| [ACP 接入](acp.md) | `acp.json` 客户端配置、`/acp` 命令、子代理桥接、Frontier 内置 v1/v2 stdio server、DSH 接入与安全边界。 |
| [ACP 插件说明](../plugins/acp/README.md) | ACP 插件的文件职责、CLI 启动命令和测试入口。 |
| [ACP v1 接入规范](../plugins/acp/docs/acp-v1.md) | v1 客户端生命周期、媒体能力、权限默认值和 Frontier 作为 Agent 的支持范围。 |
| [ACP v2 Draft 接入规范](../plugins/acp/docs/acp-v2.md) | v2 与 v1 的字段差异、`state_update` 生命周期、会话恢复/回放和草案限制。 |
| [Milky 1.3 适配](milky-1.3.md) | Milky 1.3 协议变更对应的 Frontier 行为与兼容性边界。 |
| [Milky 申请事件](platform-events.md) | 四类申请事件的 `ignore/record/rule/shadow/decision` 模式、`/events` 管理和执行恢复。 |
| [新闻插件运维](news-plugin.md) | 新闻管线的配置、投递语义、恢复与保留策略、运维命令和回滚方式（英文）。 |
| [Dashboard 前端资源](../plugins/dashboard/web/vendor/README.md) | Dashboard 第三方脚本的本地 pinned 副本与 CDN 回退说明。 |
| [周易 64 卦数据](../data/iching/README.md) | 易经占卜静态数据的目录结构、字段格式和使用方式。 |

## 存储与运维

| 文档 | 说明 |
| --- | --- |
| [SQLite 消息搜索维护](database-search.md) | FTS5 external-content 索引的搜索接口、一致性检查与维护脚本用法。 |
| [消息身份与历史迁移退役](database-identity-migration.md) | `Message.id` 与时间的语义、当前数据库结构要求、旧备份恢复和验证命令。 |
| [数据库维护脚本](../scripts/database_maintenance.py) | `diagnose` 检查 FTS/schema，`maintain` 执行 optimize、重建与可选 WAL checkpoint。 |
| [运行资源报告](reports/) | 本地资源复测快照：SenseVoice Q8 的 HTML 报告与 JSON 原始数据，不随代码更新。 |
| [代码健康审计](reports/code-health-audit-2026-10-18.md) | 2026-10-18 的代码健康盘点：可清理的死代码、可维护性热点、兼容层判定、测试缺口与建议处理顺序（一次性快照）。 |

## 历史归档

| 文档 | 说明 |
| --- | --- |
| [归档目录说明](archive/README.md) | 归档用途、维护约定，以及哪些文档不再按当前代码维护。 |
| [Checkpointer 实施计划](archive/checkpointer-plan.md) | 有界 checkpointer 与会话重建的实施计划（已实施、默认关闭）；使用说明已由 [QQ 会话缓存](agent-sessions.md) 取代。 |
| [新闻模块、Exa MCP 与日志检查](archive/news-mcp-review.md) | 2026-09-20 的历史审查记录，保留问题复现证据和修复范围；当前运维语义见 [新闻插件运维](news-plugin.md)。 |

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
