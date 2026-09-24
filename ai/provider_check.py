#!/usr/bin/env python3
"""
Provider diagnostic check for the QA Agent Harness AI Brain.

Usage:
    python3 -m ai.provider_check

Reports the current provider configuration, connection status, and
whether execution would be REAL_LLM or SIMULATED.
"""

from __future__ import annotations

import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.provider import (
    create_provider,
    is_ai_configured,
    NoOpProvider,
    OpenAIProvider,
    LocalProvider,
    parse_json_response,
)
from ai.config import build_ai_config


def check_provider() -> dict:
    """Run provider diagnostic and return result dict."""
    result: dict = {}

    # Load config
    cfg = build_ai_config()
    result["provider"] = cfg.provider
    result["model"] = cfg.model
    result["enabled"] = cfg.enabled
    result["ai_configured_env"] = is_ai_configured()

    # Create provider instance
    try:
        provider = create_provider(
            provider_name=cfg.provider,
            api_key=cfg.api_key,
            model=cfg.model,
            temperature=cfg.temperature,
            timeout_s=cfg.timeout_s,
        )
        result["provider_instance"] = type(provider).__name__
        result["provider_name"] = provider.name
        result["provider_model"] = provider.model
    except Exception as e:
        result["provider_instance"] = None
        result["provider_error"] = str(e)

    # Determine execution type
    if cfg.provider == "noop":
        result["execution_type"] = "SIMULATED"
        result["connection"] = "LOCAL"
    elif cfg.provider == "openai":
        if cfg.api_key:
            result["execution_type"] = "REAL_LLM"
            result["connection"] = "CONFIGURED"
            result["has_api_key"] = True
            # Don't expose key length or value
            result["api_key_configured"] = True
        else:
            result["execution_type"] = "BLOCKED"
            result["connection"] = "MISSING_KEY"
            result["has_api_key"] = False
            result["block_reason"] = (
                "AI provider is configured as OpenAI but OPENAI_API_KEY is missing. "
                "Set OPENAI_API_KEY or explicitly use AI_PROVIDER=noop."
            )
    elif cfg.provider == "local":
        if cfg.local_base_url:
            result["execution_type"] = "REAL_LLM"
            result["connection"] = "CONFIGURED"
            result["has_base_url"] = True
        else:
            result["execution_type"] = "BLOCKED"
            result["connection"] = "MISSING_BASE_URL"
            result["block_reason"] = (
                "AI provider is configured as local but LOCAL_LLM_BASE_URL is missing. "
                "Set LOCAL_LLM_BASE_URL or use AI_PROVIDER=noop."
            )
    else:
        result["execution_type"] = "UNKNOWN"
        result["connection"] = "UNKNOWN_PROVIDER"

    # Test NoOp canned response (always works)
    if cfg.provider == "noop":
        try:
            noop = NoOpProvider()
            test_result = noop.chat_completion([
                {"role": "system", "content": "test"},
                {"role": "user", "content": "hello"},
            ])
            result["noop_response_ok"] = test_result.get("content") is not None
            result["noop_content_length"] = len(test_result.get("content", ""))
        except Exception as e:
            result["noop_response_ok"] = False
            result["noop_error"] = str(e)

    # Test OpenAI connection (if key available)
    if cfg.provider == "openai" and cfg.api_key:
        try:
            from ai.provider import OpenAIProvider as OP
            test_provider = OP(api_key=cfg.api_key, model=cfg.model,
                               temperature=0.0, timeout_s=10.0)
            test_result = test_provider.chat_completion([
                {"role": "system", "content": "Reply with exactly: OK"},
                {"role": "user", "content": "test"},
            ])
            if test_result.get("error"):
                result["openai_connection"] = "FAILED"
                result["openai_error_type"] = test_result.get("error_type", "Unknown")
                # Sanitized error - never expose API key
                result["openai_error"] = test_result["error"][:200]
            else:
                result["openai_connection"] = "OK"
                result["openai_response_preview"] = test_result.get("content", "")[:100]
                parsed = parse_json_response(test_result.get("content", ""))
                result["openai_response_parsed"] = parsed is not None
        except Exception as e:
            result["openai_connection"] = "ERROR"
            result["openai_error"] = str(e)[:200]

    result["prompt_version"] = cfg.prompt_version

    return result


def main() -> None:
    """Print provider diagnostic report."""
    print("=" * 60)
    print("QA Agent Harness — AI Provider Diagnostic")
    print("=" * 60)
    print()

    result = check_provider()

    print(f"Provider:        {result.get('provider_instance', result.get('provider', 'unknown'))}")
    print(f"Model:           {result.get('model', 'unknown')}")
    print(f"Execution:       {result.get('execution_type', 'UNKNOWN')}")
    print(f"Connection:      {result.get('connection', 'UNKNOWN')}")
    print(f"Prompt Version:  {result.get('prompt_version', 'v1.0')}")
    print(f"AI Configured:   {result.get('ai_configured_env', False)}")
    print()

    if result.get("provider_error"):
        print(f"Provider Error:  {result['provider_error']}")
        print()

    if result.get("block_reason"):
        print(f"BLOCKED:         {result['block_reason']}")
        print()

    if result.get("has_api_key"):
        print("API Key:         Configured (not displayed for security)")
        print()

    if result.get("openai_connection"):
        print(f"OpenAI Connection: {result['openai_connection']}")
        if result.get("openai_response_preview"):
            print(f"Response:        {result['openai_response_preview']}")
        if result.get("openai_error"):
            print(f"Error:           {result['openai_error']}")
        print()

    if result.get("noop_response_ok"):
        print(f"NoOp Response:   OK ({result['noop_content_length']} chars)")
        print()

    print("=" * 60)
    print()

    # Final verdict
    exec_type = result.get("execution_type", "UNKNOWN")
    if exec_type == "REAL_LLM":
        print("VERDICT: REAL_LLM — A real LLM provider is configured and ready.")
        print("         Run with: python3 qa-run <story> --mode ai")
    elif exec_type == "SIMULATED":
        print("VERDICT: SIMULATED — Using NoOp (demo) provider.")
        print("         No real LLM calls will be made.")
        print("         Run with: python3 qa-run <story> --mode ai")
        print("         To use a real LLM, set AI_PROVIDER=openai and OPENAI_API_KEY.")
    elif exec_type == "BLOCKED":
        print("VERDICT: BLOCKED — AI provider is configured but missing required credentials.")
        print(f"         Reason: {result.get('block_reason', 'Unknown')}")
        print("         Fix the configuration or use AI_PROVIDER=noop.")
        sys.exit(1)
    else:
        print(f"VERDICT: {exec_type}")


if __name__ == "__main__":
    main()
