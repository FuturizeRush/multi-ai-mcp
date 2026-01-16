#!/usr/bin/env python3
"""
Multi-AI MCP Server

A unified MCP server providing access to multiple AI CLI tools:
- Claude CLI (Anthropic)
- Codex CLI (OpenAI)
- Gemini CLI (Google)
- Antigravity CLI (VS Code)

Uses FastMCP for tool registration with Pydantic validation.
All subprocess calls use shell=False to prevent command injection.
"""

import logging
from typing import Optional, Literal

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("multi-ai-mcp")

# Initialize FastMCP server
mcp = FastMCP(
    "multi-ai-mcp",
    instructions="Unified MCP server for multiple AI CLI tools (Claude, Codex, Gemini, Antigravity)"
)


# =============================================================================
# Claude CLI Tools
# =============================================================================

@mcp.tool()
def claude_quick_query(
    query: str,
    context: Optional[str] = None,
    model: Literal["sonnet", "opus", "haiku"] = "sonnet"
) -> dict:
    """
    Ask Claude CLI a quick question.

    Args:
        query: The question to ask
        context: Optional context to provide
        model: Model to use (sonnet/opus/haiku)
    """
    from .tools.claude_tools import claude_quick_query as _query
    return _query(query, context, model)


@mcp.tool()
def claude_analyze_code(
    code_content: str,
    analysis_type: Literal["comprehensive", "security", "performance", "architecture"] = "comprehensive"
) -> dict:
    """
    Analyze code using Claude CLI.

    Args:
        code_content: The code to analyze
        analysis_type: Type of analysis to perform
    """
    from .tools.claude_tools import claude_analyze_code as _analyze
    return _analyze(code_content, analysis_type)


@mcp.tool()
def claude_run_task(
    prompt: str,
    working_dir: Optional[str] = None,
    timeout: int = 300
) -> dict:
    """
    Run a Claude Code task with full agent capabilities.

    Args:
        prompt: Task description
        working_dir: Working directory (validated for security)
        timeout: Timeout in seconds
    """
    from .tools.claude_tools import claude_run_task as _run
    return _run(prompt, working_dir, timeout)


# =============================================================================
# Codex CLI Tools
# =============================================================================

@mcp.tool()
def codex_run(
    prompt: str,
    working_dir: Optional[str] = None,
    model: Optional[str] = None,
    sandbox: Literal["read-only", "workspace-write", "danger-full-access"] = "read-only"
) -> dict:
    """
    Run Codex non-interactively.

    Args:
        prompt: Instructions for the agent
        working_dir: Working directory
        model: Model to use
        sandbox: Sandbox policy
    """
    from .tools.codex_tools import codex_exec as _run
    return _run(prompt, working_dir, model, sandbox)


@mcp.tool()
def codex_review(
    target_path: Optional[str] = None,
    review_type: Literal["uncommitted", "base", "commit"] = "uncommitted",
    base_branch: Optional[str] = None,
    commit_sha: Optional[str] = None,
    custom_instructions: Optional[str] = None
) -> dict:
    """
    Run a code review using Codex.

    Args:
        target_path: Path to the repository
        review_type: Type of review
        base_branch: Base branch for comparison
        commit_sha: Commit SHA to review
        custom_instructions: Additional review instructions
    """
    from .tools.codex_tools import codex_review as _review
    return _review(target_path, review_type, base_branch, commit_sha, custom_instructions)


@mcp.tool()
def codex_sandbox_run(
    command: str,
    working_dir: Optional[str] = None,
    timeout: int = 60
) -> dict:
    """
    Run a command in Codex's sandbox environment.

    Args:
        command: Command to run in sandbox
        working_dir: Working directory
        timeout: Timeout in seconds
    """
    from .tools.codex_tools import codex_sandbox_run as _sandbox
    return _sandbox(command, working_dir, timeout)


# =============================================================================
# Gemini CLI Tools
# =============================================================================

@mcp.tool()
def gemini_quick_query(
    query: str,
    context: Optional[str] = None
) -> dict:
    """
    Ask Gemini CLI a quick question.

    Args:
        query: The question to ask
        context: Optional context to provide
    """
    from .tools.gemini_tools import gemini_quick_query as _query
    return _query(query, context)


@mcp.tool()
def gemini_analyze_code(
    code_content: str,
    analysis_type: Literal["comprehensive", "security", "performance", "architecture"] = "comprehensive"
) -> dict:
    """
    Analyze code using Gemini CLI.

    Args:
        code_content: The code to analyze
        analysis_type: Type of analysis to perform
    """
    from .tools.gemini_tools import gemini_analyze_code as _analyze
    return _analyze(code_content, analysis_type)


@mcp.tool()
def gemini_codebase_analysis(
    directory_path: str,
    analysis_scope: Literal["structure", "security", "performance", "patterns", "all"] = "all"
) -> dict:
    """
    Analyze an entire directory using Gemini CLI's 1M token context.

    Args:
        directory_path: Path to directory to analyze
        analysis_scope: Scope of analysis
    """
    from .tools.gemini_tools import gemini_codebase_analysis as _codebase
    return _codebase(directory_path, analysis_scope)


# =============================================================================
# Antigravity CLI Tools
# =============================================================================

@mcp.tool()
def antigravity_open(
    file_path: str,
    goto_line: Optional[int] = None,
    goto_column: Optional[int] = None,
    new_window: bool = False,
    reuse_window: bool = False
) -> dict:
    """
    Open a file in VS Code.

    Args:
        file_path: Path to the file
        goto_line: Line number to jump to
        goto_column: Column position to jump to
        new_window: Force open in new window
        reuse_window: Force reuse existing window
    """
    from .tools.antigravity_tools import antigravity_open as _open
    return _open(file_path, goto_line, goto_column, new_window, reuse_window)


@mcp.tool()
def antigravity_diff(
    file1: str,
    file2: str
) -> dict:
    """
    Compare two files using VS Code diff viewer.

    Args:
        file1: Path to first file
        file2: Path to second file
    """
    from .tools.antigravity_tools import antigravity_diff as _diff
    return _diff(file1, file2)


@mcp.tool()
def antigravity_list_extensions(
    show_versions: bool = False,
    category: Optional[str] = None
) -> dict:
    """
    List installed VS Code extensions.

    Args:
        show_versions: Include version numbers
        category: Filter by extension category
    """
    from .tools.antigravity_tools import antigravity_list_extensions as _list
    return _list(show_versions, category)


# =============================================================================
# Update Tools
# =============================================================================

@mcp.tool()
def multi_ai_check_versions() -> dict:
    """
    Check current versions of all installed CLI tools.

    Returns version information for Claude, Codex, Gemini, and Antigravity CLIs.
    """
    from .updater import check_all_versions

    results = check_all_versions()
    return {
        "tools": {
            name: {
                "current_version": info.current_version,
                "path": info.path,
                "installed": info.current_version is not None,
                "error": info.error,
            }
            for name, info in results.items()
        }
    }


@mcp.tool()
def multi_ai_check_updates() -> dict:
    """
    Check for available updates for all CLI tools.

    Returns current and latest versions with update availability.
    """
    from .updater import check_all_versions

    results = check_all_versions()
    updates = {}
    updates_available = []

    for name, info in results.items():
        updates[name] = {
            "current_version": info.current_version,
            "latest_version": info.latest_version,
            "update_available": info.update_available,
            "path": info.path,
            "error": info.error,
        }
        if info.update_available:
            updates_available.append(name)

    return {
        "tools": updates,
        "updates_available": updates_available,
        "total_with_updates": len(updates_available),
    }


@mcp.tool()
def multi_ai_update(
    tool_name: Literal["claude", "codex", "gemini", "antigravity"],
    force: bool = False
) -> dict:
    """
    Update a specific CLI tool to the latest version.

    Args:
        tool_name: Name of the tool to update
        force: Force update even if already at latest
    """
    from .updater import update_tool
    return update_tool(tool_name, force)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the MCP server."""
    logger.info("Starting Multi-AI MCP Server v1.0.0")

    # Check installed tools
    from .updater import get_installed_tools
    installed = get_installed_tools()
    logger.info(f"Installed tools: {', '.join(installed.keys())}")

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
