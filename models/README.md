# 模型目录

`models` 是 Frontier 内置的模型元数据模块。它只描述已核验的官方模型，不参与模型路由，也不把目录外模型判定为“不支持”。

`data/lobehub_names.json` 是独立的友好名称覆盖层，来自 LobeHub 发布的
[`model-bank`](https://www.npmjs.com/package/model-bank) NPM 包。它只参与界面名称展示，
不会覆盖 Frontier 核验的能力、上下文窗口、生命周期或 API 协议。快照保留上游版本、
完整性哈希、Git commit 和许可证链接；上游数据遵循
[LobeHub Community License](https://github.com/lobehub/lobehub/blob/canary/LICENSE)。

`data/catalog.json` 保存目录版本与供应商文件索引；模型卡按开发商拆分在 `data/providers/*.json`，并由 `data/provider.schema.json` 统一约束。读取接口仅使用 Python 标准库。

## 使用

```python
from models import ModelFeature, get_model, get_model_display_name, list_models

model = get_model("openai", "gpt-5.6-sol")
assert model is not None
print(model.display_name)
print(get_model_display_name("openai", "gpt-image-2"))  # GPT Image 2

tool_models = list_models(feature=ModelFeature.TOOL_CALLING)
google_previews = list_models(provider="google", status="preview")

# 未收录的自定义模型不会报错。
assert get_model("my-provider", "custom-model") is None
```

`list_models()` 默认只返回 `active` 模型。传入 `status=None` 可包含所有生命周期状态。返回值和所有模型卡均不可变，便于安全缓存和跨模块共享。

## 字段

- `schema_version`：Schema 主次版本；不兼容变更提升主版本。
- `catalog_version`：数据快照版本，格式为 `YYYY.M.D`。
- `updated_at`：本次目录快照更新日期。
- `provider`：供应商文件的顶层标识；读取后会写入每张 `ModelCard`。
- `id`：保留开发商官方大小写的 canonical 模型 ID，与 `provider` 组合后全局唯一；读取接口查询时不区分大小写。
- `description`：必填的英文与简体中文说明。
- `capabilities.input` / `output`：模型接受与直接生成的模态。
- `capabilities.features`：受控的模型或官方 API 能力标签。
- `capabilities.api_modes`：开发商官方支持的 API 形态。
- `context_window`、`max_output_tokens`、`knowledge_cutoff`、`released_at`：可空技术字段。官方资料不明确时保持 `null`，不推测。
- `status`：`active`、`preview`、`legacy` 或 `deprecated`。
- `sources`：支持该模型卡内容的官方资料 URL 和核验日期。

目录不收录价格、基准分数、推荐排名，也不为聚合平台或兼容端点复制模型记录。

LobeHub model-bank 等第三方目录只能用于友好名称展示、发现候选模型和待核对字段，不能作为模型卡的最终事实来源。模型 ID、生命周期、能力和技术限制必须回到开发商官方文档核验，并在 `sources` 中记录官方页面与核验日期。模型描述需要根据官方信息重新撰写。

## 同步 LobeHub 名称

```bash
uv run python scripts/sync_lobehub_model_names.py
uv run python scripts/sync_lobehub_model_names.py --check
```

脚本只允许从 `registry.npmjs.org` 下载 `model-bank` tarball，会先校验 NPM 提供的完整性哈希，
再原子更新快照。`--version` 可用于锁定特定 NPM 版本；`--check` 只比较快照，不写文件。

## 新增或更新模型

1. 在 `data/providers/<provider>.json` 中加入开发商名下的 canonical 记录，不为别名或代理平台创建重复记录。
2. 新开发商需要创建独立文件，并在 `data/catalog.json` 的 `providers` 中登记相对路径。
3. 只依据模型开发商或官方 API 文档填写能力和技术字段，并更新 `sources[].verified_at`。
4. 同时提供非空的 `description.en` 与 `description.zh-CN`。
5. 运行 Schema、唯一性、读取接口测试和 Ruff。

纯数据更新调整 `catalog_version`；Schema 或公开读取接口发生不兼容变更时，同时提升 `schema_version`。
