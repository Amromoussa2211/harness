#!/usr/bin/env python3
"""
AI Configuration — loads AI settings from environment and project.yaml.

Configuration precedence:
  1. Environment variables (AI_PROVIDER, AI_MODEL, AI_API_KEY, ...)
  2. project.yaml ai: section
  3. Defaults (disabled, noop provider)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIConfig:
    """Configuration for the AI engine."""
    enabled: bool = False
    provider: str = "noop"
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    timeout_s: float = 60.0
    max_tokens: int = 4096
    api_key: str = ""
    base_url: str = ""
    local_base_url: str = ""
    local_model: str = ""
    local_api_key: str = ""
    prompt_version: str = "v1.0"
    system_prompt_dir: str = "ai/prompts"
    max_retries: int = 1
    retry_delay_s: float = 2.0
    run_id: str = ""  # set per-run
    story_id: str = ""
    project_name: str = ""

    @property
    def is_real_provider(self) -> bool:
        """Return True if a real LLM provider (not noop) is configured."""
        return self.provider.lower() not in ("", "noop", "false", "disabled")

    @property
    def effective_api_key(self) -> str:
        """Resolve API key: explicit > env > project config."""
        if self.api_key:
            return self.api_key
        if self.provider.lower() == "openai":
            return os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        if self.provider.lower() == "local":
            return os.environ.get("LOCAL_LLM_API_KEY", "")
        return ""


def load_ai_config_from_env() -> dict[str, Any]:
    """Load AI configuration from environment variables."""
    return {
        "enabled": _env_bool("AI_ENABLED", "false"),
        "provider": os.environ.get("AI_PROVIDER", "").strip() or "noop",
        "model": os.environ.get("AI_MODEL", "gpt-4o-mini"),
        "temperature": float(os.environ.get("AI_TEMPERATURE", "0.3")),
        "timeout_s": float(os.environ.get("AI_TIMEOUT_S", "60.0")),
        "max_tokens": int(os.environ.get("AI_MAX_TOKENS", "4096")),
        "api_key": os.environ.get("AI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", ""),
        "base_url": os.environ.get("AI_BASE_URL", ""),
        "local_base_url": os.environ.get("LOCAL_LLM_BASE_URL", ""),
        "local_model": os.environ.get("LOCAL_LLM_MODEL", ""),
        "local_api_key": os.environ.get("LOCAL_LLM_API_KEY", ""),
        "prompt_version": os.environ.get("AI_PROMPT_VERSION", "v1.0"),
        "max_retries": int(os.environ.get("AI_MAX_RETRIES", "1")),
        "retry_delay_s": float(os.environ.get("AI_RETRY_DELAY_S", "2.0")),
    }


def _env_bool(name: str, default: str) -> bool:
    """Parse a boolean from an environment variable."""
    val = os.environ.get(name, default).lower().strip()
    return val in ("1", "true", "yes", "on")


def load_ai_config_from_project_yaml(project_config: dict) -> dict[str, Any]:
    """Extract AI config from a project.yaml dict."""
    ai_section = project_config.get("ai", {})
    if not ai_section:
        return {}

    return {
        "enabled": bool(ai_section.get("enabled", False)),
        "provider": str(ai_section.get("provider", "openai")).strip().lower(),
        "model": str(ai_section.get("model", "gpt-4o-mini")),
        "temperature": float(ai_section.get("temperature", 0.3)),
        "timeout_s": float(ai_section.get("timeout_s", 60.0)),
        "max_tokens": int(ai_section.get("max_tokens", 4096)),
        "api_key": ai_section.get("api_key", ""),  # never use from yaml
        "base_url": ai_section.get("base_url", ""),
        "local_base_url": ai_section.get("local_base_url", ""),
        "local_model": ai_section.get("local_model", ""),
        "local_api_key": ai_section.get("local_api_key", ""),
        "prompt_version": str(ai_section.get("prompt_version", "v1.0")),
        "max_retries": int(ai_section.get("max_retries", 1)),
        "retry_delay_s": float(ai_section.get("retry_delay_s", 2.0)),
    }


def merge_ai_config(env_config: dict, yaml_config: dict) -> dict[str, Any]:
    """
    Merge AI configuration from env vars and project.yaml.

    Environment variables take precedence over project.yaml.
    Secrets from yaml are ignored (env only).
    """
    merged: dict[str, Any] = {}
    all_keys = set(env_config.keys()) | set(yaml_config.keys())

    for key in all_keys:
        env_val = env_config.get(key)
        yaml_val = yaml_config.get(key)

        if key in ("api_key", "local_api_key"):
            # Secrets: env only, never from yaml
            merged[key] = env_val if env_val else ""
        elif env_val is not None and env_val != "":
            merged[key] = env_val
        elif yaml_val is not None and yaml_val != "":
            merged[key] = yaml_val
        else:
            merged[key] = env_val if env_val is not None else yaml_val if yaml_val is not None else \
                (True if key == "enabled" else "gpt-4o-mini" if key == "model" else
                 0.3 if key == "temperature" else 60.0 if key == "timeout_s" else
                 4096 if key == "max_tokens" else 1 if key == "max_retries" else 2.0)

    # Special handling for enabled: env overrides everything
    if env_config.get("enabled"):
        merged["enabled"] = True
    elif not env_config.get("enabled") and yaml_config.get("enabled"):
        # Env says false/empty but yaml says true -> env wins (explicit disable)
        merged["enabled"] = False

    return merged


def build_ai_config(project_config: dict | None = None,
                     story_id: str = "",
                     project_name: str = "",
                     run_id: str = "") -> AIConfig:
    """
    Build the complete AIConfig from environment + project.yaml.

    Environment variables take precedence. Secrets come from env only.
    """
    env_cfg = load_ai_config_from_env()
    yaml_cfg = load_ai_config_from_project_yaml(project_config) if project_config else {}

    merged = merge_ai_config(env_cfg, yaml_cfg)

    # Override model for noop provider to always report noop-demo
    if merged.get("provider", "").lower() == "noop":
        merged["model"] = "noop-demo"

    return AIConfig(
        enabled=merged.get("enabled", False),
        provider=merged.get("provider", "noop"),
        model=merged.get("model", "gpt-4o-mini"),
        temperature=merged.get("temperature", 0.3),
        timeout_s=merged.get("timeout_s", 60.0),
        max_tokens=merged.get("max_tokens", 4096),
        api_key=merged.get("api_key", ""),
        base_url=merged.get("base_url", ""),
        local_base_url=merged.get("local_base_url", ""),
        local_model=merged.get("local_model", ""),
        local_api_key=merged.get("local_api_key", ""),
        prompt_version=merged.get("prompt_version", "v1.0"),
        max_retries=merged.get("max_retries", 1),
        retry_delay_s=merged.get("retry_delay_s", 2.0),
        run_id=run_id,
        story_id=story_id,
        project_name=project_name,
    )
