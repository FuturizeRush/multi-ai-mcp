# Multi-AI MCP Server

A unified [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides access to multiple AI CLI tools through a single interface.

## Features

- **Multi-Tool Support**: Access Claude, Codex, Gemini, and Antigravity CLIs through MCP
- **Security First**: Prompt injection protection, path validation, and shell=False execution
- **Version Management**: Check versions and update CLI tools to latest releases
- **FastMCP Integration**: Pydantic-validated tools with automatic schema generation

## Supported CLI Tools

| Tool | Description | Version |
|------|-------------|---------|
| Claude CLI | Anthropic's Claude Code agent | v2.1.6+ |
| Codex CLI | OpenAI's Codex agent | v0.79.0+ |
| Gemini CLI | Google's Gemini AI | v0.24.0+ |
| Antigravity | VS Code command line tool | v1.104.0+ |

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for npm-based CLIs)
- At least one of the supported CLI tools installed

### Quick Install

```bash
# Clone the repository
git clone https://github.com/FuturizeRush/multi-ai-mcp.git
cd multi-ai-mcp

# Install dependencies
pip install -e .
```

### Install CLI Tools

```bash
# Claude CLI
npm install -g @anthropic-ai/claude-code

# Codex CLI
npm install -g @openai/codex

# Gemini CLI
npm install -g @anthropic-ai/gemini-cli
```

## Configuration

### Add to Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "multi-ai": {
      "command": "python",
      "args": ["/path/to/multi-ai-mcp/src/server.py"],
      "env": {
        "CLAUDE_DEFAULT_MODEL": "sonnet"
      }
    }
  }
}
```

### Environment Variables

Create a `.env` file or set environment variables:

```env
# CLI Paths (optional - auto-detected if in PATH)
CLAUDE_CLI_PATH=/path/to/claude
CODEX_CLI_PATH=/path/to/codex
GEMINI_CLI_PATH=/path/to/gemini
ANTIGRAVITY_CLI_PATH=/path/to/antigravity

# Default Models
CLAUDE_DEFAULT_MODEL=sonnet
CODEX_DEFAULT_MODEL=o4-mini

# API Keys (optional - for fallback)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

## Available Tools

### Claude CLI (3 tools)

| Tool | Description |
|------|-------------|
| `claude_quick_query` | Ask Claude a question |
| `claude_analyze_code` | Analyze code (security/performance/architecture) |
| `claude_run_task` | Execute a full agent task |

### Codex CLI (3 tools)

| Tool | Description |
|------|-------------|
| `codex_run` | Run Codex non-interactively |
| `codex_review` | Code review (uncommitted/base/commit) |
| `codex_sandbox_run` | Execute in sandboxed environment |

### Gemini CLI (3 tools)

| Tool | Description |
|------|-------------|
| `gemini_quick_query` | Ask Gemini a question |
| `gemini_analyze_code` | Analyze code with Gemini |
| `gemini_codebase_analysis` | Analyze entire codebase (1M token context) |

### Antigravity CLI (3 tools)

| Tool | Description |
|------|-------------|
| `antigravity_open` | Open file in VS Code |
| `antigravity_diff` | Compare two files |
| `antigravity_list_extensions` | List VS Code extensions |

### Update Tools (3 tools)

| Tool | Description |
|------|-------------|
| `multi_ai_check_versions` | Check installed CLI versions |
| `multi_ai_check_updates` | Check for available updates |
| `multi_ai_update` | Update a specific CLI tool |

## Security

This server implements multiple security measures:

- **Prompt Injection Protection**: Filters dangerous patterns like "ignore previous instructions"
- **Path Validation**: Blocks access to system paths (`/etc/`, `/proc/`, etc.)
- **Shell Injection Prevention**: All subprocess calls use `shell=False`
- **API Key Masking**: Sensitive keys are masked in logs
- **Input Length Limits**: Prevents token exhaustion attacks

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check src tests

# Type checking
mypy src
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please open an issue or pull request.

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [FastMCP](https://github.com/anthropics/fastmcp) for the MCP framework
- [claude-gemini-mcp-slim](https://github.com/cmdaltctr/claude-gemini-mcp-slim) for inspiration
