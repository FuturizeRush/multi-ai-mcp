"""
Updater Module for Multi-AI MCP Server

Provides version checking and update functionality for CLI tools.
"""

from .registry import (
    CLI_REGISTRY,
    CLITool,
    PackageManager,
    get_tool,
    get_all_tools,
    get_installed_tools,
    add_tool,
    remove_tool,
)

from .version_checker import (
    VersionInfo,
    check_version,
    check_all_versions,
    update_tool,
)

__all__ = [
    # Registry
    "CLI_REGISTRY",
    "CLITool",
    "PackageManager",
    "get_tool",
    "get_all_tools",
    "get_installed_tools",
    "add_tool",
    "remove_tool",
    # Version checker
    "VersionInfo",
    "check_version",
    "check_all_versions",
    "update_tool",
]
