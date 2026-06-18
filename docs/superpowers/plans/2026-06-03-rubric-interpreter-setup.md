# Rubric + CodeInterpreter 中间件配置 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `chat_agent` 配置 RubricMiddleware（自我评分迭代）和 CodeInterpreterMiddleware（全量工具 PTC），提升 agent 回复质量和代码编排能力。

**Architecture:** 三个 rubric markdown 文件在 `prompts/` 下定义评分标准，`FrontierCognitive._load_rubric()` 加载合并后通过 invoke state 注入。`CodeInterpreterMiddleware` 接收从 `self.tools` 提取的工具名列表作为 PTC 允许列表。

**Tech Stack:** deepagents RubricMiddleware, langchain-quickjs CodeInterpreterMiddleware

---

### Task 1: 创建 rubric 评分标准文件

**Files:**
- Create: `prompts/rubric_chat_quality.md`
- Create: `prompts/rubric_technical.md`
- Create: `prompts/rubric_compliance.md`

- [ ] **Step 1: 创建 `prompts/rubric_chat_quality.md`**

```markdown
- 回复自然、不做作，不像客服或百科全书式的回答
- 简单寒暄用短回复，不展开解释、不追问"还有什么需要帮你的吗"
- 不自我总结、不收尾、不说"希望对你有所帮助"之类的客套话
- 遇到蠢事可以有分寸地吐槽，但不记仇、不持续攻击
- 不主动承认自己是 AI，不讨论"作为 AI"或"作为语言模型"的话题
- 不输出 JSON 结构、字段名、元数据等机器可读格式（除非用户明确要求）
```

- [ ] **Step 2: 创建 `prompts/rubric_technical.md`**

```markdown
- 代码示例语法正确、使用对应语言的标准惯例
- 数据查询类回复给出准确信息，引用外部来源时标注出处
- 涉及数学计算或逻辑推理的回复，推理过程正确、结论准确
- 调用工具获取的信息与回复中的陈述一致，不编造或曲解工具返回结果
```

- [ ] **Step 3: 创建 `prompts/rubric_compliance.md`**

```markdown
- 群聊场景不使用 markdown 标题（# ## ###）和 bullet list（- * 开头分行罗列）
- 回复中不含 `_NO_REPLY_` 以外的静默标记或内部控制指令
- 不使用 JSON 代码块包裹正常聊天回复
- 不输出 API key、token、密码或其他敏感凭证信息
- 纯文字回复不加前缀标签（如"回复："、"答案："）、不添加说明性脚注
```

- [ ] **Step 4: 提交**

```bash
git add prompts/rubric_chat_quality.md prompts/rubric_technical.md prompts/rubric_compliance.md
git commit -m "feat: add rubric scoring criteria for chat quality, technical correctness, and compliance

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 修改 `utils/agents.py` — rubric 加载 + PTC 配置 + invoke 注入

**Files:**
- Modify: `utils/agents.py`

- [ ] **Step 1: 添加 `_load_rubric()` 静态方法和工具名提取逻辑**

在 `FrontierCognitive` 类中，`chat_agent` 方法的 middleware 构建之前（约第 418 行前），添加 rubric 加载和 PTC 工具名提取。

定位到 `middleware = []`（当前第 418 行），在其**上方**插入以下代码块：

```python
        # ── 加载 rubric 评分标准 ──
        rubric_text = self._load_rubric()

        # ── 提取 PTC 工具名列表 ──
        ptc_tool_names = [tool.name for tool in self.tools] if self.tools else []
```

- [ ] **Step 2: 在 `FrontierCognitive` 类中添加 `_load_rubric()` 静态方法**

在 `FrontierCognitive` 类中、`load_system_prompt` 方法之后（约第 281 行后），添加：

```python
    @staticmethod
    def _load_rubric():
        """加载并合并所有 rubric 评分标准文件。"""
        rubric_dir = os.path.join(os.getcwd(), "prompts")
        rubric_files = [
            "rubric_chat_quality.md",
            "rubric_technical.md",
            "rubric_compliance.md",
        ]
        parts = []
        for filename in rubric_files:
            filepath = os.path.join(rubric_dir, filename)
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        parts.append(content)
            except FileNotFoundError:
                logger.warning(f"Rubric 文件未找到，跳过: {filename}")
            except Exception as exc:
                logger.warning(f"Rubric 文件读取失败: {filename} ({type(exc).__name__}: {exc})")
        return "\n\n".join(parts) if parts else ""
```

- [ ] **Step 3: 修改 `CodeInterpreterMiddleware` 传入 PTC**

将第 431 行的：
```python
                CodeInterpreterMiddleware(),
```
改为：
```python
                CodeInterpreterMiddleware(ptc=ptc_tool_names),
```

- [ ] **Step 4: 在 invoke payload 中注入 rubric**

在 `agent.ainvoke()` 调用处（约第 466 行），在 payload dict 中添加 `"rubric"` 键。将：

```python
            response = await agent.ainvoke(
                {
                    "messages": messages,
                    "user_id": user_id,
                    "group_id": group_id,
                    "image_inputs": image_inputs or [],
                    "video_inputs": video_inputs or [],
                },
                config=config,
            )
```

改为：

```python
            response = await agent.ainvoke(
                {
                    "messages": messages,
                    "user_id": user_id,
                    "group_id": group_id,
                    "image_inputs": image_inputs or [],
                    "video_inputs": video_inputs or [],
                    "rubric": rubric_text,
                },
                config=config,
            )
```

- [ ] **Step 5: 运行现有测试确保不引入回归**

```bash
python -m pytest test/utils/agents_test.py -v --tb=short
```

预期：全部 PASS（rubric 为空字符串时 RubricMiddleware 是 no-op，不影响现有行为）

- [ ] **Step 6: 提交**

```bash
git add utils/agents.py
git commit -m "feat: configure RubricMiddleware with chat quality criteria and CodeInterpreterMiddleware with full PTC

- Load merged rubric from prompts/rubric_*.md files and inject via invoke state
- Enable PTC for CodeInterpreterMiddleware with all agent tool names
- Rubric only activates in chat_agent (not assistant_agent)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: 验证端到端行为

**Files:**
- Run: `test/utils/agents_test.py` (现有测试)

- [ ] **Step 1: 运行完整测试套件**

```bash
python -m pytest test/utils/agents_test.py -v --tb=long
```

预期：全部 20 个测试 PASS

- [ ] **Step 2: 运行 lint 检查**

```bash
ruff check utils/agents.py
```

预期：无 lint 错误

- [ ] **Step 3: 手动验证 rubric 文件加载（可选）**

```bash
python -c "
from utils.agents import FrontierCognitive
rubric = FrontierCognitive._load_rubric()
print(f'Rubric length: {len(rubric)} chars')
print('---')
print(rubric[:500])
"
```

预期：输出合并后的 rubric 文本，长度 > 0
