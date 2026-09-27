# Laya 决策 Provider

`utils.decision.LayaDecisionProvider` 是 Laya 与 Frontier 之间的可选边界。
它支持两种后端：

- **本地 SDK**：不设置 `base_url`，首次调用时惰性导入 `laya.Router`。
- **HTTP 服务**：设置 `base_url`，请求兼容 Laya/Jev 的 `/v1/systemone` 接口。

项目默认不依赖 Laya，也不会在 import 阶段加载 torch、transformers 或模型权重。

## 最小示例

```python
from utils.decision import LayaDecisionProvider, score_reply_gate

provider = LayaDecisionProvider(model="auto")
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
uv run --locked --extra content-check --with laya \
  python scripts/evaluate_reply_gate.py --model multilingual
```

脚本会同时报告当前候选词门控和 Laya 的 accuracy、precision、recall、F1、
置信度和延迟。样例只用于接口和趋势验证，不能代表生产效果；上线前应使用脱敏、
人工标注的真实消息，并按语言和群活跃度重新校准阈值。

Laya 的预测结果只能作为决策层输入。Signal 仍是默认线上门控，浏览器截图/录屏等
受控工具继续 fail-closed。启用 Laya 前应先运行 shadow mode，记录两者的分歧、延迟、
fallback 和人工纠错结果。
