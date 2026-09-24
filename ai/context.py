#!/usr/bin/env python3
"""
AI Context Builder — builds focused context for each AI agent.

Never dumps the entire repository. Selects only relevant artifacts
and content for each agent's specific role.
"""

from __future__ import annotations

import json
import os
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Context block ─────────────────────────────────────────────────────────────

@dataclass
class ContextBlock:
    """A single block of context for an AI agent."""
    name: str           # e.g. "story", "analysis", "discovery"
    content: str        # the actual text content
    source: str         # file path or description
    size_chars: int = 0
    truncated: bool = False
    hash: str = ""

    def __post_init__(self):
        self.size_chars = len(self.content)
        self.hash = hashlib.sha256(self.content.encode()).hexdigest()[:12]
        if self.size_chars == 0:
            self.content = "(empty)"


@dataclass
class AgentContext:
    """Complete context bundle for an AI agent invocation."""
    story_id: str = ""
    project_name: str = ""
    blocks: list[ContextBlock] = field(default_factory=list)
    config_summary: str = ""
    agent_role: str = ""
    instructions: str = ""
    total_chars: int = 0
    max_chars: int = 32000  # soft limit per agent call

    def to_dict(self) -> dict:
        """Serialize context for LLM prompt building."""
        d: dict = {
            "story_id": self.story_id,
            "project_name": self.project_name,
            "agent_role": self.agent_role,
            "config_summary": self.config_summary,
            "blocks": [],
            "instructions": self.instructions,
        }
        for b in self.blocks:
            d["blocks"].append({
                "name": b.name,
                "source": b.source,
                "content": b.content,
                "size_chars": b.size_chars,
                "truncated": b.truncated,
                "hash": b.hash,
            })
        d["total_chars"] = self.total_chars
        return d

    @property
    def is_over_limit(self) -> bool:
        return self.total_chars > self.max_chars

    def summary(self) -> str:
        lines = [
            f"=== Agent Context: {self.agent_role} ===",
            f"Story: {self.story_id} | Project: {self.project_name}",
            f"Config: {self.config_summary}",
            f"Total blocks: {len(self.blocks)} | Total chars: {self.total_chars}",
        ]
        for b in self.blocks:
            indicator = " [TRUNCATED]" if b.truncated else ""
            lines.append(f"  [{b.name}] {b.source} ({b.size_chars} chars{indicator})")
        if self.is_over_limit:
            lines.append(f"  WARNING: Context exceeds {self.max_chars} char limit")
        return "\n".join(lines)


# ── Context builder ───────────────────────────────────────────────────────────

class ContextBuilder:
    """
    Builds focused context for AI agents from shared-state artifacts.

    Usage:
        cb = ContextBuilder(shared_state_dir=Path("/path/to/shared-state/STORY-XXX"))
        context = cb.build_analyst_context(story_text, project_config)

    Never reads arbitrary filesystem — only artifacts known to exist.
    """

    def __init__(self, shared_state_dir: Path | str,
                 project_dir: Path | str = "",
                 max_chars_per_block: int = 8000,
                 max_total_chars: int = 32000) -> None:
        self.base = Path(shared_state_dir)
        self.project_dir = Path(project_dir) if project_dir else Path()
        self.max_chars_per_block = max_chars_per_block
        self.max_total_chars = max_total_chars

    def _load_artifact(self, rel_path: str) -> str:
        """Load an artifact file, return empty string if missing."""
        p = self.base / rel_path
        if not p.is_file():
            return ""
        content = p.read_text(errors="replace")
        if len(content) > self.max_chars_per_block:
            # Keep head and tail
            head = content[:self.max_chars_per_block // 2]
            tail = content[-(self.max_chars_per_block // 2):]
            return f"{head}\n\n...[truncated {len(content) - len(head) - len(tail)} chars]...\n\n{tail}"
        return content

    def _load_story(self, story_path: str) -> str:
        p = Path(story_path)
        if p.is_file():
            content = p.read_text(errors="replace")
            if len(content) > self.max_chars_per_block:
                head = content[:self.max_chars_per_block // 2]
                tail = content[-(self.max_chars_per_block // 2):]
                return f"{head}\n\n...[truncated {len(content) - len(head) - len(tail)} chars]...\n\n{tail}"
            return content
        return ""

    def _block(self, name: str, content: str, source: str) -> ContextBlock:
        return ContextBlock(name=name, content=content, source=source)

    # ── Per-agent context builders ──────────────────────────────────────────

    def build_analyst_context(self, story_text: str, project_config: dict) -> AgentContext:
        """Context for the Analyst Agent."""
        blocks = [
            self._block("story", story_text, "story.md"),
            self._block("project_config", json.dumps(project_config, indent=2),
                       "project.yaml"),
        ]
        return AgentContext(
            story_id="",  # set by caller
            project_name=project_config.get("project", {}).get("name", "unknown"),
            blocks=blocks,
            config_summary=f"web={project_config.get('application',{}).get('web',False)}, "
                          f"api={project_config.get('application',{}).get('api',False)}",
            agent_role="QA Analyst",
            instructions="""Analyze the story to identify:
1. Business behavior described
2. Actors (who is performing the action)
3. Inputs (what data/parameters are involved)
4. Outputs (what results/responses are expected)
5. Acceptance criteria
6. Ambiguities (unclear or missing information)
7. Missing requirements
8. Dependencies (external systems, data, credentials)
9. Assumptions

Separate clearly:
- EXPLICIT: directly stated in the story
- INFERENCE: reasonable deduction from the story
- ASSUMPTION: needed to proceed but not confirmed
- UNKNOWN: cannot determine from available information
- QUESTION: needs clarification

DO NOT invent:
- URLs, credentials, APIs, database schemas
- Business rules not stated in the story
- Error messages, user roles, product behavior

When information is missing, mark as UNKNOWN or QUESTION.""",
        )

    def build_grill_context(self, story_text: str, analysis_text: str,
                            project_config: dict) -> AgentContext:
        """Context for the QA Grill Agent."""
        blocks = [
            self._block("story", story_text, "story.md"),
            self._block("analysis", analysis_text, "analysis/output.md"),
            self._block("project_config", json.dumps(project_config, indent=2),
                       "project.yaml"),
        ]
        return AgentContext(
            story_id="",
            project_name=project_config.get("project", {}).get("name", "unknown"),
            blocks=blocks,
            config_summary=f"web={project_config.get('application',{}).get('web',False)}, "
                          f"api={project_config.get('application',{}).get('api',False)}",
            agent_role="QA Grill Master",
            instructions="""Challenge the story from a QA perspective. Ask probing questions about:

1. Invalid inputs — what happens when data is wrong?
2. Unauthorized access — what happens without permission?
3. Edge cases — boundary values, empty data, duplicates
4. Error handling — timeouts, failures, retries
5. External dependencies — what if they fail?
6. State transitions — what if steps are repeated or skipped?
7. Concurrency — what if two requests arrive at once?
8. Security — injection, enumeration, CSRF, auth bypass
9. Performance — what if it's slow or overloaded?

Each question should be specific to THIS story. Do NOT ask generic boilerplate.
Cite the relevant part of the story that motivates each question.

Output:
- questions: list of {id, question, motivation, risk_if_unanswered}
- ambiguities_found: what is unclear
- missing_requirements: what's needed but not specified
- risk_flags: potential risks identified during grilling
- clarification_needed: list of items needing human clarification""",
        )

    def build_risk_context(self, story_text: str, analysis_text: str,
                           grill_text: str, discovery_text: str,
                           project_config: dict) -> AgentContext:
        """Context for the Risk Agent."""
        blocks = [
            self._block("story", story_text, "story.md"),
            self._block("analysis", analysis_text, "analysis/output.md"),
            self._block("grill", grill_text, "grill/output.md"),
            self._block("discovery", discovery_text, "discovery/output.md"),
            self._block("project_config", json.dumps(project_config, indent=2),
                       "project.yaml"),
        ]
        return AgentContext(
            story_id="",
            project_name=project_config.get("project", {}).get("name", "unknown"),
            blocks=blocks,
            config_summary=f"web={project_config.get('application',{}).get('web',False)}, "
                          f"api={project_config.get('application',{}).get('api',False)}",
            agent_role="QA Risk Analyst",
            instructions="""Identify and assess risks for this story. Consider:

1. BUSINESS RISK — what business impact if this is wrong?
2. TECHNICAL RISK — implementation complexity, uncertainty
3. SECURITY RISK — auth, data exposure, injection, etc.
4. DATA RISK — data loss, corruption, consistency
5. INTEGRATION RISK — external dependencies, APIs, webhooks
6. PERFORMANCE RISK — load, latency, scalability
7. AVAILABILITY RISK — downtime, failover, recovery
8. REGRESSION RISK — what else could break?

Each risk needs:
- risk_id: unique identifier
- description: what could go wrong
- reason: why this is a risk for THIS story
- impact: business/technical impact
- likelihood: low/medium/high
- priority: low/medium/high/critical
- affected_area: which part of the system
- mitigation: how to reduce the risk
- evidence: what supports this assessment

Only include relevant categories. Do NOT pad with irrelevant risks.
Explain WHY each risk applies to this specific story.""",
        )

    def build_architect_context(self, story_text: str, analysis_text: str,
                                grill_text: str, discovery_text: str,
                                project_config: dict) -> AgentContext:
        """Context for the Architect Agent."""
        blocks = [
            self._block("story", story_text, "story.md"),
            self._block("analysis", analysis_text, "analysis/output.md"),
            self._block("grill", grill_text, "grill/output.md"),
            self._block("discovery", discovery_text, "discovery/output.md"),
            self._block("project_config", json.dumps(project_config, indent=2),
                       "project.yaml"),
        ]
        project = project_config.get("project", {}) or {}
        app = project_config.get("application", {}) or {}
        autom = project_config.get("automation", {}) or {}
        return AgentContext(
            story_id="",
            project_name=project.get("name", "unknown"),
            blocks=blocks,
            config_summary=f"web={app.get('web', False)}, "
                          f"api={app.get('api', False)}, "
                          f"playwright={autom.get('framework', '') == 'playwright'}",
            agent_role="QA Test Architect",
            instructions="""Design the test architecture for this story.

The project uses Playwright for web testing. Determine:

1. test_strategy: which test types are appropriate
   - UI/E2E: for user-facing flows
   - API: for service-layer testing
   - Contract: for API contract validation
   - Performance: for load/latency
   - Security: for auth, injection, etc.
   - Accessibility: for WCAG compliance
   - Mobile: for responsive/mobile behavior

2. rationale: WHY each test type is or is not recommended
   - Link to specific story elements
   - Explain the testing pyramid position

3. recommendations: specific architectural guidance
   - Test level selection
   - Data setup strategy
   - Environment needs
   - Mock/stub suggestions
   - Cross-browser considerations

Do NOT recommend every test type. Only what's relevant.
If the story doesn't need API testing, say so and explain why."""
        )

    def build_specification_context(self, story_text: str, analysis_text: str,
                                    grill_text: str, project_config: dict) -> AgentContext:
        """Context for the Specification Agent."""
        blocks = [
            self._block("story", story_text, "story.md"),
            self._block("analysis", analysis_text, "analysis/output.md"),
            self._block("grill", grill_text, "grill/output.md"),
            self._block("project_config", json.dumps(project_config, indent=2),
                       "project.yaml"),
        ]
        return AgentContext(
            story_id="",
            project_name=project_config.get("project", {}).get("name", "unknown"),
            blocks=blocks,
            config_summary=f"web={project_config.get('application',{}).get('web',False)}, "
                          f"api={project_config.get('application',{}).get('api',False)}",
            agent_role="QA Specification Writer",
            instructions="""Transform the analyzed requirements into detailed, testable specifications.

For each acceptance criterion, produce a specification with:
- preconditions: what must be true before testing
- test_data: specific data needed (from story, not invented)
- steps: numbered test steps
- expected_results: what PASS looks like
- negative_behavior: what FAIL looks like
- edge_cases: boundary conditions
- dependencies: external needs

Each spec must map back to an acceptance criterion.
No orphan specs. No invented business rules.

When exact values are not specified (error messages, URLs), mark as 'TO_BE_DEFINED'.""",
        )

    def build_test_design_context(self, specification_text: str, grill_text: str,
                                  project_config: dict) -> AgentContext:
        """Context for the Test Designer Agent."""
        blocks = [
            self._block("specification", specification_text, "specification/output.md"),
            self._block("grill", grill_text, "grill/output.md"),
            self._block("project_config", json.dumps(project_config, indent=2),
                       "project.yaml"),
        ]
        return AgentContext(
            story_id="",
            project_name=project_config.get("project", {}).get("name", "unknown"),
            blocks=blocks,
            config_summary=f"web={project_config.get('application',{}).get('web',False)}, "
                          f"api={project_config.get('application',{}).get('api',False)}",
            agent_role="QA Test Designer",
            instructions="""Design concrete test scenarios from the specifications.

Each scenario must include:
- id: TC-XXX
- name: concise test name
- description: what is being tested
- linked_spec: which specification item this tests
- test_level: UI, API, Integration, etc.
- automation_candidate: yes/no/maybe
- manual_validation_required: yes/no
- required_test_data: data needed
- required_environment: env dependencies
- notes: any special considerations

Rules:
- Every scenario must trace to a specification item
- No orphan tests
- Prefer lower test levels where valid
- Include happy path + negative + edge cases
- Mark what makes each scenario distinct

Cover:
- Happy path (primary success scenario)
- Negative paths (invalid inputs, error conditions)
- Edge cases (boundary values, extremes)
- Error handling (timeouts, failures)
- State transitions (retry, partial success)""",
        )

    def build_test_generation_context(self, scenarios_text: str, project_config: dict,
                                      story_text: str) -> AgentContext:
        """Context for the Playwright Test Generator Agent."""
        blocks = [
            self._block("scenarios", scenarios_text, "test-design/output.md"),
            self._block("story", story_text, "story.md"),
            self._block("project_config", json.dumps(project_config, indent=2),
                       "project.yaml"),
        ]
        return AgentContext(
            story_id="",
            project_name=project_config.get("project", {}).get("name", "unknown"),
            blocks=blocks,
            config_summary=f"framework={project_config.get('automation',{}).get('framework','')}, "
                          f"language={project_config.get('automation',{}).get('language','')}",
            agent_role="Playwright Test Generator",
            instructions="""Generate executable Playwright test code from the test scenarios.

Requirements:
1. Generate valid JavaScript/Node.js Playwright test code
2. Use stable locators (data-testid preferred, then semantic selectors)
3. Use environment variables for URLs and credentials (never hardcode)
4. Avoid arbitrary sleeps — use web-first assertions and waitFor
5. Generate ONE test file per scenario or group related scenarios
6. Include clear comments linking each test to its scenario ID
7. Make tests deterministic and repeatable
8. Do NOT include credentials — use process.env

Each test must:
- Have a clear test name matching the scenario
- Set up proper preconditions
- Execute the steps from the spec
- Assert the expected results
- Clean up if needed

Output the complete file content as a string in generated_specs.
Include the file path where each spec should be saved.""",
        )

    def build_failure_analysis_context(self, execution_report: str,
                                       test_specs: str, story_text: str,
                                       project_config: dict) -> AgentContext:
        """Context for the Failure Analysis Agent."""
        blocks = [
            self._block("execution_report", execution_report, "execution/run-report.md"),
            self._block("test_specs", test_specs, "test-design/output.md"),
            self._block("story", story_text, "story.md"),
            self._block("project_config", json.dumps(project_config, indent=2),
                       "project.yaml"),
        ]
        return AgentContext(
            story_id="",
            project_name=project_config.get("project", {}).get("name", "unknown"),
            blocks=blocks,
            config_summary=f"web={project_config.get('application',{}).get('web',False)}, "
                          f"api={project_config.get('application',{}).get('api',False)}",
            agent_role="QA Failure Analyst",
            instructions="""Analyze test failures and determine root causes.

For each failure, determine:
- classification: PRODUCT_DEFECT | TEST_DEFECT | ENVIRONMENT_ISSUE | DATA_ISSUE | INFRASTRUCTURE_ISSUE | REQUIREMENT_ISSUE | UNKNOWN
- root_cause: what actually caused the failure
- confidence: low/medium/high — based on available evidence
- evidence: what supports this conclusion (cite specific artifacts)
- recommended_solution: actionable fix

Classifications:
- PRODUCT_DEFECT: the application has a bug
- TEST_DEFECT: the test itself is wrong (wrong assertion, bad locator, timing)
- ENVIRONMENT_ISSUE: test env is misconfigured or unavailable
- DATA_ISSUE: test data is wrong or missing
- INFRASTRUCTURE_ISSUE: tools, network, CI, etc.
- REQUIREMENT_ISSUE: the requirement/spec is unclear or wrong
- UNKNOWN: cannot determine from available evidence

Never say 'probably a bug' without evidence.
Cite specific evidence: test output, error messages, expected vs actual.
If evidence is insufficient, mark as UNKNOWN with recommended investigation.""",
        )

    def build_review_context(self, all_artifacts: dict[str, str],
                             project_config: dict) -> AgentContext:
        """Context for the QA Reviewer Agent."""
        blocks = []
        for name, content in all_artifacts.items():
            blocks.append(self._block(name, content, name))

        return AgentContext(
            story_id="",
            project_name=project_config.get("project", {}).get("name", "unknown"),
            blocks=blocks,
            config_summary=f"web={project_config.get('application',{}).get('web',False)}, "
                          f"api={project_config.get('application',{}).get('api',False)}",
            agent_role="Independent QA Reviewer",
            instructions="""Perform an independent review of the entire QA work product.

Evaluate:
1. Requirement understanding: did we correctly interpret the story?
2. Scenario completeness: are there missing scenarios?
3. Test traceability: does every test map to a requirement?
4. Assumptions: are all assumptions clearly marked and reasonable?
5. Risk coverage: are identified risks addressed by tests?
6. Test quality: are assertions meaningful and specific?
7. Evidence sufficiency: is there enough evidence for conclusions?
8. Unsupported conclusions: any claims not backed by evidence?

For each finding, rate: strong / adequate / weak / missing
Provide specific improvement recommendations.

This is an INDEPENDENT review — do not simply summarize previous agents.
Challenge the work. Find gaps. Be specific.""",
        )
