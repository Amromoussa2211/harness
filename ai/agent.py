#!/usr/bin/env python3
"""
AI Agent Framework — base classes, structured output contracts, and validation
for the QA Agent Harness AI Brain.

Every AI agent:
  - Has a role, prompt version, input contract, output contract
  - Receives context via a ContextBuilder
  - Returns structured JSON output validated against a schema
  - Records prompt version, model, provider, and timing metadata
  - On failure: retries once, then routes to Failure Analysis
"""

from __future__ import annotations

import json
import os
import time
import sys
from dataclasses import dataclass, field
from typing import Any, Callable

from ai.provider import (
    LLMProvider, create_provider, is_ai_configured, parse_json_response,
    TokenUsage, ProviderStats,
)


# ── Run metadata ──────────────────────────────────────────────────────────────

@dataclass
class AIRunMetadata:
    """Metadata for a single AI-enabled run."""
    run_id: str
    story_id: str
    project_name: str
    mode: str = "ai"
    provider: str = "noop"
    model: str = "unknown"
    prompt_version: str = "v1.0"
    timestamp: str = ""
    config_source: str = "env"  # env, yaml, or env+yaml
    input_artifacts: list[str] = field(default_factory=list)
    output_artifacts: list[str] = field(default_factory=list)
    agent_results: list[dict] = field(default_factory=list)
    total_duration_ms: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_usd: float = 0.0
    provider_stats: ProviderStats = field(default_factory=ProviderStats)
    is_deterministic: bool = False


# ── Agent response contract ───────────────────────────────────────────────────

@dataclass
class AgentResponse:
    """Standardized response from an AI agent."""
    agent_name: str
    agent_role: str
    prompt_version: str
    provider: str
    model: str
    status: str = "success"  # success, retry, failed
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    output: dict = field(default_factory=dict)  # validated structured output
    raw_output: str = ""  # raw LLM response (for diagnosis)
    error: str = ""
    error_type: str = ""
    retry_count: int = 0
    input_artifact_refs: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# ── Output validation ─────────────────────────────────────────────────────────

class AgentOutputValidator:
    """Validate agent output against expected structure."""

    @staticmethod
    def validate(obj: dict, required_fields: list[str], optional_fields: list[str] = None) -> tuple[bool, list[str]]:
        """
        Validate that a dict contains required fields.

        Returns (is_valid, list_of_errors).
        """
        errors = []
        for field_name in required_fields:
            if field_name not in obj:
                errors.append(f"Missing required field: '{field_name}'")
            elif obj[field_name] is None:
                errors.append(f"Required field '{field_name}' is null")

        if optional_fields:
            for field_name in optional_fields:
                if field_name in obj and obj[field_name] is None:
                    errors.append(f"Optional field '{field_name}' is null when present")

        # Check for empty collections where data is expected
        for field_name in required_fields:
            val = obj.get(field_name)
            if isinstance(val, list) and len(val) == 0 and field_name in ("findings", "risks", "questions", "recommendations"):
                # Empty lists are acceptable for some fields
                pass

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_analyst_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, [
            "summary", "actors", "inputs", "outputs", "acceptance_criteria",
            "ambiguities", "missing_requirements", "dependencies", "assumptions",
            "unknowns", "questions", "confidence"
        ])

    @staticmethod
    def validate_grill_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, [
            "questions", "ambiguities_found", "missing_requirements",
            "risk_flags", "clarification_needed"
        ])

    @staticmethod
    def validate_risk_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, ["risks", "summary"])

    @staticmethod
    def validate_architect_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, ["test_strategy", "rationale", "recommendations"])

    @staticmethod
    def validate_specification_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, ["specifications", "traceability"])

    @staticmethod
    def validate_test_design_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, ["scenarios", "scenario_count", "coverage_summary"])

    @staticmethod
    def validate_test_generator_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, [
            "generated_specs", "spec_count", "spec_paths",
            "traceability", "validation_notes"
        ])

    @staticmethod
    def validate_failure_analysis_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, [
            "failures", "failure_count", "classifications",
            "root_causes", "recommended_actions"
        ])

    @staticmethod
    def validate_review_output(obj: dict) -> tuple[bool, list[str]]:
        return AgentOutputValidator.validate(obj, [
            "findings", "ratings", "coverage_gaps",
            "assumption_violations", "overall_assessment"
        ])


# ── Base AI Agent ─────────────────────────────────────────────────────────────

class BaseAIAgent:
    """
    Base class for all AI agents in the QA Brain.

    Subclasses must implement:
      - agent_name: str
      - agent_role: str
      - prompt_version: str
      - build_prompt(context) -> str
      - validate_output(raw_dict) -> (bool, errors)
      - transform_output(raw_dict) -> dict  (optional, post-processing)
    """

    agent_name: str = "base_agent"
    agent_role: str = "Base QA Agent"
    prompt_version: str = "v1.0"

    def __init__(self, config: Any, provider: LLMProvider | None = None) -> None:
        """
        Initialize the agent.

        Args:
            config: AIConfig or dict with AI settings
            provider: Optional LLMProvider instance (injected by orchestrator)
        """
        self.config = config
        self.provider = provider
        self.validator = AgentOutputValidator()
        self.stats = ProviderStats()

    def get_provider(self) -> LLMProvider:
        """Get the provider, creating one if needed."""
        if self.provider is not None:
            return self.provider
        if isinstance(self.config, AIConfig):
            p = create_provider(
                provider_name=self.config.provider,
                api_key=self.config.api_key,
                model=self.config.model,
                temperature=self.config.temperature,
                timeout_s=self.config.timeout_s,
            )
            self.provider = p
            return p
        # dict config
        p = create_provider(
            provider_name=self.config.get("provider", "noop") if isinstance(self.config, dict) else "noop",
        )
        self.provider = p
        return p

    def build_system_prompt(self) -> str:
        """Return the system prompt for this agent. Override in subclasses."""
        return f"You are {self.agent_role}. Respond with valid JSON only."

    def build_prompt(self, context: dict | str) -> str:
        """
        Build the full prompt (system + user) from context.

        Override in subclasses to provide agent-specific prompts.
        """
        system = self.build_system_prompt()
        if isinstance(context, dict):
            user = json.dumps(context, indent=2)
        else:
            user = str(context)
        return f"{system}\n\nUSER INPUT:\n{user}\n\nRespond with valid JSON only. Do not include markdown code fences around the JSON. Do not add any text outside the JSON object."

    def call_llm(self, prompt: str, **kwargs: Any) -> dict:
        """Call the LLM provider with a prompt."""
        provider = self.get_provider()
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        result = provider.chat_completion(messages, **kwargs)
        return result

    def parse_and_validate(self, llm_result: dict, validator_fn: Callable = None) -> AgentResponse:
        """
        Parse LLM result, validate output, and return an AgentResponse.

        Args:
            llm_result: dict from LLMProvider.chat_completion()
            validator_fn: optional custom validation function

        Returns:
            AgentResponse with validated output or error details
        """
        # Handle error from provider
        if "error" in llm_result:
            return AgentResponse(
                agent_name=self.agent_name,
                agent_role=self.agent_role,
                prompt_version=self.prompt_version,
                provider=llm_result.get("raw_provider", "unknown"),
                model=llm_result.get("raw_model", "unknown"),
                status="failed",
                latency_ms=llm_result.get("duration_ms", 0),
                prompt_tokens=llm_result.get("token_usage", TokenUsage()).prompt_tokens,
                completion_tokens=llm_result.get("token_usage", TokenUsage()).completion_tokens,
                cost_usd=llm_result.get("token_usage", TokenUsage()).estimated_cost_usd,
                raw_output="",
                error=llm_result["error"],
                error_type=llm_result.get("error_type", "Unknown"),
            )

        raw_content = llm_result.get("content", "{}")
        self.stats.record_call(
            model=llm_result.get("raw_model", self.config.model if hasattr(self.config, 'model') else "unknown"),
            usage=llm_result.get("token_usage", TokenUsage()),
            duration_ms=llm_result.get("duration_ms", 0),
            success=True,
        )

        # Parse JSON
        parsed = parse_json_response(raw_content)
        if parsed is None:
            return AgentResponse(
                agent_name=self.agent_name,
                agent_role=self.agent_role,
                prompt_version=self.prompt_version,
                provider=llm_result.get("raw_provider", "unknown"),
                model=llm_result.get("raw_model", "unknown"),
                status="failed",
                latency_ms=llm_result.get("duration_ms", 0),
                prompt_tokens=llm_result.get("token_usage", TokenUsage()).prompt_tokens,
                completion_tokens=llm_result.get("token_usage", TokenUsage()).completion_tokens,
                cost_usd=llm_result.get("token_usage", TokenUsage()).estimated_cost_usd,
                output={},
                raw_output=raw_content[:2000],
                error="LLM response could not be parsed as JSON",
                error_type="JSONParseError",
            )

        # Validate
        validator_fn = validator_fn or self.validate_output
        is_valid, errors = validator_fn(parsed)

        if not is_valid:
            return AgentResponse(
                agent_name=self.agent_name,
                agent_role=self.agent_role,
                prompt_version=self.prompt_version,
                provider=llm_result.get("raw_provider", "unknown"),
                model=llm_result.get("raw_model", "unknown"),
                status="failed",
                latency_ms=llm_result.get("duration_ms", 0),
                prompt_tokens=llm_result.get("token_usage", TokenUsage()).prompt_tokens,
                completion_tokens=llm_result.get("token_usage", TokenUsage()).completion_tokens,
                cost_usd=llm_result.get("token_usage", TokenUsage()).estimated_cost_usd,
                output=parsed,
                raw_output=raw_content[:2000],
                error="; ".join(errors),
                error_type="ValidationError",
            )

        # Transform output if needed
        output = self.transform_output(parsed)

        return AgentResponse(
            agent_name=self.agent_name,
            agent_role=self.agent_role,
            prompt_version=self.prompt_version,
            provider=llm_result.get("raw_provider", "unknown"),
            model=llm_result.get("raw_model", "unknown"),
            status="success",
            latency_ms=llm_result.get("duration_ms", 0),
            prompt_tokens=llm_result.get("token_usage", TokenUsage()).prompt_tokens,
            completion_tokens=llm_result.get("token_usage", TokenUsage()).completion_tokens,
            cost_usd=llm_result.get("token_usage", TokenUsage()).estimated_cost_usd,
            output=output,
            raw_output=raw_content[:500],  # Truncate raw for storage
        )

    def run(self, context: dict | str, **kwargs: Any) -> AgentResponse:
        """
        Run the agent: build prompt, call LLM, parse, validate, return response.

        Args:
            context: input context (dict or serialized)
            **kwargs: additional args passed to call_llm

        Returns:
            AgentResponse
        """
        start = time.time()
        prompt = self.build_prompt(context)
        llm_result = self.call_llm(prompt, **kwargs)
        response = self.parse_and_validate(llm_result)
        response.latency_ms = (time.time() - start) * 1000
        return response

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        """Default validation: check it's a non-empty dict."""
        if not isinstance(obj, dict):
            return False, ["Output is not a dictionary"]
        if len(obj) == 0:
            return False, ["Output dictionary is empty"]
        return True, []

    def transform_output(self, obj: dict) -> dict:
        """Post-process validated output. Override in subclasses."""
        return obj


# ── Retry wrapper ──────────────────────────────────────────────────────────────

def run_agent_with_retry(agent: BaseAIAgent, context: dict | str,
                         max_retries: int = 1, retry_delay_s: float = 2.0,
                         **kwargs: Any) -> AgentResponse:
    """
    Run an agent with retry logic.

    If the first attempt fails with a retryable error, retry once with
    correction instructions appended to the context.

    Args:
        agent: the AI agent to run
        context: input context
        max_retries: maximum retry attempts (default 1)
        retry_delay_s: delay between retries
        **kwargs: passed to agent.run()

    Returns:
        AgentResponse (may be failed after retries exhausted)
    """
    attempt = 0
    last_response = None

    while attempt <= max_retries:
        response = agent.run(context, **kwargs)

        if response.status == "success":
            return response

        # Check if retryable
        retryable_errors = ("JSONParseError", "ValidationError", "TimeoutError")
        is_retryable = any(err in response.error_type for err in retryable_errors)

        if is_retryable and attempt < max_retries:
            attempt += 1
            time.sleep(retry_delay_s)

            # Add correction instruction to context
            if isinstance(context, dict):
                context["_retry_attempt"] = attempt
                context["_previous_error"] = response.error
                context["_correction"] = (
                    f"Your previous response was invalid: {response.error}. "
                    "Please review the required output format and provide a valid JSON response."
                )
            # Retry with same context (now enriched)
            continue

        # Not retryable or out of retries
        last_response = response
        break

    return last_response or response


# ── Agent registry ─────────────────────────────────────────────────────────────

AGENT_REGISTRY: dict[str, type[BaseAIAgent]] = {}


def register_agent(cls: type[BaseAIAgent]) -> type[BaseAIAgent]:
    """Decorator to register an AI agent class."""
    AGENT_REGISTRY[cls.agent_name] = cls
    return cls


def get_agent(agent_name: str, config: Any = None, provider: LLMProvider = None) -> BaseAIAgent:
    """Instantiate a registered agent by name."""
    if agent_name not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}")
    return AGENT_REGISTRY[agent_name](config=config, provider=provider)
