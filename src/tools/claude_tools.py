"""
Claude CLI Tools Module

Provides MCP tools for interacting with Claude CLI (Anthropic's Claude Code).
"""

import subprocess
import os
import logging
from typing import Optional, Literal
from dataclasses import dataclass

from ..security import (
    sanitize_for_prompt,
    validate_path_security,
    get_safe_working_dir,
    mask_api_keys,
)

logger = logging.getLogger(__name__)

# Claude CLI configuration
CLAUDE_CLI_PATH = os.environ.get(
    "CLAUDE_CLI_PATH",
    "/Users/rush/.nvm/versions/node/v24.11.1/bin/claude"
)
DEFAULT_TIMEOUT = 300  # 5 minutes
DEFAULT_MODEL = os.environ.get("CLAUDE_DEFAULT_MODEL", "sonnet")

# Model options
CLAUDE_MODELS = Literal["sonnet", "opus", "haiku"]


@dataclass
class ClaudeResult:
    """Result from Claude CLI execution."""
    success: bool
    output: str
    error: Optional[str] = None
    model: Optional[str] = None


def _get_claude_path() -> str:
    """Get the Claude CLI executable path."""
    if os.path.exists(CLAUDE_CLI_PATH):
        return CLAUDE_CLI_PATH

    # Try to find in PATH
    import shutil
    claude_in_path = shutil.which("claude")
    if claude_in_path:
        return claude_in_path

    raise FileNotFoundError(
        "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
    )


def _execute_claude(
    args: list[str],
    working_dir: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ClaudeResult:
    """
    Execute Claude CLI with safety measures.

    Args:
        args: Command arguments (without 'claude' prefix)
        working_dir: Working directory for execution
        timeout: Timeout in seconds

    Returns:
        ClaudeResult with execution outcome
    """
    claude_path = _get_claude_path()
    cwd = get_safe_working_dir(working_dir)

    # Build command
    cmd = [claude_path] + args

    # Minimal environment
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "TERM": "xterm-256color",
        "CLAUDE_CODE_ENTRYPOINT": "mcp",
        # Preserve necessary auth
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    }

    logger.info(f"Executing Claude CLI: {mask_api_keys(' '.join(cmd))}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            shell=False,  # Critical: prevent shell injection
        )

        return ClaudeResult(
            success=result.returncode == 0,
            output=result.stdout.strip(),
            error=result.stderr.strip() if result.returncode != 0 else None,
        )

    except subprocess.TimeoutExpired:
        return ClaudeResult(
            success=False,
            output="",
            error=f"Execution timed out after {timeout} seconds",
        )
    except FileNotFoundError:
        return ClaudeResult(
            success=False,
            output="",
            error="Claude CLI not found",
        )
    except Exception as e:
        return ClaudeResult(
            success=False,
            output="",
            error=str(e),
        )


def claude_quick_query(
    query: str,
    context: Optional[str] = None,
    model: CLAUDE_MODELS = DEFAULT_MODEL,
) -> dict:
    """
    Ask Claude a quick question.

    Args:
        query: The question to ask
        context: Optional context to provide
        model: Model to use (sonnet/opus/haiku)

    Returns:
        Dict with success, output, and optional error
    """
    # Sanitize input
    safe_query = sanitize_for_prompt(query)

    # Build prompt
    prompt = safe_query
    if context:
        safe_context = sanitize_for_prompt(context, max_length=50000)
        prompt = f"Context:\n{safe_context}\n\nQuestion:\n{safe_query}"

    # Build args
    args = [
        "--print",  # Non-interactive output
        "--dangerously-skip-permissions",
        "--model", model,
        prompt,
    ]

    result = _execute_claude(args)

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "model": model,
    }


def claude_analyze_code(
    code_content: str,
    analysis_type: Literal["comprehensive", "security", "performance", "architecture"] = "comprehensive",
) -> dict:
    """
    Analyze code using Claude CLI.

    Args:
        code_content: The code to analyze
        analysis_type: Type of analysis to perform

    Returns:
        Dict with analysis results
    """
    # Sanitize code input
    safe_code = sanitize_for_prompt(code_content, max_length=50000)

    # Build analysis prompt based on type
    prompts = {
        "comprehensive": "Provide a comprehensive analysis of this code including purpose, structure, potential issues, and improvement suggestions:",
        "security": "Perform a security audit of this code. Identify vulnerabilities, injection risks, authentication issues, and data exposure:",
        "performance": "Analyze the performance characteristics of this code. Identify bottlenecks, inefficient patterns, and optimization opportunities:",
        "architecture": "Analyze the architecture of this code. Evaluate design patterns, coupling, cohesion, and suggest structural improvements:",
    }

    prompt = f"{prompts[analysis_type]}\n\n```\n{safe_code}\n```"

    args = [
        "--print",
        "--dangerously-skip-permissions",
        prompt,
    ]

    result = _execute_claude(args, timeout=180)  # 3 min for analysis

    return {
        "success": result.success,
        "analysis_type": analysis_type,
        "output": result.output,
        "error": result.error,
    }


def claude_run_task(
    prompt: str,
    working_dir: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Execute a Claude Code task with full agent capabilities.

    Args:
        prompt: Task description
        working_dir: Working directory (validated for security)
        timeout: Timeout in seconds (default: 300)

    Returns:
        Dict with task execution results
    """
    # Sanitize prompt
    safe_prompt = sanitize_for_prompt(prompt)

    # Validate working directory if provided
    if working_dir:
        is_valid, message = validate_path_security(working_dir)
        if not is_valid:
            return {
                "success": False,
                "output": "",
                "error": f"Invalid working directory: {message}",
            }

    args = [
        "--print",
        "--dangerously-skip-permissions",
        safe_prompt,
    ]

    result = _execute_claude(args, working_dir=working_dir, timeout=timeout)

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "working_dir": working_dir or os.getcwd(),
    }


def get_claude_version() -> dict:
    """
    Get the installed Claude CLI version.

    Returns:
        Dict with version info
    """
    try:
        claude_path = _get_claude_path()
        result = subprocess.run(
            [claude_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )

        version = result.stdout.strip() or result.stderr.strip()

        return {
            "success": True,
            "version": version,
            "path": claude_path,
        }
    except Exception as e:
        return {
            "success": False,
            "version": None,
            "error": str(e),
        }
