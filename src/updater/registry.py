"""
CLI Tool Registry

Centralized registry for all managed CLI tools with their paths,
version commands, and update commands.
"""

import os
import shutil
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


class PackageManager(Enum):
    """Package manager types."""
    NPM = "npm"
    HOMEBREW = "homebrew"
    CUSTOM = "custom"


@dataclass
class CLITool:
    """Configuration for a CLI tool."""
    name: str
    display_name: str
    package_name: str  # npm package or homebrew formula
    package_manager: PackageManager
    default_path: str
    version_args: list[str] = field(default_factory=lambda: ["--version"])
    version_parser: Optional[Callable[[str], str]] = None
    update_command: Optional[list[str]] = None

    def get_path(self) -> Optional[str]:
        """Get the actual path to the CLI tool."""
        # Check environment variable override
        env_key = f"{self.name.upper()}_CLI_PATH"
        env_path = os.environ.get(env_key)
        if env_path and os.path.exists(env_path):
            return env_path

        # Check default path
        if os.path.exists(self.default_path):
            return self.default_path

        # Try to find in PATH
        which_path = shutil.which(self.name)
        if which_path:
            return which_path

        return None

    def is_installed(self) -> bool:
        """Check if the tool is installed."""
        return self.get_path() is not None


# Default version parser (extracts first version-like string)
def _default_version_parser(output: str) -> str:
    """Extract version from CLI output."""
    import re
    # Match semver-like patterns
    match = re.search(r"(\d+\.\d+\.\d+)", output)
    if match:
        return match.group(1)
    return output.strip().split("\n")[0]


# Registry of all managed CLI tools
CLI_REGISTRY: dict[str, CLITool] = {
    "claude": CLITool(
        name="claude",
        display_name="Claude CLI",
        package_name="@anthropic-ai/claude-code",
        package_manager=PackageManager.NPM,
        default_path="/Users/rush/.nvm/versions/node/v24.11.1/bin/claude",
        version_parser=_default_version_parser,
    ),

    "codex": CLITool(
        name="codex",
        display_name="Codex CLI",
        package_name="@openai/codex",
        package_manager=PackageManager.NPM,
        default_path="/Users/rush/.nvm/versions/node/v24.11.1/bin/codex",
        version_parser=_default_version_parser,
    ),

    "gemini": CLITool(
        name="gemini",
        display_name="Gemini CLI",
        package_name="@anthropic-ai/gemini-cli",  # Or the correct package name
        package_manager=PackageManager.NPM,
        default_path="/opt/homebrew/bin/gemini",
        version_parser=_default_version_parser,
    ),

    "antigravity": CLITool(
        name="antigravity",
        display_name="Antigravity CLI (VS Code)",
        package_name="antigravity",
        package_manager=PackageManager.CUSTOM,
        default_path="/Users/rush/.antigravity/antigravity/bin/antigravity",
        version_parser=_default_version_parser,
    ),
}


def get_tool(name: str) -> Optional[CLITool]:
    """Get a CLI tool from the registry."""
    return CLI_REGISTRY.get(name.lower())


def get_all_tools() -> dict[str, CLITool]:
    """Get all registered CLI tools."""
    return CLI_REGISTRY.copy()


def get_installed_tools() -> dict[str, CLITool]:
    """Get only installed CLI tools."""
    return {
        name: tool
        for name, tool in CLI_REGISTRY.items()
        if tool.is_installed()
    }


def add_tool(tool: CLITool) -> None:
    """Add a new tool to the registry."""
    CLI_REGISTRY[tool.name.lower()] = tool


def remove_tool(name: str) -> bool:
    """Remove a tool from the registry."""
    if name.lower() in CLI_REGISTRY:
        del CLI_REGISTRY[name.lower()]
        return True
    return False
