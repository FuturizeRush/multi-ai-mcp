"""
Multi-AI MCP Server

A unified MCP server providing access to multiple AI CLI tools.
"""

__version__ = "1.0.0"

from .server import mcp, main

__all__ = ["mcp", "main", "__version__"]
