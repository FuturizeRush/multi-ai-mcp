"""
CLI Tools Module for Multi-AI MCP Server

Provides interfaces to various AI CLI tools.
"""

from .claude_tools import (
    claude_quick_query,
    claude_analyze_code,
    claude_run_task,
    get_claude_version,
)

from .codex_tools import (
    codex_exec,
    codex_review,
    codex_sandbox_run,
    get_codex_version,
)

from .gemini_tools import (
    gemini_quick_query,
    gemini_analyze_code,
    gemini_codebase_analysis,
    get_gemini_version,
)

from .antigravity_tools import (
    antigravity_open,
    antigravity_diff,
    antigravity_list_extensions,
    antigravity_add_folder,
    antigravity_status,
    get_antigravity_version,
)

__all__ = [
    # Claude
    "claude_quick_query",
    "claude_analyze_code",
    "claude_run_task",
    "get_claude_version",
    # Codex
    "codex_exec",
    "codex_review",
    "codex_sandbox_run",
    "get_codex_version",
    # Gemini
    "gemini_quick_query",
    "gemini_analyze_code",
    "gemini_codebase_analysis",
    "get_gemini_version",
    # Antigravity
    "antigravity_open",
    "antigravity_diff",
    "antigravity_list_extensions",
    "antigravity_add_folder",
    "antigravity_status",
    "get_antigravity_version",
]
