"""
Antigravity CLI Tools Module

Provides MCP tools for interacting with Antigravity CLI (VS Code command line tool).
Note: Uses subprocess with shell=False for safe execution.
"""

import subprocess
import os
import logging
from typing import Optional
from dataclasses import dataclass

from ..security import (
    validate_path_security,
    mask_api_keys,
)

logger = logging.getLogger(__name__)

# Antigravity CLI configuration
ANTIGRAVITY_CLI_PATH = os.environ.get(
    "ANTIGRAVITY_CLI_PATH",
    "/Users/rush/.antigravity/antigravity/bin/antigravity"
)
DEFAULT_TIMEOUT = 30  # 30 seconds for most operations


@dataclass
class AntigravityResult:
    """Result from Antigravity CLI execution."""
    success: bool
    output: str
    error: Optional[str] = None


def _get_antigravity_path() -> str:
    """Get the Antigravity CLI executable path."""
    if os.path.exists(ANTIGRAVITY_CLI_PATH):
        return ANTIGRAVITY_CLI_PATH

    # Try to find in PATH
    import shutil
    ag_in_path = shutil.which("antigravity")
    if ag_in_path:
        return ag_in_path

    # Also try 'code' command (standard VS Code CLI)
    code_in_path = shutil.which("code")
    if code_in_path:
        return code_in_path

    raise FileNotFoundError(
        "Antigravity CLI not found. Ensure VS Code or Antigravity is installed."
    )


def _execute_antigravity(
    args: list[str],
    timeout: int = DEFAULT_TIMEOUT,
) -> AntigravityResult:
    """
    Execute Antigravity CLI with safety measures.
    Uses shell=False to prevent command injection.

    Args:
        args: Command arguments (without 'antigravity' prefix)
        timeout: Timeout in seconds

    Returns:
        AntigravityResult with execution outcome
    """
    antigravity_path = _get_antigravity_path()

    # Build command as list (shell=False pattern)
    cmd = [antigravity_path] + args

    # Minimal environment
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "TERM": "xterm-256color",
        "DISPLAY": os.environ.get("DISPLAY", ""),
        "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", ""),
    }

    logger.info(f"Executing Antigravity CLI: {mask_api_keys(' '.join(cmd))}")

    try:
        # SECURITY: shell=False prevents shell injection
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            shell=False,
        )

        return AntigravityResult(
            success=result.returncode == 0,
            output=result.stdout.strip(),
            error=result.stderr.strip() if result.returncode != 0 else None,
        )

    except subprocess.TimeoutExpired:
        return AntigravityResult(
            success=False,
            output="",
            error=f"Execution timed out after {timeout} seconds",
        )
    except FileNotFoundError:
        return AntigravityResult(
            success=False,
            output="",
            error="Antigravity CLI not found",
        )
    except Exception as e:
        return AntigravityResult(
            success=False,
            output="",
            error=str(e),
        )


def antigravity_open(
    file_path: str,
    goto_line: Optional[int] = None,
    goto_column: Optional[int] = None,
    new_window: bool = False,
    reuse_window: bool = False,
) -> dict:
    """
    Open a file in VS Code.

    Args:
        file_path: Path to the file to open
        goto_line: Line number to jump to (1-indexed)
        goto_column: Column position to jump to (1-indexed)
        new_window: Force open in new window
        reuse_window: Force reuse existing window

    Returns:
        Dict with operation result
    """
    # Validate file path
    is_valid, message = validate_path_security(file_path)
    if not is_valid:
        return {
            "success": False,
            "output": "",
            "error": f"Invalid file path: {message}",
        }

    if not os.path.exists(file_path):
        return {
            "success": False,
            "output": "",
            "error": f"File does not exist: {file_path}",
        }

    # Build args
    args = []

    if new_window:
        args.append("--new-window")
    elif reuse_window:
        args.append("--reuse-window")

    # Handle goto position
    if goto_line:
        target = f"{file_path}:{goto_line}"
        if goto_column:
            target = f"{target}:{goto_column}"
        args.extend(["--goto", target])
    else:
        args.append(file_path)

    result = _execute_antigravity(args)

    return {
        "success": result.success,
        "output": result.output or f"Opened {file_path}",
        "error": result.error,
        "file_path": file_path,
    }


def antigravity_diff(
    file1: str,
    file2: str,
) -> dict:
    """
    Compare two files using VS Code diff viewer.

    Args:
        file1: Path to first file
        file2: Path to second file

    Returns:
        Dict with operation result
    """
    # Validate both file paths
    for path, name in [(file1, "file1"), (file2, "file2")]:
        is_valid, message = validate_path_security(path)
        if not is_valid:
            return {
                "success": False,
                "output": "",
                "error": f"Invalid {name} path: {message}",
            }

        if not os.path.exists(path):
            return {
                "success": False,
                "output": "",
                "error": f"{name} does not exist: {path}",
            }

    args = ["--diff", file1, file2]

    result = _execute_antigravity(args)

    return {
        "success": result.success,
        "output": result.output or f"Comparing {file1} with {file2}",
        "error": result.error,
        "file1": file1,
        "file2": file2,
    }


def antigravity_list_extensions(
    show_versions: bool = False,
    category: Optional[str] = None,
) -> dict:
    """
    List installed VS Code extensions.

    Args:
        show_versions: Include version numbers in output
        category: Filter by extension category

    Returns:
        Dict with list of extensions
    """
    args = ["--list-extensions"]

    if show_versions:
        args.append("--show-versions")

    if category:
        args.extend(["--category", category])

    result = _execute_antigravity(args, timeout=60)

    # Parse extensions from output
    extensions = []
    if result.success and result.output:
        extensions = [
            ext.strip()
            for ext in result.output.split("\n")
            if ext.strip()
        ]

    return {
        "success": result.success,
        "extensions": extensions,
        "count": len(extensions),
        "error": result.error,
    }


def antigravity_add_folder(folder_path: str) -> dict:
    """
    Add a folder to the current VS Code workspace.

    Args:
        folder_path: Path to folder to add

    Returns:
        Dict with operation result
    """
    # Validate folder path
    is_valid, message = validate_path_security(folder_path)
    if not is_valid:
        return {
            "success": False,
            "output": "",
            "error": f"Invalid folder path: {message}",
        }

    if not os.path.isdir(folder_path):
        return {
            "success": False,
            "output": "",
            "error": f"Path is not a directory: {folder_path}",
        }

    args = ["--add", folder_path]

    result = _execute_antigravity(args)

    return {
        "success": result.success,
        "output": result.output or f"Added folder: {folder_path}",
        "error": result.error,
        "folder": folder_path,
    }


def antigravity_status() -> dict:
    """
    Get VS Code process status and diagnostics.

    Returns:
        Dict with status information
    """
    args = ["--status"]

    result = _execute_antigravity(args, timeout=60)

    return {
        "success": result.success,
        "status": result.output,
        "error": result.error,
    }


def get_antigravity_version() -> dict:
    """
    Get the installed Antigravity/VS Code CLI version.

    Returns:
        Dict with version info
    """
    try:
        antigravity_path = _get_antigravity_path()
        # SECURITY: shell=False with list args
        result = subprocess.run(
            [antigravity_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )

        version = result.stdout.strip() or result.stderr.strip()

        return {
            "success": True,
            "version": version,
            "path": antigravity_path,
        }
    except Exception as e:
        return {
            "success": False,
            "version": None,
            "error": str(e),
        }
