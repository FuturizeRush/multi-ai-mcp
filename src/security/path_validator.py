"""
Path Security Validation

This module provides security functions to validate file paths and prevent
directory traversal attacks and access to sensitive system locations.
"""

import os
from pathlib import Path
from typing import Optional

# System paths that should never be accessed
BLOCKED_PATHS = [
    "/etc/",
    "/proc/",
    "/sys/",
    "/dev/",
    "/boot/",
    "/root/",
    "/var/log/",
    "/private/etc/",    # macOS
    "/private/var/",    # macOS
    "/System/",         # macOS
    "/Library/",        # macOS system library
    "C:\\Windows\\",    # Windows
    "C:\\System32\\",   # Windows
]

# Sensitive file patterns
SENSITIVE_PATTERNS = [
    ".env",
    ".ssh",
    "id_rsa",
    "id_ed25519",
    ".aws/credentials",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "token.json",
    ".git/config",
    "shadow",
    "passwd",
    "sudoers",
]


def is_path_blocked(path: str) -> tuple[bool, Optional[str]]:
    """
    Check if a path is in a blocked system location.

    Args:
        path: The path to check

    Returns:
        Tuple of (is_blocked, reason)
        - is_blocked: True if path is in blocked location
        - reason: Description of why path is blocked, or None
    """
    if not path:
        return True, "Empty path"

    # Normalize the path
    try:
        normalized = os.path.normpath(os.path.expanduser(path))
        absolute = os.path.abspath(normalized)
    except (ValueError, OSError) as e:
        return True, f"Invalid path: {e}"

    # Check against blocked paths
    for blocked in BLOCKED_PATHS:
        if absolute.startswith(blocked) or normalized.startswith(blocked):
            return True, f"Access to system path blocked: {blocked}"

    return False, None


def is_path_sensitive(path: str) -> tuple[bool, Optional[str]]:
    """
    Check if a path points to a sensitive file.

    Args:
        path: The path to check

    Returns:
        Tuple of (is_sensitive, reason)
        - is_sensitive: True if path is sensitive
        - reason: Description of sensitivity, or None
    """
    if not path:
        return False, None

    normalized = os.path.normpath(path).lower()
    basename = os.path.basename(normalized)

    for pattern in SENSITIVE_PATTERNS:
        if pattern.lower() in normalized or pattern.lower() == basename:
            return True, f"Sensitive file pattern detected: {pattern}"

    return False, None


def validate_path_security(
    path: str,
    base_dir: Optional[str] = None,
    allow_sensitive: bool = False
) -> tuple[bool, str]:
    """
    Comprehensive path security validation.

    Args:
        path: The path to validate
        base_dir: Optional base directory to restrict access within
        allow_sensitive: Whether to allow access to sensitive files

    Returns:
        Tuple of (is_valid, message)
        - is_valid: True if path passes all security checks
        - message: Description of validation result
    """
    if not path:
        return False, "Empty path"

    # Check for path traversal attempts
    if ".." in path:
        # Resolve and check if it escapes intended directory
        try:
            resolved = os.path.realpath(os.path.expanduser(path))
        except (ValueError, OSError) as e:
            return False, f"Path resolution failed: {e}"

        if base_dir:
            base_resolved = os.path.realpath(os.path.expanduser(base_dir))
            if not resolved.startswith(base_resolved):
                return False, "Path traversal detected: path escapes base directory"

    # Check blocked paths
    is_blocked, reason = is_path_blocked(path)
    if is_blocked:
        return False, reason

    # Check sensitive files (unless explicitly allowed)
    if not allow_sensitive:
        is_sensitive, reason = is_path_sensitive(path)
        if is_sensitive:
            return False, f"Access to sensitive file denied: {reason}"

    # Base directory constraint
    if base_dir:
        try:
            path_resolved = os.path.realpath(os.path.expanduser(path))
            base_resolved = os.path.realpath(os.path.expanduser(base_dir))

            if not path_resolved.startswith(base_resolved):
                return False, "Path is outside allowed base directory"
        except (ValueError, OSError) as e:
            return False, f"Path validation failed: {e}"

    return True, "Path passed security validation"


def get_safe_working_dir(
    requested_dir: Optional[str] = None,
    fallback_dir: Optional[str] = None
) -> str:
    """
    Get a safe working directory, with validation.

    Args:
        requested_dir: User-requested working directory
        fallback_dir: Directory to use if requested is invalid

    Returns:
        A validated, safe working directory path

    Raises:
        ValueError: If no valid working directory can be determined
    """
    # Try requested directory first
    if requested_dir:
        is_valid, _ = validate_path_security(requested_dir)
        if is_valid and os.path.isdir(requested_dir):
            return os.path.realpath(os.path.expanduser(requested_dir))

    # Try fallback
    if fallback_dir:
        is_valid, _ = validate_path_security(fallback_dir)
        if is_valid and os.path.isdir(fallback_dir):
            return os.path.realpath(os.path.expanduser(fallback_dir))

    # Use current directory
    cwd = os.getcwd()
    is_valid, _ = validate_path_security(cwd)
    if is_valid:
        return cwd

    # Last resort: home directory
    home = os.path.expanduser("~")
    return home


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe filesystem use.

    Args:
        filename: The filename to sanitize

    Returns:
        A safe filename with dangerous characters removed
    """
    if not filename:
        return "unnamed"

    # Remove path components
    basename = os.path.basename(filename)

    # Remove dangerous characters
    dangerous_chars = '<>:"/\\|?*\x00'
    for char in dangerous_chars:
        basename = basename.replace(char, '_')

    # Remove leading/trailing whitespace and dots
    basename = basename.strip('. \t\n\r')

    # Ensure non-empty
    if not basename:
        return "unnamed"

    # Limit length
    if len(basename) > 255:
        name, ext = os.path.splitext(basename)
        basename = name[:255 - len(ext)] + ext

    return basename
