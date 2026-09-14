# ACP 插件

ACP 专属实现、配置示例和协议文档集中在本目录。

| 文件 | 职责 |
|------|------|
| `__init__.py` | 延迟导出的 Python API，以及 NoneBot 插件加载入口 |
| `commands.py` | QQ `/acp` 命令、访问控制、媒体输入和结果投递 |
| `lifecycle.py` | 子进程关闭与每日 ACP 缓存清理任务 |
| `service.py` | 配置解析、v1 客户端、进程与会话生命周期、权限和超时 |
| `client_v2.py` | v2 客户端及会话更新适配 |
| `agent.py` | 将外部 Agent 结果转换为 Frontier 返回格式 |
| `subagent.py` | Deep Agents 子代理桥接与工件保存 |
| `server.py` / `server_v2.py` | Frontier 内置 Agent 的 v1 / v2 stdio 服务端 |
| `__main__.py` | 独立 stdio CLI |
| `acp.json.example` | 外部 ACP Agent 配置示例 |
| `docs/` | [v1 接入规范](docs/acp-v1.md)与 [v2 接入规范](docs/acp-v2.md) |

在项目根目录执行：

```bash
cp plugins/acp/acp.json.example acp.json
uv run --locked python -m plugins.acp --protocol-version 1
# v2 Draft
uv run --locked python -m plugins.acp --protocol-version 2
```

运行时配置仍从工作目录的 `acp.json` 读取，现有部署不需要搬迁配置。
`scripts/frontier_acp.py` 保留为兼容入口，转发到本插件的 CLI。
普通 Python 导入不会注册 QQ 命令；NoneBot 加载 `plugins.acp` 时注册命令和生命周期钩子。

主 Agent 通过 `plugins.acp.subagent.build_acp_subagents` 接入外部 Agent。
协议无关的执行入口、进度事件和媒体基础设施继续由 `utils` 共享。

测试位于 `test/plugins/acp/`；跨进程协议及加载测试位于 `test/integration/`：

```bash
uv run --locked pytest test/plugins/acp/ test/integration/acp_protocols_test.py test/integration/acp_imports_test.py -q
uv run --locked ty check plugins/acp scripts/frontier_acp.py
```
