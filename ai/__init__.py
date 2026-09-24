#!/usr/bin/env python3
"""AI Brain package for the QA Agent Harness."""

# Import agent modules to trigger @register_agent decorators
from ai.agents import stage_agents  # noqa: F401
from ai.agents import test_agents    # noqa: F401

from ai.provider import (
    LLMProvider, OpenAIProvider, LocalProvider, NoOpProvider,
    create_provider, is_ai_configured,
    parse_json_response, TokenUsage, ProviderStats,
)
from ai.config import (
    AIConfig, load_ai_config_from_env, load_ai_config_from_project_yaml,
    merge_ai_config, build_ai_config,
)
from ai.agent import (
    BaseAIAgent, AgentResponse, AIRunMetadata, AgentOutputValidator,
    run_agent_with_retry, AGENT_REGISTRY, get_agent, register_agent,
)
from ai.context import (
    ContextBlock, AgentContext, ContextBuilder,
)
from ai.engine import AIEngine, AIEngineResult

__all__ = [
    # Provider
    "LLMProvider", "OpenAIProvider", "LocalProvider", "NoOpProvider",
    "create_provider", "is_ai_configured", "build_effective_config",
    "parse_json_response", "TokenUsage", "ProviderStats",
    "LOCAL_PROVIDER_ENV", "DEFAULT_OPENAI_MODEL", "DEFAULT_LOCAL_MODEL",
    # Config
    "AIConfig", "load_ai_config_from_env", "load_ai_config_from_project_yaml",
    "merge_ai_config", "build_ai_config",
    # Agent
    "BaseAIAgent", "AgentResponse", "AIRunMetadata", "AgentOutputValidator",
    "run_agent_with_retry", "AGENT_REGISTRY", "get_agent", "register_agent",
    # Context
    "ContextBlock", "AgentContext", "ContextBuilder",
    # Engine
    "AIEngine", "AIEngineResult",
]
