"""
Gemini CLI Tools Module

Provides MCP tools for interacting with Gemini CLI (Google's AI CLI).
Note: Uses subprocess with shell=False for safe execution.
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

# Gemini CLI configuration
GEMINI_CLI_PATH = os.environ.get(
    "GEMINI_CLI_PATH",
    "/opt/homebrew/bin/gemini"
)
DEFAULT_TIMEOUT = 300  # 5 minutes

# Analysis scope options
ANALYSIS_SCOPES = Literal["structure", "security", "performance", "patterns", "all"]


@dataclass
class GeminiResult:
    """Result from Gemini CLI execution."""
    success: bool
    output: str
    error: Optional[str] = None


def _get_gemini_path() -> str:
    """Get the Gemini CLI executable path."""
    if os.path.exists(GEMINI_CLI_PATH):
        return GEMINI_CLI_PATH

    # Try to find in PATH
    import shutil
    gemini_in_path = shutil.which("gemini")
    if gemini_in_path:
        return gemini_in_path

    raise FileNotFoundError(
        "Gemini CLI not found. Install with: npm install -g @anthropic-ai/gemini-cli"
    )


def _execute_gemini(
    args: list[str],
    working_dir: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> GeminiResult:
    """
    Execute Gemini CLI with safety measures.
    Uses shell=False to prevent command injection.

    Args:
        args: Command arguments (without 'gemini' prefix)
        working_dir: Working directory for execution
        timeout: Timeout in seconds

    Returns:
        GeminiResult with execution outcome
    """
    gemini_path = _get_gemini_path()
    cwd = get_safe_working_dir(working_dir)

    # Build command as list (shell=False pattern)
    cmd = [gemini_path] + args

    # Minimal environment
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "TERM": "xterm-256color",
        # Preserve Google auth
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
        "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
    }

    logger.info(f"Executing Gemini CLI: {mask_api_keys(' '.join(cmd))}")

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

        return GeminiResult(
            success=result.returncode == 0,
            output=result.stdout.strip(),
            error=result.stderr.strip() if result.returncode != 0 else None,
        )

    except subprocess.TimeoutExpired:
        return GeminiResult(
            success=False,
            output="",
            error=f"Execution timed out after {timeout} seconds",
        )
    except FileNotFoundError:
        return GeminiResult(
            success=False,
            output="",
            error="Gemini CLI not found",
        )
    except Exception as e:
        return GeminiResult(
            success=False,
            output="",
            error=str(e),
        )


def gemini_quick_query(
    query: str,
    context: Optional[str] = None,
) -> dict:
    """
    Ask Gemini a quick question.

    Args:
        query: The question to ask
        context: Optional context to provide

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

    # Use -p for non-interactive mode
    args = ["-p", prompt]

    result = _execute_gemini(args)

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
    }


def gemini_analyze_code(
    code_content: str,
    analysis_type: Literal["comprehensive", "security", "performance", "architecture"] = "comprehensive",
) -> dict:
    """
    Analyze code using Gemini CLI.

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

    args = ["-p", prompt]

    result = _execute_gemini(args, timeout=180)  # 3 min for analysis

    return {
        "success": result.success,
        "analysis_type": analysis_type,
        "output": result.output,
        "error": result.error,
    }


def gemini_codebase_analysis(
    directory_path: str,
    analysis_scope: ANALYSIS_SCOPES = "all",
) -> dict:
    """
    Analyze an entire directory using Gemini CLI's 1M token context.

    Args:
        directory_path: Path to directory to analyze
        analysis_scope: Scope of analysis (structure/security/performance/patterns/all)

    Returns:
        Dict with codebase analysis results
    """
    # Validate directory path
    is_valid, message = validate_path_security(directory_path)
    if not is_valid:
        return {
            "success": False,
            "output": "",
            "error": f"Invalid directory path: {message}",
        }

    if not os.path.isdir(directory_path):
        return {
            "success": False,
            "output": "",
            "error": f"Path is not a directory: {directory_path}",
        }

    # Build scope-specific prompts
    scope_prompts = {
        "structure": "Analyze the structure and organization of this codebase. Describe the directory layout, module dependencies, and architectural patterns.",
        "security": "Perform a security audit of this codebase. Identify potential vulnerabilities, insecure patterns, and security best practice violations.",
        "performance": "Analyze the performance characteristics of this codebase. Identify potential bottlenecks, inefficient patterns, and optimization opportunities.",
        "patterns": "Identify design patterns used in this codebase. Evaluate their effectiveness and suggest improvements.",
        "all": "Provide a comprehensive analysis of this codebase including structure, security, performance, and design patterns.",
    }

    prompt = f"{scope_prompts[analysis_scope]}\n\nDirectory: {directory_path}"

    # Change to the directory for context
    args = ["-p", prompt]

    result = _execute_gemini(args, working_dir=directory_path, timeout=300)

    return {
        "success": result.success,
        "analysis_scope": analysis_scope,
        "directory": directory_path,
        "output": result.output,
        "error": result.error,
    }


def get_gemini_version() -> dict:
    """
    Get the installed Gemini CLI version.

    Returns:
        Dict with version info
    """
    try:
        gemini_path = _get_gemini_path()
        # SECURITY: shell=False with list args
        result = subprocess.run(
            [gemini_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )

        version = result.stdout.strip() or result.stderr.strip()

        return {
            "success": True,
            "version": version,
            "path": gemini_path,
        }
    except Exception as e:
        return {
            "success": False,
            "version": None,
            "error": str(e),
        }
