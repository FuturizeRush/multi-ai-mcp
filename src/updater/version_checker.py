"""
Version Checker and Updater

Provides functionality to check CLI tool versions and update them.
Note: Uses subprocess with shell=False for safe execution.
"""

import subprocess
import json
import logging
from typing import Optional
from dataclasses import dataclass

from .registry import CLI_REGISTRY, CLITool, PackageManager, get_tool

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """Version information for a CLI tool."""
    name: str
    current_version: Optional[str]
    latest_version: Optional[str]
    update_available: bool
    path: Optional[str]
    error: Optional[str] = None


def _get_current_version(tool: CLITool) -> tuple[Optional[str], Optional[str]]:
    """
    Get the current installed version of a CLI tool.

    Returns:
        Tuple of (version, error)
    """
    path = tool.get_path()
    if not path:
        return None, f"{tool.display_name} not installed"

    try:
        cmd = [path] + tool.version_args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,  # SECURITY: prevent shell injection
        )

        output = result.stdout.strip() or result.stderr.strip()

        if tool.version_parser:
            version = tool.version_parser(output)
        else:
            version = output

        return version, None

    except subprocess.TimeoutExpired:
        return None, "Version check timed out"
    except Exception as e:
        return None, str(e)


def _get_npm_latest_version(package_name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Get the latest version of an npm package.

    Returns:
        Tuple of (version, error)
    """
    try:
        result = subprocess.run(
            ["npm", "view", package_name, "version"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,  # SECURITY: prevent shell injection
        )

        if result.returncode == 0:
            return result.stdout.strip(), None
        else:
            return None, result.stderr.strip() or "Failed to query npm registry"

    except subprocess.TimeoutExpired:
        return None, "npm registry query timed out"
    except FileNotFoundError:
        return None, "npm command not found"
    except Exception as e:
        return None, str(e)


def _compare_versions(current: str, latest: str) -> bool:
    """
    Compare two semver versions.

    Returns:
        True if latest is newer than current
    """
    try:
        from packaging import version
        return version.parse(latest) > version.parse(current)
    except ImportError:
        # Fallback: simple string comparison (less accurate)
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]

        for c, l in zip(current_parts, latest_parts):
            if l > c:
                return True
            if l < c:
                return False

        return len(latest_parts) > len(current_parts)
    except Exception:
        # If parsing fails, assume update is available
        return current != latest


def check_version(tool_name: str) -> VersionInfo:
    """
    Check the version of a specific CLI tool.

    Args:
        tool_name: Name of the tool to check

    Returns:
        VersionInfo with current and latest version information
    """
    tool = get_tool(tool_name)
    if not tool:
        return VersionInfo(
            name=tool_name,
            current_version=None,
            latest_version=None,
            update_available=False,
            path=None,
            error=f"Unknown tool: {tool_name}",
        )

    # Get current version
    current, error = _get_current_version(tool)
    if error:
        return VersionInfo(
            name=tool.name,
            current_version=None,
            latest_version=None,
            update_available=False,
            path=tool.get_path(),
            error=error,
        )

    # Get latest version based on package manager
    latest = None
    if tool.package_manager == PackageManager.NPM:
        latest, error = _get_npm_latest_version(tool.package_name)

    # Check if update is available
    update_available = False
    if current and latest:
        update_available = _compare_versions(current, latest)

    return VersionInfo(
        name=tool.name,
        current_version=current,
        latest_version=latest,
        update_available=update_available,
        path=tool.get_path(),
        error=error,
    )


def check_all_versions() -> dict[str, VersionInfo]:
    """
    Check versions for all registered CLI tools.

    Returns:
        Dict mapping tool names to their VersionInfo
    """
    results = {}
    for name in CLI_REGISTRY:
        results[name] = check_version(name)
    return results


def update_tool(tool_name: str, force: bool = False) -> dict:
    """
    Update a CLI tool to the latest version.

    Args:
        tool_name: Name of the tool to update
        force: Force update even if already at latest

    Returns:
        Dict with update result
    """
    tool = get_tool(tool_name)
    if not tool:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
        }

    # Check current version
    version_info = check_version(tool_name)

    if not version_info.update_available and not force:
        return {
            "success": True,
            "message": f"{tool.display_name} is already at latest version ({version_info.current_version})",
            "current_version": version_info.current_version,
            "updated": False,
        }

    # Perform update based on package manager
    if tool.package_manager == PackageManager.NPM:
        return _update_npm_tool(tool, force)
    elif tool.package_manager == PackageManager.HOMEBREW:
        return _update_homebrew_tool(tool)
    else:
        return {
            "success": False,
            "error": f"Auto-update not supported for {tool.display_name}. Please update manually.",
        }


def _update_npm_tool(tool: CLITool, force: bool = False) -> dict:
    """Update an npm-based CLI tool."""
    try:
        cmd = ["npm", "install", "-g", tool.package_name]
        if force:
            cmd.append("--force")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes for install
            shell=False,  # SECURITY: prevent shell injection
        )

        if result.returncode == 0:
            # Check new version
            new_version_info = check_version(tool.name)
            return {
                "success": True,
                "message": f"Updated {tool.display_name} to {new_version_info.current_version}",
                "current_version": new_version_info.current_version,
                "updated": True,
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip() or "Update failed",
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Update timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _update_homebrew_tool(tool: CLITool) -> dict:
    """Update a Homebrew-based CLI tool."""
    try:
        cmd = ["brew", "upgrade", tool.package_name]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes for brew
            shell=False,  # SECURITY: prevent shell injection
        )

        if result.returncode == 0:
            new_version_info = check_version(tool.name)
            return {
                "success": True,
                "message": f"Updated {tool.display_name} to {new_version_info.current_version}",
                "current_version": new_version_info.current_version,
                "updated": True,
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip() or "Update failed",
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Update timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
