# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **NoneBot2 chatbot** named "frontier" that integrates with LangChain, LangGraph, and multiple MCP (Model Context Protocol) servers. The bot processes messages from QQ and OneBot adapters, uses an intelligent agent powered by ChatOpenAI to respond to user queries, and can render markdown responses as images.

## Architecture

### Core Components

- **Main Bot Handler** (`plugins/frontier/__init__.py`): Entry point handling message routing, update commands, and response formatting
- **Cognitive Agent** (`plugins/frontier/cognitive.py`): LangGraph-powered intelligent agent with tool integration, memory management, and conversation state
- **Tool System** (`plugins/frontier/tools/`): Modular tool collection including web extraction, weather, astronomy, bilibili integration, and MCP client
- **MCP Integration** (`plugins/frontier/tools/mcp_client.py`): Multi-server MCP client providing access to external services
- **Context Checker** (`plugins/frontier/context_check.py`): Image analysis and content validation
- **Markdown Renderer** (`plugins/frontier/markdown_render.py`): Converts markdown text to images for chat display

### MCP Servers Configuration

The bot integrates with multiple MCP servers defined in `mcp.json`:
- **arxiv-mcp-server**: Academic paper search and retrieval
- **time**: Timezone-aware time services
- **sequential-thinking**: Enhanced reasoning capabilities
- **tavily**: Web search and information retrieval
- **playwright**: Web automation and scraping
- **pydantic-run-python**: Python code execution
- **osm-mcp-server**: OpenStreetMap integration
- **12306-mcp**: Chinese railway information
- **trends-hub**: Trending topics and social media analysis
- **mcp-server-git**: Git repository operations
- **howtocook-mcp**: Cooking recipes and instructions
- **amap-maps**: Chinese mapping services

### Message Flow

1. User sends message → `handle_common()` in `__init__.py`
2. Message extraction and image processing → `message_extract()`
3. Intelligent agent processing → `intelligent_agent()` in `cognitive.py`
4. Tool execution via LangGraph and MCP integration
5. Response formatting and delivery → `send_messages()` or `send_artifacts()`

## Development Commands

### Setup and Installation
```bash
# Install dependencies
uv sync

# Activate virtual environment (Linux/Mac)
source .venv/bin/activate

# Activate virtual environment (Windows)
.venv/Scripts/Activate.ps1
```

### Running the Bot
```bash
# Start with auto-reload (recommended for development)
nb run --reload

# Or use the provided scripts
./run.sh          # Linux/Mac
./run.ps1         # Windows
```

### Code Quality
```bash
# Format code
ruff format

# Lint code
ruff check

# Fix auto-fixable lint issues
ruff check --fix
```

### Bot Commands
- `更新` or `update`: Updates the repository (git pull + uv sync)
- Regular messages: Processed by the intelligent agent

## Configuration Files

- **`pyproject.toml`**: Python project configuration, dependencies, and tool settings
- **`mcp.json`**: MCP server configurations and connection details
- **`configs/system_prompt.txt`**: System prompt template for the intelligent agent
- **NoneBot Configuration**: Adapters and plugin settings in `pyproject.toml` under `[tool.nonebot]`

## Key Dependencies

- **NoneBot2**: Bot framework with QQ and OneBot adapter support
- **LangChain/LangGraph**: Agent orchestration and tool integration
- **MCP**: Model Context Protocol for external service integration
- **OpenAI**: LLM backend for the intelligent agent
- **Pillow**: Image processing and markdown rendering
- **FastAPI**: Web framework components
- **BeautifulSoup4**: HTML parsing for web tools

## Tool Development

Tools are organized modularly in `plugins/frontier/tools/`. Each tool follows the LangChain tool pattern and can be:
- Standalone Python functions with tool decorators
- MCP client integrations
- Custom implementations for specific services

The `ModuleTools` class in `tools/__init__.py` automatically discovers and loads all available tools for the agent.