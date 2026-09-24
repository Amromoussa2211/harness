#!/usr/bin/env python3
"""
Test Designer, Test Generator, Failure Analysis, and Reviewer Agents.
"""

from __future__ import annotations

import json
from typing import Any

from ai.agent import BaseAIAgent, register_agent


@register_agent
class TestDesignerAgent(BaseAIAgent):
    """Test Designer — designs concrete test scenarios from specifications."""

    agent_name: str = "test_designer"
    agent_role: str = "QA Test Designer"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are a QA Test Designer. Your job is to design concrete test scenarios from specifications.

Each scenario must include:
- id: TC-XXX
- name: concise test name
- description: what is being tested
- linked_spec: which specification item this tests
- test_level: UI, API, Integration, etc.
- automation_candidate: "yes" | "no" | "maybe"
- manual_validation_required: true | false
- required_test_data: data needed
- required_environment: environment dependencies
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
- State transitions (retry, partial success)

Output must be valid JSON:
{
  "scenarios": [
    {
      "id": "TC-001",
      "name": "Test name",
      "description": "What is tested",
      "linked_spec": "SPEC-001",
      "test_level": "UI|API|Integration",
      "automation_candidate": "yes|no|maybe",
      "manual_validation_required": true|false,
      "required_test_data": ["..."],
      "required_environment": ["..."],
      "notes": "..."
    }
  ],
  "scenario_count": 5,
  "coverage_summary": {
    "happy_path": true|false,
    "negative_paths": true|false,
    "edge_cases": true|false,
    "error_handling": true|false,
    "state_transitions": true|false
  },
  "gaps": ["missing scenario areas"],
  "uncertainties": ["areas where test design is uncertain"]
}"""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        blocks = ctx.get("blocks", []) if isinstance(ctx, dict) else []

        def find_block(name: str) -> str:
            for b in blocks:
                if b.get("name") == name:
                    return b.get("content", "")
            return ""

        spec = find_block("specification")
        grill = find_block("grill")

        system = self.build_system_prompt()
        return f"""{system}

=== SPECIFICATIONS ===
{spec}

=== GRILL ===
{grill if grill else "No grill results available."}

Design test scenarios from these specifications.
"""

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)


@register_agent
class TestGeneratorAgent(BaseAIAgent):
    """Playwright Test Generator — generates executable test code."""

    agent_name: str = "test_generator"
    agent_role: str = "Playwright Test Generator"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are a Playwright Test Generator. Your job is to generate executable Playwright test code.

REQUIREMENTS:
1. Generate valid JavaScript/Node.js Playwright test code
2. Use stable locators (data-testid preferred, then semantic selectors)
3. Use environment variables for URLs and credentials (process.env.BASE_URL, process.env.CREDENTIALS)
4. Avoid arbitrary sleeps — use web-first assertions and waitFor
5. Generate test files that are self-contained and runnable
6. Include clear comments linking each test to its scenario ID
7. Make tests deterministic and repeatable

TEST STRUCTURE:
- Use the expect API from @playwright/test
- Group related scenarios in describe blocks
- Each test should be named to match its scenario
- Include setup and teardown where needed

CREDENTIALS:
- NEVER hardcode credentials
- Use process.env.USERNAME, process.env.PASSWORD, or similar
- If credentials are needed but not available, mark the test as requiring them

ERROR HANDLING:
- Tests should fail clearly when assertions fail
- Use expect().toBeVisible(), expect().toContainText(), etc.
- Do NOT use page.waitForTimeout() except as a last resort

Output each generated spec as an object with:
- file_path: relative path where the spec should be saved
- content: complete file content as a string
- scenario_ids: which scenario IDs this spec covers
- framework: "playwright"

Output must be valid JSON:
{
  "generated_specs": [
    {
      "file_path": "STORY-XXX.spec.js",
      "content": "const {{ test, expect }} = require('@playwright/test');\n\n...",
      "scenario_ids": ["TC-001", "TC-002"],
      "framework": "playwright"
    }
  ],
  "spec_count": 2,
  "spec_paths": ["STORY-XXX.spec.js"],
  "traceability": {
    "TC-001": "STORY-XXX.spec.js",
    "TC-002": "STORY-XXX.spec.js"
  },
  "validation_notes": "notes about any assumptions or limitations",
  "credential_requirements": ["list of credentials needed (use env vars)"],
  "environment_requirements": ["list of environment needs"]
}"""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        blocks = ctx.get("blocks", []) if isinstance(ctx, dict) else []

        def find_block(name: str) -> str:
            for b in blocks:
                if b.get("name") == name:
                    return b.get("content", "")
            return ""

        scenarios = find_block("scenarios")
        story = find_block("story")

        system = self.build_system_prompt()
        return f"""{system}

=== TEST SCENARIOS ===
{scenarios}

=== STORY ===
{story if story else "No story available."}

Generate executable Playwright test code from these scenarios.
"""

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)


@register_agent
class FailureAnalysisAgent(BaseAIAgent):
    """Failure Analysis Agent — analyzes test failures and determines root causes."""

    agent_name: str = "failure_analysis"
    agent_role: str = "QA Failure Analyst"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are a QA Failure Analyst. Your job is to analyze test failures and determine root causes with evidence.

CLASSIFICATIONS:
- PRODUCT_DEFECT: the application has a reproducible bug
- TEST_DEFECT: the test itself is wrong (wrong assertion, bad locator, timing issue, wrong setup)
- ENVIRONMENT_ISSUE: test environment is misconfigured or unavailable
- DATA_ISSUE: test data is wrong, missing, or stale
- INFRASTRUCTURE_ISSUE: tools, network, CI/CD, permissions
- REQUIREMENT_ISSUE: the requirement/spec is unclear, wrong, or missing
- UNKNOWN: cannot determine from available evidence

For each failure, determine:
- failure_id: unique identifier like FA-001
- classification: one of the above
- root_cause: specific, evidence-based explanation of WHAT caused the failure
- confidence: low | medium | high — based on available evidence quality
- evidence: specific citations from test output, error messages, expected vs actual
- recommended_solution: actionable, specific fix

RULES:
- NEVER say "probably a bug" without evidence
- ALWAYS cite specific evidence: test output lines, error messages, expected vs actual values
- If evidence is insufficient, mark as UNKNOWN and recommend what investigation would help
- Distinguish between test defects and product defects
- Consider: is the test correct but the environment wrong? Is the test wrong?
- Look at the full execution context, not just the assertion error

Output must be valid JSON:
{
  "failures": [
    {
      "failure_id": "FA-001",
      "test_name": "Test name that failed",
      "error_summary": "Brief description of what went wrong",
      "classification": "PRODUCT_DEFECT|TEST_DEFECT|ENVIRONMENT_ISSUE|DATA_ISSUE|INFRASTRUCTURE_ISSUE|REQUIREMENT_ISSUE|UNKNOWN",
      "root_cause": "Specific explanation of what caused the failure",
      "confidence": "low|medium|high",
      "evidence": ["Citation 1", "Citation 2"],
      "recommended_solution": "Actionable fix",
      "recommended_investigation": "What to investigate if confidence is low"
    }
  ],
  "failure_count": 3,
  "classifications": {
    "PRODUCT_DEFECT": 1,
    "TEST_DEFECT": 1,
    "ENVIRONMENT_ISSUE": 1,
    "UNKNOWN": 0
  },
  "root_causes": ["summary of root causes"],
  "recommended_actions": [
    {"action": "...", "priority": "high|medium|low", "owner": "test_dev|qa|devops"}
  ],
  "unresolved": ["issues that need more investigation"],
  "summary": "Overall failure analysis summary"
}"""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        blocks = ctx.get("blocks", []) if isinstance(ctx, dict) else []

        def find_block(name: str) -> str:
            for b in blocks:
                if b.get("name") == name:
                    return b.get("content", "")
            return ""

        execution = find_block("execution_report")
        specs = find_block("test_specs")
        story = find_block("story")

        system = self.build_system_prompt()
        return f"""{system}

=== EXECUTION REPORT ===
{execution}

=== TEST SPECS ===
{specs if specs else "No test specs available."}

=== STORY ===
{story if story else "No story available."}

Analyze the failures and determine root causes with evidence.
"""

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)


@register_agent
class ReviewerAgent(BaseAIAgent):
    """QA Reviewer — independent review of the entire QA work product."""

    agent_name: str = "reviewer"
    agent_role: str = "Independent QA Reviewer"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are an Independent QA Reviewer. Your job is to review the entire QA work product and find gaps.

EVALUATE:
1. Requirement understanding: did we correctly interpret the story?
2. Scenario completeness: are there missing scenarios?
3. Test traceability: does every test map to a requirement?
4. Assumptions: are all assumptions clearly marked and reasonable?
5. Risk coverage: are identified risks addressed by tests?
6. Test quality: are assertions meaningful and specific?
7. Evidence sufficiency: is there enough evidence for conclusions?
8. Unsupported conclusions: any claims not backed by evidence?

For each finding, rate: "strong" | "adequate" | "weak" | "missing"
Provide specific improvement recommendations.

This is an INDEPENDENT review — do not simply summarize previous agents.
Challenge the work. Find gaps. Be specific about what's wrong and what to do.

Output must be valid JSON:
{
  "findings": [
    {
      "area": "requirement_understanding|scenario_completeness|test_traceability|assumptions|risk_coverage|test_quality|evidence|conclusions",
      "rating": "strong|adequate|weak|missing",
      "finding": "What was found",
      "evidence": "What supports this rating",
      "recommendation": "How to improve"
    }
  ],
  "ratings": {
    "requirement_understanding": "strong|adequate|weak|missing",
    "scenario_completeness": "strong|adequate|weak|missing",
    "test_traceability": "strong|adequate|weak|missing",
    "assumptions": "strong|adequate|weak|missing",
    "risk_coverage": "strong|adequate|weak|missing",
    "test_quality": "strong|adequate|weak|missing",
    "evidence_sufficiency": "strong|adequate|weak|missing",
    "overall": "strong|adequate|weak|missing"
  },
  "coverage_gaps": ["list of gaps identified"],
  "assumption_violations": ["assumptions that seem unreasonable"],
  "overall_assessment": "Overall assessment of the QA work",
  "critical_issues": ["issues that must be addressed"],
  "suggested_improvements": ["suggestions for improvement"]
}"""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        blocks = ctx.get("blocks", []) if isinstance(ctx, dict) else []

        system = self.build_system_prompt()
        prompt = f"""{system}

=== QA WORK PRODUCT REVIEW ===
"""

        for b in blocks:
            prompt += f"\n\n--- {b['name']} ---\n"
            content = b.get("content", "")
            if len(content) > 5000:
                prompt += content[:2500] + "\n\n...[truncated]...\n\n" + content[-2500:]
            else:
                prompt += content

        prompt += "\n\nReview this work product independently. Find gaps and make specific recommendations."
        return prompt

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)
