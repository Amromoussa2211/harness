#!/usr/bin/env python3
"""
AI Engine — orchestrates AI agents for a QA run.

Routes context to the appropriate agent, manages retries, records metadata,
and persists agent outputs to shared-state.
"""

from __future__ import annotations

import time
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai.agent import (
    BaseAIAgent, AgentResponse, AIRunMetadata,
    run_agent_with_retry, AGENT_REGISTRY, get_agent, ProviderStats,
)
from ai.config import AIConfig
from ai.context import AgentContext, ContextBuilder
from ai.provider import LLMProvider, create_provider


@dataclass
class AIEngineResult:
    """Result of running the AI engine for a story."""
    run_id: str
    story_id: str
    project_name: str
    mode: str  # "ai" or "deterministic"
    provider: str
    model: str
    prompt_version: str = "v1.0"
    success: bool = False
    blocked: bool = False
    blocked_reason: str = ""
    agent_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    duration_ms: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_usd: float = 0.0
    artifacts_dir: Path = Path()
    started_at: str = ""
    completed_at: str = ""
    provider_type: str = "noop"
    is_real_llm: bool = False
    noop_response: str = ""  # canned response from noop provider


class AIEngine:
    """
    Orchestrates AI agents for a QA run.

    Responsibilities:
    - Manage run isolation (run_id, artifacts directory)
    - Route context to appropriate agents
    - Handle retries and failures
    - Record metadata for reporting
    """

    def __init__(self, shared_state_base: Path,
                 project_dir: Path = Path(),
                 mode: str = "ai",
                 config: AIConfig | None = None) -> None:
        self.shared_state_base = shared_state_base
        self.project_dir = project_dir
        self.mode = mode
        self.config = config or AIConfig()
        self.agent_results: list[AgentResponse] = []
        self._provider: LLMProvider | None = None
        self._start_time: float = 0.0
        self.run_id: str = ""

    def _get_provider(self) -> LLMProvider:
        """Get or create the shared provider instance."""
        if self._provider is not None:
            return self._provider
        if self.config.is_real_provider:
            kwargs: dict = dict(
                provider_name=self.config.provider,
                api_key=self.config.effective_api_key,
                model=self.config.model,
                temperature=self.config.temperature,
                timeout_s=self.config.timeout_s,
            )
            if self.config.provider == "openai" and self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            self._provider = create_provider(**kwargs)
        else:
            self._provider = create_provider("noop")
        return self._provider

    def create_run_id(self) -> str:
        """Create a unique run ID for this execution."""
        ts = int(time.time())
        rand = uuid.uuid4().hex[:8]
        return f"ai-{ts}-{rand}"

    def set_run_metadata(self, story_id: str, project_name: str,
                         config_source: str = "env") -> None:
        """Set metadata for the current run."""
        self.run_id = self.create_run_id()
        self._start_time = time.time()
        self.artifacts_dir = self.shared_state_base / "ai-runs" / self.run_id
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save_agent_result(self, response: AgentResponse, label: str) -> Path:
        """Persist an agent result to shared state."""
        result_path = self.artifacts_dir / f"{label}.json"
        data = {
            "agent_name": response.agent_name,
            "agent_role": response.agent_role,
            "prompt_version": response.prompt_version,
            "provider": response.provider,
            "model": response.model,
            "status": response.status,
            "latency_ms": round(response.latency_ms, 2),
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost_usd": round(response.cost_usd, 6),
            "output": response.output,
            "raw_output": response.raw_output,
            "error": response.error,
            "error_type": response.error_type,
            "retry_count": response.retry_count,
            "run_id": self.run_id,
            "story_id": str(self.shared_state_base.name).replace("STORY-", "").replace("/", "-"),
            "project_name": "playwriteAdvanced",
        }
        result_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.agent_results.append(response)
        return result_path

    def _save_noop_response(self, response: AgentResponse) -> None:
        """Save the noop canned response for the report."""
        self._noop_response = response.raw_output

    def run_agent(self, agent_name: str, context: AgentContext,
                  label: str, max_retries: int = None,
                  retry_delay_s: float = None,
                  **kwargs: Any) -> AgentResponse:
        """Run a single AI agent with the given context."""
        mr = max_retries if max_retries is not None else self.config.max_retries
        rd = retry_delay_s if retry_delay_s is not None else self.config.retry_delay_s

        agent = get_agent(agent_name, config=self.config, provider=self._get_provider())
        agent.prompt_version = self.config.prompt_version

        response = run_agent_with_retry(agent, context.to_dict(), max_retries=mr,
                                        retry_delay_s=rd, **kwargs)
        self.save_agent_result(response, label)
        return response

    def save_context(self, context: AgentContext, label: str = "context") -> Path:
        """Persist context to shared state for traceability."""
        ctx_path = self.artifacts_dir / f"{label}.context.json"
        ctx_path.write_text(json.dumps(context.to_dict(), indent=2), encoding="utf-8")
        return ctx_path

    def run_analyst(self, story_text: str, project_config: dict) -> AgentResponse:
        """Run the Analyst agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_analyst_context(story_text, project_config)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "analyst.context")
        return self.run_agent("analyst", ctx, "analyst.result")

    def run_grill(self, story_text: str, analysis_text: str,
                  project_config: dict) -> AgentResponse:
        """Run the Grill agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_grill_context(story_text, analysis_text, project_config)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "grill.context")
        return self.run_agent("grill", ctx, "grill.result")

    def run_risk(self, story_text: str, analysis_text: str, grill_text: str,
                 discovery_text: str, project_config: dict) -> AgentResponse:
        """Run the Risk agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_risk_context(story_text, analysis_text, grill_text,
                                     discovery_text, project_config)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "risk.context")
        return self.run_agent("risk", ctx, "risk.result")

    def run_architect(self, story_text: str, analysis_text: str, grill_text: str,
                      discovery_text: str, project_config: dict) -> AgentResponse:
        """Run the Architect agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_architect_context(story_text, analysis_text, grill_text,
                                          discovery_text, project_config)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "architect.context")
        return self.run_agent("architect", ctx, "architect.result")

    def run_specification(self, story_text: str, analysis_text: str,
                          grill_text: str, project_config: dict) -> AgentResponse:
        """Run the Specification agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_specification_context(story_text, analysis_text, grill_text,
                                              project_config)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "specification.context")
        return self.run_agent("specification", ctx, "specification.result")

    def run_test_designer(self, specification_text: str, grill_text: str,
                          project_config: dict) -> AgentResponse:
        """Run the Test Designer agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_test_design_context(specification_text, grill_text, project_config)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "test_designer.context")
        return self.run_agent("test_designer", ctx, "test_designer.result")

    def run_test_generator(self, scenarios_text: str, project_config: dict,
                           story_text: str) -> AgentResponse:
        """Run the Test Generator agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_test_generation_context(scenarios_text, project_config, story_text)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "test_generator.context")
        return self.run_agent("test_generator", ctx, "test_generator.result")

    def run_failure_analysis(self, execution_report: str, test_specs: str,
                             story_text: str, project_config: dict) -> AgentResponse:
        """Run the Failure Analysis agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_failure_analysis_context(execution_report, test_specs,
                                                 story_text, project_config)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "failure_analysis.context")
        return self.run_agent("failure_analysis", ctx, "failure_analysis.result")

    def run_reviewer(self, all_artifacts: dict[str, str], project_config: dict) -> AgentResponse:
        """Run the Reviewer agent."""
        cb = ContextBuilder(self.shared_state_base, self.project_dir)
        ctx = cb.build_review_context(all_artifacts, project_config)
        ctx.story_id = self.run_id
        ctx.project_name = "playwriteAdvanced"
        self.save_context(ctx, "reviewer.context")
        return self.run_agent("reviewer", ctx, "reviewer.result")

    def finalize(self) -> AIEngineResult:
        """Finalize the engine run and return the result."""
        elapsed = time.time() - self._start_time
        success_count = sum(1 for r in self.agent_results if r.status == "success")
        fail_count = len(self.agent_results) - success_count

        result = AIEngineResult(
            run_id=self.run_id,
            story_id=str(self.shared_state_base.name).replace("STORY-", "").split("/")[0],
            project_name="playwriteAdvanced",
            mode=self.mode,
            provider=self.config.provider,
            model=self.config.model,
            prompt_version=self.config.prompt_version,
            success=success_count > 0,
            blocked=False,
            agent_count=len(self.agent_results),
            success_count=success_count,
            fail_count=fail_count,
            duration_ms=round(elapsed * 1000, 2),
            total_prompt_tokens=sum(r.prompt_tokens for r in self.agent_results),
            total_completion_tokens=sum(r.completion_tokens for r in self.agent_results),
            total_cost_usd=round(sum(r.cost_usd for r in self.agent_results), 6),
            artifacts_dir=self.artifacts_dir,
            started_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            completed_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            provider_type=self.config.provider,
            is_real_llm=self.config.is_real_provider,
        )
        return result
