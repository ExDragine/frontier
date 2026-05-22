# DeepSeek Balance Tool Design

## Context

Frontier discovers LangChain tools by scanning `tools/*.py` for `BaseTool` instances. DeepSeek API credentials already live in `EnvConfig.DEEPSEEK_API_KEY`, with an optional `EnvConfig.DEEPSEEK_API_BASE` used by the LLM factory.

The DeepSeek balance API is `GET /user/balance`. It returns an `is_available` flag and a `balance_infos` array with `currency`, `total_balance`, `granted_balance`, and `topped_up_balance`.

## Goal

Add a main-agent tool that lets the assistant query the configured DeepSeek account balance without requiring tool arguments.

## Architecture

Create `tools/deepseek_balance.py` as a focused module responsible only for DeepSeek balance querying and formatting. The module will own an async `httpx.AsyncClient`, an `aclose_http_client()` lifecycle hook, URL normalization helpers, response formatting helpers, and one LangChain tool named `get_deepseek_api_balance`.

The tool reads `EnvConfig.DEEPSEEK_API_KEY` at call time. If the key is empty, it returns a clear Chinese message. If `EnvConfig.DEEPSEEK_API_BASE` is present, the tool uses its scheme and host but always targets `/user/balance`; otherwise it defaults to `https://api.deepseek.com/user/balance`.

`tools/__init__.py` should map the new module to the `main` tool group explicitly so the grouping test documents the intended exposure.

## Data Flow

1. The agent invokes `get_deepseek_api_balance()`.
2. The tool reads and strips `EnvConfig.DEEPSEEK_API_KEY`.
3. The tool builds the balance URL from `EnvConfig.DEEPSEEK_API_BASE` or the DeepSeek default.
4. The tool performs `GET` with `Authorization: Bearer <key>`.
5. The response JSON is formatted into concise Chinese text:
   - Availability: `可用` or `不可用`
   - One line per balance info entry with total, granted, and topped-up balances

## Error Handling

Missing API key returns `未配置 DeepSeek API Key：请在 env.toml 的 [key].deepseek_api_key 中填写。`

HTTP and network failures are caught and returned as `获取 DeepSeek API 余额失败: <error>`, with details logged through NoneBot logger.

Malformed response payloads are caught by validating the top-level JSON object and `balance_infos` array before formatting.

## Testing

Add tests in `test/tools/basic_info_tools_test.py` for:

- Successful formatting of CNY balance information.
- Missing API key behavior.
- Base URL normalization from a `/v1` API base to `/user/balance`.
- HTTP failure reporting.

Update `test/tools/http_client_lifecycle_test.py` so the new module participates in the shared async client close contract.

Update the existing tool grouping test so `deepseek_balance` is expected in the main tool set.

## Spec Review

No placeholders remain. Scope is limited to one API-specific tool plus tests. The design avoids adding a generic provider balance abstraction until another provider needs the same behavior.
