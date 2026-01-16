"""
Codex CLI Tools Module

Provides MCP tools for interacting with Codex CLI (OpenAI's Codex Agent).
Note: Uses subprocess with shell=False for safe execution (no shell injection risk).
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

# Codex CLI configuration
CODEX_CLI_PATH = os.environ.get(
    "CODEX_CLI_PATH",
    "/Users/rush/.nvm/versions/node/v24.11.1/bin/codex"
)
DEFAULT_TIMEOUT = 300  # 5 minutes
DEFAULT_MODEL = os.environ.get("CODEX_DEFAULT_MODEL", "o4-mini")

# Sandbox modes
SANDBOX_MODES = Literal["read-only", "workspace-write", "danger-full-access"]


@dataclass
class CodexResult:
    """Result from Codex CLI execution."""
    success: bool
    output: str
    error: Optional[str] = None
    model: Optional[str] = None


def _get_codex_path() -> str:
    """Get the Codex CLI executable path."""
    if os.path.exists(CODEX_CLI_PATH):
        return CODEX_CLI_PATH

    # Try to find in PATH
    import shutil
    codex_in_path = shutil.which("codex")
    if codex_in_path:
        return codex_in_path

    raise FileNotFoundError(
        "Codex CLI not found. Install with: npm install -g @openai/codex"
    )


def _execute_codex(
    args: list[str],
    working_dir: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> CodexResult:
    """
    Execute Codex CLI with safety measures.
    Uses shell=False to prevent command injection.

    Args:
        args: Command arguments (without 'codex' prefix)
        working_dir: Working directory for execution
        timeout: Timeout in seconds

    Returns:
        CodexResult with execution outcome
    """
    codex_path = _get_codex_path()
    cwd = get_safe_working_dir(working_dir)

    # Build command as list (shell=False pattern)
    cmd = [codex_path] + args

    # Minimal environment
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "TERM": "xterm-256color",
        # Preserve necessary auth
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
    }

    logger.info(f"Executing Codex CLI: {mask_api_keys(' '.join(cmd))}")

    try:
        # SECURITY: shell=False prevents shell injection
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            shell=False,
        )

        return CodexResult(
            success=result.returncode == 0,
            output=result.stdout.strip(),
            error=result.stderr.strip() if result.returncode != 0 else None,
        )

    except subprocess.TimeoutExpired:
        return CodexResult(
            success=False,
            output="",
            error=f"Execution timed out after {timeout} seconds",
        )
    except FileNotFoundError:
        return CodexResult(
            success=False,
            output="",
            error="Codex CLI not found",
        )
    except Exception as e:
        return CodexResult(
            success=False,
            output="",
            error=str(e),
        )


def codex_exec(
    prompt: str,
    working_dir: Optional[str] = None,
    model: Optional[str] = None,
    sandbox: SANDBOX_MODES = "read-only",
) -> dict:
    """
    Run Codex non-interactively with exec command.

    Args:
        prompt: Instructions for the agent
        working_dir: Working directory (validated for security)
        model: Model to use (default: o4-mini)
        sandbox: Sandbox policy (read-only/workspace-write/danger-full-access)

    Returns:
        Dict with execution results
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

    # Build args as list
    args = ["exec"]

    if model:
        args.extend(["--model", model])

    # Use read-only sandbox by default for safety
    args.extend(["--sandbox", sandbox])

    # Change to working directory if specified
    if working_dir:
        args.extend(["--cd", working_dir])

    args.append(safe_prompt)

    result = _execute_codex(args, working_dir=working_dir)

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "model": model or DEFAULT_MODEL,
        "sandbox": sandbox,
    }


def codex_review(
    target_path: Optional[str] = None,
    review_type: Literal["uncommitted", "base", "commit"] = "uncommitted",
    base_branch: Optional[str] = None,
    commit_sha: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> dict:
    """
    Run a code review using Codex.

    Args:
        target_path: Path to the repository to review
        review_type: Type of review (uncommitted/base/commit)
        base_branch: Base branch for comparison (when review_type is 'base')
        commit_sha: Commit SHA to review (when review_type is 'commit')
        custom_instructions: Additional review instructions

    Returns:
        Dict with review results
    """
    # Validate target path if provided
    if target_path:
        is_valid, message = validate_path_security(target_path)
        if not is_valid:
            return {
                "success": False,
                "output": "",
                "error": f"Invalid target path: {message}",
            }

    # Build args as list
    args = ["review"]

    if review_type == "uncommitted":
        args.append("--uncommitted")
    elif review_type == "base" and base_branch:
        args.extend(["--base", base_branch])
    elif review_type == "commit" and commit_sha:
        args.extend(["--commit", commit_sha])

    if custom_instructions:
        safe_instructions = sanitize_for_prompt(custom_instructions, max_length=10000)
        args.append(safe_instructions)

    result = _execute_codex(args, working_dir=target_path, timeout=180)

    return {
        "success": result.success,
        "review_type": review_type,
        "output": result.output,
        "error": result.error,
    }


def codex_sandbox_run(
    command: str,
    working_dir: Optional[str] = None,
    timeout: int = 60,
) -> dict:
    """
    Run a command in Codex's sandbox environment.

    Args:
        command: Command to execute in sandbox
        working_dir: Working directory for execution
        timeout: Timeout in seconds (default: 60)

    Returns:
        Dict with command output
    """
    # Sanitize command (basic protection, sandbox provides additional isolation)
    safe_command = sanitize_for_prompt(command, max_length=5000)

    # Validate working directory
    if working_dir:
        is_valid, message = validate_path_security(working_dir)
        if not is_valid:
            return {
                "success": False,
                "output": "",
                "error": f"Invalid working directory: {message}",
            }

    # Use sandbox subcommand - args as list for shell=False safety
    args = ["sandbox"]

    if working_dir:
        args.extend(["--cd", working_dir])

    args.extend(["--", "sh", "-c", safe_command])

    result = _execute_codex(args, working_dir=working_dir, timeout=timeout)

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "command": safe_command,
    }


def get_codex_version() -> dict:
    """
    Get the installed Codex CLI version.

    Returns:
        Dict with version info
    """
    try:
        codex_path = _get_codex_path()
        # SECURITY: shell=False with list args
        result = subprocess.run(
            [codex_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )

        version = result.stdout.strip() or result.stderr.strip()

        return {
            "success": True,
            "version": version,
            "path": codex_path,
        }
    except Exception as e:
        return {
            "success": False,
            "version": None,
            "error": str(e),
        }
