"""
Settings Configuration

Pydantic-based settings for the Multi-AI MCP Server.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Claude CLI settings
    claude_cli_path: str = Field(
        default="/Users/rush/.nvm/versions/node/v24.11.1/bin/claude",
        description="Path to Claude CLI executable"
    )
    claude_default_model: str = Field(
        default="sonnet",
        description="Default Claude model (sonnet/opus/haiku)"
    )
    claude_timeout: int = Field(
        default=300,
        description="Default timeout for Claude operations (seconds)"
    )

    # Codex CLI settings
    codex_cli_path: str = Field(
        default="/Users/rush/.nvm/versions/node/v24.11.1/bin/codex",
        description="Path to Codex CLI executable"
    )
    codex_default_model: str = Field(
        default="o4-mini",
        description="Default Codex model"
    )
    codex_timeout: int = Field(
        default=300,
        description="Default timeout for Codex operations (seconds)"
    )

    # Gemini CLI settings
    gemini_cli_path: str = Field(
        default="/opt/homebrew/bin/gemini",
        description="Path to Gemini CLI executable"
    )
    gemini_timeout: int = Field(
        default=300,
        description="Default timeout for Gemini operations (seconds)"
    )

    # Antigravity CLI settings
    antigravity_cli_path: str = Field(
        default="/Users/rush/.antigravity/antigravity/bin/antigravity",
        description="Path to Antigravity CLI executable"
    )
    antigravity_timeout: int = Field(
        default=30,
        description="Default timeout for Antigravity operations (seconds)"
    )

    # Security settings
    max_prompt_length: int = Field(
        default=100000,
        description="Maximum allowed prompt length"
    )
    enable_prompt_injection_filter: bool = Field(
        default=True,
        description="Enable prompt injection detection"
    )
    enable_path_validation: bool = Field(
        default=True,
        description="Enable path security validation"
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG/INFO/WARNING/ERROR)"
    )
    log_api_keys: bool = Field(
        default=False,
        description="Log API keys (DANGEROUS - only for debugging)"
    )

    # API Keys (optional, for API fallback)
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for Codex"
    )
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google API key for Gemini"
    )

    class Config:
        env_prefix = "MULTI_AI_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
