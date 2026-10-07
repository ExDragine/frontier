# Laya 决策 Provider

`utils.decision.LayaDecisionProvider` 是 Laya 与 Frontier 之间的边界。
它支持两种后端：

- **本地 SDK**：不设置 `base_url`，首次调用时惰性导入 `laya.Router`。
- **HTTP 服务**：设置 `base_url`，请求兼容 Laya/Jev 的 `/v1/systemone` 接口。

同一 `DecisionProvider` 协议也有 `LLMDecisionProvider` 实现：它使用 `[models]`
中的 `decision_model`，把传统聊天模型的输出转换为 Pydantic 校验的结构化答案。
群聊主动回复的最终判断通过这个 provider 执行；@ 和唤醒词仍走显式触发规则。
Laya 是可选的候选预筛，默认关闭，不会绕过最终判断。这里尚未接入 OpenAI `/v1/decisions`。
普通文本、翻译和格式化任务不经过这个 provider，使用 `basic_model`。

内部问题与答案使用 `predicate` / `probability`；仅 Laya 适配器转换为旧 `noul` 协议。
`confidence` 可选，与命题为真的概率分开，未返回时保留 `None`。
provider 校验问题 ID 完整性、答案类型、概率/置信度范围、choice 候选和 score 范围。
内部 choice 问题使用字符串列表 `choices`，score 使用有序字符串列表 `levels`，分数范围为零起始索引。
拒答显式返回 `type="refusal"` 和 `reason`；门控返回静默且概率为 `None`。
最终门控只在概率大于 0.5 时通过；异常或无效答案保持静默。该阈值仍需真实标注样例校准。

Laya 作为项目主依赖安装，但仍不会在 import 阶段加载 torch、transformers 或模型权重。
HTTP 模式只需要配置 `base_url`；本地模式首次使用时才加载 SDK 和模型。

## 最小示例

```python
from utils.decision import LayaDecisionProvider, score_reply_gate

provider = LayaDecisionProvider(model="auto", device="cpu")
score = await score_reply_gate(provider, "这个报错怎么解决？")
if score.should_reply:
    ...
```

HTTP 服务模式：

```python
provider = LayaDecisionProvider(
    model="multilingual",
    base_url="http://127.0.0.1:8000",
    api_key="...",  # 可选，对应 LAYA_API_KEY
)
```

## 本地比较

仓库提供了脱敏的合成门控样例。运行本地 Laya 评估：

```bash
uv run --locked \
  python scripts/evaluate_reply_gate.py --model multilingual
```

脚本会同时报告当前候选词门控和 Laya 的 accuracy、precision、recall、F1、
概率和延迟。样例只用于接口和趋势验证，不能代表生产效果；上线前应使用脱敏、
人工标注的真实消息，并按语言和群活跃度重新校准阈值。

Laya 的预测结果只能作为决策层输入。Decision LLM 仍是默认线上门控，浏览器截图/录屏等
受控工具继续 fail-closed。启用 Laya 前应先运行 shadow mode，记录两者的分歧、延迟、
fallback 和人工纠错结果。
