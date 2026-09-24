#!/usr/bin/env python3
"""
Analyst Agent — understands the story, extracts actors/inputs/outputs/ACs,
identifies ambiguities, missing requirements, dependencies, assumptions.
"""

from __future__ import annotations

import json
from typing import Any

from ai.agent import BaseAIAgent, register_agent, AgentResponse


@register_agent
class AnalystAgent(BaseAIAgent):
    """QA Analyst — requirement interpretation and analysis."""

    agent_name: str = "analyst"
    agent_role: str = "QA Analyst"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are a QA Analyst. Your job is to understand a software story and produce a structured analysis.

You must:
1. Understand the story completely
2. Identify business behavior described
3. Extract actors (who performs the action)
4. Identify inputs (what data/parameters are involved)
5. Identify outputs (what results/responses are expected)
6. Identify acceptance criteria
7. Identify ambiguities (unclear or missing information)
8. Identify missing requirements
9. Identify dependencies (external systems, data, credentials)
10. Identify assumptions

CRITICAL RULES:
- Never invent undocumented business rules
- Never invent URLs, credentials, APIs, database schemas
- Never invent error messages, user roles, or product behavior
- When information is missing, mark as UNKNOWN or QUESTION
- Clearly separate: EXPLICIT | INFERENCE | ASSUMPTION | UNKNOWN | QUESTION

Output must be valid JSON with this structure:
{
  "summary": "Brief analysis summary",
  "actors": ["list of actors"],
  "inputs": ["list of inputs"],
  "outputs": ["list of outputs"],
  "acceptance_criteria": [{"id": "AC1", "text": "...", "type": "functional|negative|edge"}],
  "ambiguities": [{"issue": "...", "impact": "...", "confidence": "low|medium|high"}],
  "missing_requirements": [{"requirement": "...", "why_needed": "..."}],
  "dependencies": [{"dependency": "...", "type": "external_system|data|credential|api"}],
  "assumptions": [{"assumption": "...", "justification": "...", "risk": "..."}],
  "unknowns": [{"unknown": "...", "impact": "..."}],
  "questions": [{"question": "...", "priority": "high|medium|low"}],
  "confidence": "high|medium|low"
}"""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        story = ctx.get("blocks", [{}])[-1] if isinstance(context, dict) else {}
        story_content = story.get("content", str(context)) if isinstance(story, dict) else str(context)

        system = self.build_system_prompt()
        return f"""{system}

=== STORY ===
{story_content}

=== PROJECT CONFIG ===
{json.dumps(ctx.get("project_config", {}), indent=2) if isinstance(ctx, dict) and "project_config" in ctx else "No project config available"}

Analyze this story and produce the structured JSON analysis.
"""

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)  # uses default dict+nonempty check


@register_agent
class GrillAgent(BaseAIAgent):
    """QA Grill — challenges the story with probing questions."""

    agent_name: str = "grill"
    agent_role: str = "QA Grill Master"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are a QA Grill Master. Your job is to challenge a software story with probing questions.

Ask questions that reveal:
1. What happens with invalid inputs?
2. What happens without proper authorization?
3. What happens on duplicate requests?
4. What happens on timeout or partial failure?
5. What happens when external dependencies fail?
6. What happens with boundary values?
7. What happens when data already exists?
8. What happens when requests are retried?
9. What happens after partial success?
10. Security: injection, enumeration, CSRF, auth bypass
11. Performance: slow responses, overload
12. Error handling: what errors, what messages, where displayed?

Each question must be SPECIFIC to this story. No generic boilerplate.
Cite the story element that motivates each question.

Output must be valid JSON:
{
  "questions": [
    {"id": "Q1", "question": "...", "motivation": "...", "risk_if_unanswered": "..."}
  ],
  "ambiguities_found": ["list of ambiguities"],
  "missing_requirements": ["list of missing requirements"],
  "risk_flags": ["list of risk flags raised during grilling"],
  "clarification_needed": ["list of items needing human clarification"]
}"""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        story_block = None
        analysis_block = None
        for b in (ctx.get("blocks", []) if isinstance(ctx, dict) else []):
            if b.get("name") == "story":
                story_block = b
            elif b.get("name") == "analysis":
                analysis_block = b

        story_content = story_block.get("content", "") if story_block else (ctx.get("story_text", "") if isinstance(ctx, dict) else str(ctx))
        analysis_content = analysis_block.get("content", "") if analysis_block else ""

        system = self.build_system_prompt()
        return f"""{system}

=== STORY ===
{story_content}

=== ANALYSIS (if available) ===
{analysis_content if analysis_content else "No prior analysis available."}

Challenge this story with probing QA questions.
"""

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)


@register_agent
class RiskAgent(BaseAIAgent):
    """Risk Agent — identifies and assesses QA risks."""

    agent_name: str = "risk"
    agent_role: str = "QA Risk Analyst"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are a QA Risk Analyst. Your job is to identify and assess risks for a software story.

Consider these risk categories (only include relevant ones):
- BUSINESS_RISK: business impact if this is wrong
- TECHNICAL_RISK: implementation complexity, uncertainty
- SECURITY_RISK: auth, data exposure, injection, etc.
- DATA_RISK: data loss, corruption, consistency
- INTEGRATION_RISK: external dependencies, APIs, webhooks
- PERFORMANCE_RISK: load, latency, scalability
- AVAILABILITY_RISK: downtime, failover, recovery
- REGRESSION_RISK: what else could break

Each risk needs:
- risk_id: unique identifier like RR-001
- category: one of the above
- description: what could go wrong
- reason: why this is a risk for THIS story (cite story elements)
- impact: business/technical impact
- likelihood: low/medium/high
- priority: low/medium/high/critical
- affected_area: which part of the system
- mitigation: how to reduce the risk
- evidence: what supports this assessment

DO NOT pad with irrelevant risks. Only include risks that genuinely apply.
Explain WHY each risk applies to this specific story."""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        blocks = ctx.get("blocks", []) if isinstance(ctx, dict) else []

        def find_block(name: str) -> str:
            for b in blocks:
                if b.get("name") == name:
                    return b.get("content", "")
            return ""

        story = find_block("story")
        analysis = find_block("analysis")
        grill = find_block("grill")
        discovery = find_block("discovery")

        system = self.build_system_prompt()
        return f"""{system}

=== STORY ===
{story}

=== ANALYSIS ===
{analysis if analysis else "No analysis available."}

=== GRILL ===
{grill if grill else "No grill results available."}

=== DISCOVERY ===
{discovery if discovery else "No discovery available."}

Identify and assess risks for this story.
"""

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)


@register_agent
class ArchitectAgent(BaseAIAgent):
    """Architect Agent — determines test strategy and architecture."""

    agent_name: str = "architect"
    agent_role: str = "QA Test Architect"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are a QA Test Architect. Your job is to design the test architecture for a software story.

Determine the appropriate test strategy:
- UI/E2E: for user-facing flows (Playwright)
- API: for service-layer testing
- Contract: for API contract validation
- Performance: for load/latency testing
- Security: for auth, injection, etc.
- Accessibility: for WCAG compliance

For each test type, explain:
- WHY it is or is not recommended for THIS story
- What it would test
- What level of the testing pyramid it sits at
- What data/environment it needs

The project uses Playwright for web automation when UI testing is needed.

Output must be valid JSON:
{
  "test_strategy": {
    "ui_e2e": {"recommended": true|false, "rationale": "...", "scope": "..."},
    "api": {"recommended": true|false, "rationale": "...", "scope": "..."},
    "contract": {"recommended": true|false, "rationale": "...", "scope": "..."},
    "performance": {"recommended": true|false, "rationale": "...", "scope": "..."},
    "security": {"recommended": true|false, "rationale": "...", "scope": "..."},
    "accessibility": {"recommended": true|false, "rationale": "...", "scope": "..."}
  },
  "rationale_summary": "Overall reasoning for the test strategy",
  "recommendations": [
    {"recommendation": "...", "priority": "high|medium|low", "why": "..."}
  ]
}"""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        blocks = ctx.get("blocks", []) if isinstance(ctx, dict) else []

        def find_block(name: str) -> str:
            for b in blocks:
                if b.get("name") == name:
                    return b.get("content", "")
            return ""

        story = find_block("story")
        analysis = find_block("analysis")
        grill = find_block("grill")
        discovery = find_block("discovery")

        system = self.build_system_prompt()
        return f"""{system}

=== STORY ===
{story}

=== ANALYSIS ===
{analysis if analysis else "No analysis available."}

=== GRILL ===
{grill if grill else "No grill results available."}

=== DISCOVERY ===
{discovery if discovery else "No discovery available."}

Design the test architecture for this story.
"""

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)


@register_agent
class SpecificationAgent(BaseAIAgent):
    """Specification Agent — transforms requirements into testable specs."""

    agent_name: str = "specification"
    agent_role: str = "QA Specification Writer"
    prompt_version: str = "v1.0"

    def build_system_prompt(self) -> str:
        return """You are a QA Specification Writer. Your job is to transform analyzed requirements into detailed, testable specifications.

For each acceptance criterion, produce a specification entry with:
- spec_id: unique identifier like SPEC-001
- linked_ac: which acceptance criterion this maps to
- preconditions: what must be true before testing
- test_data: specific data needed (from story only, never invented)
- steps: numbered test steps
- expected_results: what PASS looks like
- negative_behavior: what FAIL looks like
- edge_cases: boundary conditions to test
- dependencies: external needs (marked TO_BE_DEFINED if unknown)

Rules:
- Every spec must map to an acceptance criterion
- No orphan specs
- Use only information from the story and analysis
- When exact values are not specified (error messages, URLs, etc.), mark as "TO_BE_DEFINED"
- Do NOT invent business rules, URLs, credentials, or product behavior

Output must be valid JSON:
{
  "specifications": [
    {
      "spec_id": "SPEC-001",
      "linked_ac": "AC1",
      "preconditions": ["..."],
      "test_data": ["..."],
      "steps": ["1. ...", "2. ..."],
      "expected_results": ["..."],
      "negative_behavior": ["..."],
      "edge_cases": ["..."],
      "dependencies": ["..."],
      "notes": "..."
    }
  ],
  "traceability": "summary of how specs map to ACs",
  "gaps": ["specification items that could not be fully defined"],
  "to_be_defined": ["items marked TO_BE_DEFINED"]
}"""

    def build_prompt(self, context: dict | str) -> str:
        ctx = context if isinstance(context, dict) else {}
        blocks = ctx.get("blocks", []) if isinstance(ctx, dict) else []

        def find_block(name: str) -> str:
            for b in blocks:
                if b.get("name") == name:
                    return b.get("content", "")
            return ""

        story = find_block("story")
        analysis = find_block("analysis")
        grill = find_block("grill")

        system = self.build_system_prompt()
        return f"""{system}

=== STORY ===
{story}

=== ANALYSIS ===
{analysis if analysis else "No analysis available."}

=== GRILL ===
{grill if grill else "No grill results available."}

Transform the requirements into detailed testable specifications.
"""

    def validate_output(self, obj: dict) -> tuple[bool, list[str]]:
        return super().validate_output(obj)
