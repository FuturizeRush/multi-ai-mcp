"""
Prompt Injection Protection and Input Sanitization

This module provides security functions to prevent prompt injection attacks
and sanitize user inputs before passing them to AI CLI tools.
"""

import re
from typing import Optional

# Maximum allowed prompt length (characters)
MAX_PROMPT_LENGTH = 100_000

# Patterns that indicate potential prompt injection attempts
DANGEROUS_PATTERNS = [
    # Instruction override attempts
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",

    # System prompt extraction
    r"(show|reveal|display|print|output)\s+(me\s+)?(your\s+)?(system\s+)?(prompt|instructions?)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?)",

    # Role manipulation
    r"you\s+are\s+now\s+a",
    r"pretend\s+(to\s+be|you\s+are)",
    r"act\s+as\s+(if\s+you\s+are|a)",
    r"roleplay\s+as",

    # Jailbreak attempts
    r"DAN\s+mode",
    r"developer\s+mode",
    r"jailbreak",

    # Delimiter injection
    r"```\s*system",
    r"\[SYSTEM\]",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
]

# Compiled regex patterns for efficiency
_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

# Patterns for API key detection (for masking in logs)
API_KEY_PATTERNS = [
    r"(sk-[a-zA-Z0-9]{20,})",           # OpenAI-style keys
    r"(ghp_[a-zA-Z0-9]{36,})",          # GitHub PAT
    r"(gho_[a-zA-Z0-9]{36,})",          # GitHub OAuth
    r"(AIza[a-zA-Z0-9_-]{35})",         # Google API keys
    r"(ya29\.[a-zA-Z0-9_-]+)",          # Google OAuth tokens
    r"(AKIA[A-Z0-9]{16})",              # AWS Access Key
    r"(xox[baprs]-[a-zA-Z0-9-]+)",      # Slack tokens
    r"(Bearer\s+[a-zA-Z0-9._-]+)",      # Bearer tokens
]

_compiled_api_patterns = [re.compile(p) for p in API_KEY_PATTERNS]


def detect_injection(text: str) -> tuple[bool, Optional[str]]:
    """
    Detect potential prompt injection patterns in text.

    Args:
        text: The input text to check

    Returns:
        Tuple of (is_dangerous, matched_pattern)
        - is_dangerous: True if injection pattern detected
        - matched_pattern: The pattern that was matched, or None
    """
    if not text:
        return False, None

    for pattern in _compiled_patterns:
        match = pattern.search(text)
        if match:
            return True, match.group(0)

    return False, None


def sanitize_for_prompt(text: str, max_length: int = MAX_PROMPT_LENGTH) -> str:
    """
    Sanitize text for safe use in prompts.

    This function:
    1. Validates length constraints
    2. Removes or escapes potentially dangerous patterns
    3. Normalizes whitespace

    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length (default: 100,000)

    Returns:
        Sanitized text safe for prompt use

    Raises:
        ValueError: If text exceeds maximum length after sanitization
    """
    if not text:
        return ""

    # Strip and normalize whitespace
    sanitized = " ".join(text.split())

    # Check length
    if len(sanitized) > max_length:
        raise ValueError(
            f"Input exceeds maximum length: {len(sanitized)} > {max_length}"
        )

    # Check for injection patterns
    is_dangerous, pattern = detect_injection(sanitized)
    if is_dangerous:
        # Log the attempt (pattern only, not full text)
        import logging
        logging.warning(f"Potential prompt injection detected: '{pattern}'")

        # Remove the dangerous pattern
        for compiled in _compiled_patterns:
            sanitized = compiled.sub("[FILTERED]", sanitized)

    return sanitized


def mask_api_keys(text: str) -> str:
    """
    Mask API keys and tokens in text for safe logging.

    Args:
        text: Text that may contain API keys

    Returns:
        Text with API keys replaced by [MASKED_KEY]
    """
    if not text:
        return ""

    masked = text
    for pattern in _compiled_api_patterns:
        masked = pattern.sub("[MASKED_KEY]", masked)

    return masked


def validate_prompt_safety(prompt: str) -> tuple[bool, str]:
    """
    Comprehensive safety validation for prompts.

    Args:
        prompt: The prompt to validate

    Returns:
        Tuple of (is_safe, message)
        - is_safe: True if prompt passes all checks
        - message: Description of validation result
    """
    if not prompt:
        return False, "Empty prompt"

    if len(prompt) > MAX_PROMPT_LENGTH:
        return False, f"Prompt exceeds maximum length ({MAX_PROMPT_LENGTH} chars)"

    is_dangerous, pattern = detect_injection(prompt)
    if is_dangerous:
        return False, f"Potential injection pattern detected: '{pattern}'"

    return True, "Prompt passed safety validation"


def escape_for_shell(text: str) -> str:
    """
    Escape text for safe shell argument use.

    Note: This is a secondary defense. Primary protection comes from
    using shell=False in subprocess calls.

    Args:
        text: Text to escape

    Returns:
        Shell-safe escaped text
    """
    if not text:
        return ""

    # Replace characters that have special meaning in shells
    dangerous_chars = {
        '`': r'\`',
        '$': r'\$',
        '\\': r'\\',
        '"': r'\"',
        "'": r"\'",
        ';': r'\;',
        '&': r'\&',
        '|': r'\|',
        '<': r'\<',
        '>': r'\>',
        '(': r'\(',
        ')': r'\)',
        '{': r'\{',
        '}': r'\}',
        '\n': ' ',
        '\r': ' ',
    }

    result = text
    for char, escaped in dangerous_chars.items():
        result = result.replace(char, escaped)

    return result
