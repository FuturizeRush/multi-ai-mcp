"""
Security Module for Multi-AI MCP Server

Provides sanitization and path validation utilities for safe CLI execution.
"""

from .sanitizer import (
    sanitize_for_prompt,
    mask_api_keys,
    detect_injection,
    validate_prompt_safety,
    escape_for_shell,
    MAX_PROMPT_LENGTH,
)

from .path_validator import (
    validate_path_security,
    is_path_blocked,
    is_path_sensitive,
    get_safe_working_dir,
    sanitize_filename,
)

__all__ = [
    # Sanitizer
    "sanitize_for_prompt",
    "mask_api_keys",
    "detect_injection",
    "validate_prompt_safety",
    "escape_for_shell",
    "MAX_PROMPT_LENGTH",
    # Path validator
    "validate_path_security",
    "is_path_blocked",
    "is_path_sensitive",
    "get_safe_working_dir",
    "sanitize_filename",
]
