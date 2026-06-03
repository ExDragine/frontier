# Rubric + CodeInterpreter 中间件配置设计

**日期：** 2026-06-03
**状态：** 已批准

## 概述

为 Frontier bot 的 `chat_agent` 配置 deepagents 的 `RubricMiddleware`（输出自我评分和迭代优化）和 `CodeInterpreterMiddleware`（代码执行器），提升 agent 回复质量和工具编排能力。

## 动机

- `RubricMiddleware` 和 `CodeInterpreterMiddleware` 已添加到 middleware 列表，但均为最小化配置
- `RubricMiddleware` 需要调用方在 invocation state 中传入 `rubric` 字段才会激活
- `CodeInterpreterMiddleware` 没有 PTC 配置，interpreter 中无法调用 agent 工具

## 设计

### 1. Rubric 评分标准（三类）

三个 rubric 文件在 `prompts/` 下，加载时合并为单一 rubric 文本注入 invoke state：

**`prompts/rubric_chat_quality.md`** — 对话质量（A）
- 回复自然、不做作，不像客服或百科
- 简单寒暄用短回复，不展开解释
- 不自我总结、不收尾、不说"有什么需要帮你的吗"
- 遇到蠢事可以有分寸地吐槽，但不记仇
- 不主动承认自己是 AI，不讨论"作为AI"的话题

**`prompts/rubric_technical.md`** — 技术正确性（B）
- 代码示例语法正确、可运行
- 数据查询结果准确，有来源时标注来源
- 数学/计算类回复逻辑正确

**`prompts/rubric_compliance.md`** — 通用规范（C）
- 群聊不滥用 markdown 标题和 bullet list
- 不输出 `_NO_REPLY_` 以外的静默标记
- 不使用 JSON 或代码块包裹正常回复
- 不包含敏感信息（API key、个人隐私等）

### 2. CodeInterpreter PTC

`CodeInterpreterMiddleware(ptc=<all_tool_names>)` — 允许 interpreter 代码调用所有 agent 工具。工具名从 `self.tools` 动态提取。

### 3. 数据流

```
chat_agent() prepare:
  1. 加载 rubric_chat_quality.md + rubric_technical.md + rubric_compliance.md
  2. 合并为单一 rubric 文本
  3. 从 self.tools 提取工具名列表

agent.ainvoke():
  input: {
    "messages": ...,
    "user_id": ...,
    "rubric": <合并后的 rubric 文本>,  ← 新增
  }

after_agent (RubricMiddleware):
  grader 子 agent 读取 rubric → 逐条评分 →
    satisfied → 正常返回
    needs_revision → 注入反馈，agent 重新运行（最多3轮）
    其他 → 记录 warning，返回当前结果
```

### 4. 文件变更

| 文件 | 操作 |
|------|------|
| `prompts/rubric_chat_quality.md` | 新建 |
| `prompts/rubric_technical.md` | 新建 |
| `prompts/rubric_compliance.md` | 新建 |
| `utils/agents.py` | 修改：rubric 加载 + PTC 配置 + invoke state 注入 |

### 5. 关键设计决策

- **Rubric 只在 `chat_agent` 触发**：`assistant_agent`（工具类调用、后台任务）不触发 rubric，避免不必要的延迟和成本
- **全量工具 PTC**：允许 interpreter 调用所有 agent 工具，最大化解释器中代码的编排能力
- **rubric 文件化**：方便非开发人员调整评分标准，不需要改 Python 代码
- **合并加载**：三个文件合并为一个 rubric 文本，grader 一次性评估所有维度
