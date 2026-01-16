"""
Configuration Module for Multi-AI MCP Server

Provides Pydantic-based settings management.
"""

from .settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
]
