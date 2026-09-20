#!/usr/bin/env python3
"""
Dynamic Skill Selection Engine for the QA Agent Harness.

Selects which skills and specialist agents are relevant for a given story
based on:
  1. Story content (user story, ACs, business rules)
  2. Target project capability map (from project adapter)
  3. Project policy (from project.yaml)

Output: a machine-readable selection report + human-readable summary.
"""

from __future__ import annotations

import json
import os
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Constants ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent


# ── Skill Definitions ────────────────────────────────────────────────────────

SKILLS = {
    "playwright": {
        "name": "Playwright Specialist",
        "category": "web",
        "description": "Web UI automation using Playwright for browser-based testing.",
        "triggers": {
            "story": ["web", "ui", "browser", "click", "form", "navigation", "page", "login", "screen", "dashboard", "visual"],
            "capability": ["web", "playwright"],
            "project": ["application.web", "automation.framework:playwright"],
        },
        "provides": ["test execution", "screenshot evidence", "trace evidence", "UI assertions"],
    },
    "api": {
        "name": "API Specialist",
        "category": "api",
        "description": "REST and GraphQL API testing — status codes, schemas, contracts, error handling.",
        "triggers": {
            "story": ["api", "endpoint", "request", "response", "rest", "graphql", "json", "http", "server", "backend", "service"],
            "capability": ["api", "rest", "graphql"],
            "project": ["api.rest", "api.graphql"],
        },
        "provides": ["API test execution", "schema validation", "contract validation", "status code verification"],
    },
    "webhook": {
        "name": "Webhook Specialist",
        "category": "integration",
        "description": "Webhook payload validation, signature verification, retry handling, idempotency checks.",
        "triggers": {
            "story": ["webhook", "callback", "signature", "payload", "event", "notification", "async", "retry", "idempotent"],
            "capability": ["webhooks"],
            "project": ["api.webhooks"],
        },
        "provides": ["webhook payload testing", "signature verification", "retry testing", "idempotency validation"],
    },
    "database": {
        "name": "Database Specialist",
        "category": "data",
        "description": "SQL/NoSQL data validation, integrity checks, API/UI/database comparison.",
        "triggers": {
            "story": ["database", "data", "sql", "query", "record", "table", "schema", "storage", "persist", "save", "crud"],
            "capability": ["database"],
            "project": ["database.enabled"],
        },
        "provides": ["data validation", "integrity checks", "state verification"],
    },
    "authentication": {
        "name": "Authentication Specialist",
        "category": "security",
        "description": "Session auth, cookies, JWT, API keys, OAuth, MFA/OTP, RBAC, permission testing.",
        "triggers": {
            "story": ["login", "logout", "auth", "session", "token", "jwt", "cookie", "credential", "password", "oauth", "mfa", "factor", "permission", "role", "rbac", "access", "guard"],
            "capability": [],
            "project": [],
        },
        "provides": ["auth flow testing", "session management", "permission validation"],
    },
    "test-data": {
        "name": "Test Data Specialist",
        "category": "data",
        "description": "Fixtures, generated data, unique data, cleanup, API/database setup.",
        "triggers": {
            "story": ["data", "fixture", "seed", "factory", "unique", "generated", "setup", " prerequisit", "existing", "pre-existing"],
            "capability": [],
            "project": [],
        },
        "provides": ["test data generation", "fixtures", "cleanup", "data setup"],
    },
    "contract-testing": {
        "name": "Contract Testing Specialist",
        "category": "integration",
        "description": "OpenAPI/schema/Pact-style validation where appropriate.",
        "triggers": {
            "story": ["schema", "contract", "openapi", "swagger", "pact", "specification", "type", "validate", "structure"],
            "capability": ["api"],
            "project": ["api.rest", "api.graphql"],
        },
        "provides": ["schema validation", "contract verification", "OpenAPI validation"],
    },
    "execution": {
        "name": "Execution Specialist",
        "category": "orchestration",
        "description": "Orchestrates test execution across specialists, collects results, handles timeouts.",
        "triggers": {
            "story": [],
            "capability": [],
            "project": [],
        },
        "provides": ["test execution coordination", "result collection", "timeout handling"],
        "always_selected": True,
    },
    "failure-analysis": {
        "name": "Failure Analysis Specialist",
        "category": "analysis",
        "description": "Classifies test failures: product defect, automation defect, environment, dependency, config, data, network, timeout.",
        "triggers": {
            "story": [],
            "capability": [],
            "project": [],
        },
        "provides": ["failure classification", "root cause analysis", "evidence correlation"],
        "always_selected": True,
    },
    "evidence": {
        "name": "Evidence Specialist",
        "category": "orchestration",
        "description": "Collects and consolidates test evidence: screenshots, traces, logs, request IDs, correlation IDs.",
        "triggers": {
            "story": [],
            "capability": [],
            "project": [],
        },
        "provides": ["evidence collection", "artifact consolidation", "observability"],
        "always_selected": True,
    },
    "security": {
        "name": "Security Specialist",
        "category": "security",
        "description": "Safe QA-level OWASP-oriented checks.",
        "triggers": {
            "story": ["security", "inject", "xss", "csrf", "sql injection", "auth", "secure", "https", "token", "vulnerability", "attack", "exploit"],
            "capability": [],
            "project": ["security.enabled"],
        },
        "provides": ["OWASP checks", "security validation", "vulnerability scanning"],
    },
    "accessibility": {
        "name": "Accessibility Specialist",
        "category": "quality",
        "description": "WCAG-oriented checks and axe integration where applicable.",
        "triggers": {
            "story": ["accessibility", "a11y", "wcag", "screen reader", "keyboard", "aria", "alt text", "contrast", "focus"],
            "capability": ["web"],
            "project": ["accessibility"],
        },
        "provides": ["WCAG validation", "axe integration", "accessibility reporting"],
    },
    "visual-testing": {
        "name": "Visual Testing Specialist",
        "category": "quality",
        "description": "Screenshot comparison where applicable.",
        "triggers": {
            "story": ["visual", "screenshot", " ui", "pixel", "css", "styling", "layout", "responsive"],
            "capability": ["web"],
            "project": ["visual"],
        },
        "provides": ["visual regression", "screenshot diffing", "layout validation"],
    },
    "mocking": {
        "name": "Mocking Specialist",
        "category": "integration",
        "description": "Mock servers, stubbing, API response mocking, network interception.",
        "triggers": {
            "story": ["mock", "stub", "fake", "intercept", "replace", "simulate", "third party", "external", "dependency"],
            "capability": [],
            "project": [],
        },
        "provides": ["mock server setup", "response stubbing", "dependency simulation"],
    },
    "performance": {
        "name": "Performance Specialist",
        "category": "quality",
        "description": "k6/JMeter/Locust integration architecture.",
        "triggers": {
            "story": ["performance", "load", "stress", "benchmark", "latency", "throughput", "response time", "slow", " scalable", "capacity"],
            "capability": [],
            "project": ["performance.enabled"],
        },
        "provides": ["load testing", "performance measurement", "benchmark execution"],
    },
    "ci-cd": {
        "name": "CI/CD Specialist",
        "category": "orchestration",
        "description": "Generates or updates test pipeline configuration for GitHub Actions, GitLab CI, Azure DevOps, Jenkins.",
        "triggers": {
            "story": ["ci", "pipeline", "github actions", "gitlab", "azure devops", "jenkins", "automation", "continuous"],
            "capability": ["ci"],
            "project": ["ci.provider"],
        },
        "provides": ["pipeline generation", "CI configuration", "test integration"],
    },
}


# ── Skill Selection Engine ───────────────────────────────────────────────────

class SkillSelector:
    """Selects skills and specialist agents based on story content and project context."""

    def __init__(self, story_text: str, project_config: dict, capability_map: dict | None = None):
        self.story_text = story_text.lower()
        self.project_config = project_config
        self.capability_map = capability_map or {}
        self._sections = self._parse_sections(story_text)

    def _parse_sections(self, text: str) -> dict:
        """Parse story markdown into sections."""
        sections = {}
        current = None
        current_lines = []
        for line in text.splitlines():
            if line.startswith("## ") and not line.startswith("### "):
                if current is not None:
                    sections[current] = "\n".join(current_lines).strip()
                current = line[3:].strip()
                current_lines = []
            else:
                if current is not None:
                    current_lines.append(line)
        if current is not None:
            sections[current] = "\n".join(current_lines).strip()
        return sections

    def _story_matches(self, triggers: list[str]) -> bool:
        """Check if story content matches any of the trigger keywords."""
        if not triggers:
            return False
        for trigger in triggers:
            if trigger in self.story_text:
                return True
        return False

    def _capability_matches(self, triggers: list[str]) -> bool:
        """Check if capability map matches any of the trigger keys."""
        if not triggers:
            return True  # No capability requirement = always pass
        for key in triggers:
            if key in self.capability_map and self.capability_map[key]:
                return True
            # Also check nested keys like "automation.framework"
            if ":" in key:
                parts = key.split(":")
                if len(parts) == 2:
                    outer = self.capability_map.get(parts[0], {})
                    if isinstance(outer, dict) and outer.get(parts[1]):
                        return True
        return False

    def _project_matches(self, conditions: list[str]) -> bool:
        """Check if project.yaml conditions are met."""
        if not conditions:
            return True
        for cond in conditions:
            # Handle "key:value" format
            if ":" in cond:
                parts = cond.split(":")
                if len(parts) == 2:
                    # Navigate nested dict
                    d = self.project_config
                    for k in parts[0].split("."):
                        d = d.get(k, {})
                    if isinstance(d, dict):
                        val = d.get(parts[1])
                        if val:
                            return True
            else:
                # Simple key check
                for k in cond.split("."):
                    if k in self.project_config:
                        v = self.project_config[k]
                        if isinstance(v, dict):
                            # Check if any value is truthy
                            if any(v.values()):
                                return True
                        elif v:
                            return True
        return False

    def select(self) -> dict:
        """Select skills based on story + capability map + project config.

        Selection logic (conservative, story-driven):
        1. Skills with always_selected=True are always included (execution,
           failure-analysis, evidence — core orchestration).
        2. Skills WITH story triggers: require story match. Capability and
           project config are secondary signals (capability match can add,
           but won't select without story or capability signal).
        3. Skills WITHOUT story triggers (generic): require capability or
           project match.

        Returns:
            Dict with selected, rejected, rationale.
        """
        selected = []
        rejected = []
        rationale = {}

        for skill_key, skill_def in SKILLS.items():
            # Always-selected core skills
            if skill_def.get("always_selected"):
                selected.append(skill_key)
                rationale[skill_key] = "Always selected — core orchestration capability."
                continue

            has_story_triggers = bool(skill_def["triggers"]["story"])
            story_match = self._story_matches(skill_def["triggers"]["story"])
            cap_match = self._capability_matches(skill_def["triggers"]["capability"])
            proj_match = self._project_matches(skill_def["triggers"]["project"])

            if has_story_triggers:
                # Skills with story triggers: story match required.
                # Capability match is a bonus signal for rationale.
                if story_match:
                    selected.append(skill_key)
                    reasons = ["story content matches skill triggers"]
                    if cap_match:
                        reasons.append("target capability map confirms this skill is applicable")
                    rationale[skill_key] = "; ".join(reasons)
                else:
                    rejected.append((skill_key,
                        "No story trigger match — this skill is not indicated by the story content."))
                    rationale[skill_key] = "Not selected"
            else:
                # Skills without story triggers: need BOTH capability AND project match
                # OR have a project config flag that explicitly enables them
                proj_flag_found = False
                for proj_cond in skill_def["triggers"]["project"]:
                    if ":" in proj_cond:
                        parts = proj_cond.split(":")
                        if len(parts) == 2:
                            d = self.project_config
                            for k in parts[0].split("."):
                                d = d.get(k, {})
                            if isinstance(d, dict) and d.get(parts[1]):
                                proj_flag_found = True
                                break
                    else:
                        for k in proj_cond.split("."):
                            if k in self.project_config:
                                v = self.project_config[k]
                                if isinstance(v, dict):
                                    if any(v.values()):
                                        proj_flag_found = True
                                        break
                                elif v:
                                    proj_flag_found = True
                                    break

                if cap_match and proj_flag_found:
                    selected.append(skill_key)
                    reasons = []
                    if cap_match:
                        reasons.append("target capability map supports this skill")
                    if proj_flag_found:
                        reasons.append("project configuration explicitly enables this skill")
                    rationale[skill_key] = "; ".join(reasons)
                else:
                    rejected.append((skill_key,
                        "No capability AND project config signal — this skill is not needed."))
                    rationale[skill_key] = "Not selected"

        return {
            "selected": selected,
            "rejected": rejected,
            "rationale": rationale,
        }

    def generate_report(self, selection_result: dict) -> str:
        """Generate a human-readable skill selection report."""
        lines = []
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        lines.extend([
            "# Skill Selection Report",
            "",
            f"**Generated:** {now}",
            "",
            "---",
            "",
            "## 1. Selection Summary",
            "",
            f"**Total skills available:** {len(SKILLS)}",
            f"**Skills selected:** {len(selection_result['selected'])}",
            f"**Skills not selected:** {len(selection_result['rejected'])}",
            "",
            "### Selected Skills",
            "",
        ])

        for sk in selection_result["selected"]:
            defn = SKILLS[sk]
            lines.append(f"- **{defn['name']}** ({sk})")
            lines.append(f"  - Category: {defn['category']}")
            lines.append(f"  - Rationale: {selection_result['rationale'][sk]}")
            lines.append(f"  - Provides: {', '.join(defn['provides'])}")
            lines.append("")

        if selection_result["rejected"]:
            lines.extend([
                "### Not Selected (Rejected)",
                "",
            ])
            for sk, reason in selection_result["rejected"]:
                defn = SKILLS[sk]
                lines.append(f"- **{defn['name']}** ({sk}) — {reason}")
            lines.append("")

        # Capability map summary
        if self.capability_map:
            lines.extend([
                "## 2. Target Capability Map (used for selection)",
                "",
            ])
            for k, v in sorted(self.capability_map.items()):
                if isinstance(v, bool):
                    lines.append(f"- **{k}:** {v}")
                elif isinstance(v, str):
                    lines.append(f"- **{k}:** {v}")
            lines.append("")

        # Story content summary
        lines.extend([
            "## 3. Story Content Analyzed",
            "",
        ])
        if self._sections:
            for sec_name, sec_content in self._sections.items():
                preview = sec_content[:200].replace("\n", " ") if sec_content else "(empty)"
                lines.append(f"- **{sec_name}:** {preview}...")
        else:
            lines.append("- No sections parsed from story.")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*Skill selection performed by qa-run runtime. Selection is based on story content, target project capability map, and project.yaml configuration. Skills not selected are not needed for this story.*")

        return "\n".join(lines)


# ── Specialist Agent Base ────────────────────────────────────────────────────

class SpecialistAgent:
    """Base class for specialist execution agents."""

    def __init__(self, story_id: str, project_config: dict, target_path: Path | None,
                 adapter=None):
        self.story_id = story_id
        self.project_config = project_config
        self.target_path = target_path
        self.adapter = adapter
        self.results = []

    def can_execute(self) -> bool:
        """Check if this specialist can execute (environment, config, etc.)."""
        raise NotImplementedError

    def execute(self, scenarios: list[dict]) -> list[dict]:
        """Execute assigned scenarios. Returns execution results."""
        raise NotImplementedError

    def get_name(self) -> str:
        raise NotImplementedError


# ── Playwright Specialist Agent ─────────────────────────────────────────────

class PlaywrightAgent(SpecialistAgent):
    """Playwright specialist — executes web UI tests against target project."""

    def get_name(self) -> str:
        return "Playwright Specialist"

    def can_execute(self) -> bool:
        """Check if Playwright execution is possible."""
        if self.target_path is None or not self.target_path.is_dir():
            return False
        # Check for Playwright config in target
        playwright_configs = list(self.target_path.glob("playwright.config.*"))
        if not playwright_configs:
            return False
        # Check for test files
        test_files = list(self.target_path.rglob("*.spec.js")) + \
                     list(self.target_path.rglob("*.spec.ts")) + \
                     list(self.target_path.rglob("*.test.js")) + \
                     list(self.target_path.rglob("*.test.ts"))
        if not test_files:
            return False
        # Check for node_modules with playwright
        if not (self.target_path / "node_modules").is_dir():
            return False
        return True

    def _find_test_command(self) -> str | None:
        """Find the test command from package.json."""
        if self.target_path is None:
            return None
        pkg = self.target_path / "package.json"
        if not pkg.exists():
            return None
        try:
            import json as _json
            with open(pkg) as f:
                data = _json.load(f)
            scripts = data.get("scripts", {})
            for name in ["test", "test:e2e", "test:ui"]:
                if name in scripts:
                    return f"npm run {name}"
            return None
        except (OSError, json.JSONDecodeError):
            return None

    def execute(self, scenarios: list[dict]) -> list[dict]:
        """Execute Playwright tests. Returns execution results per scenario."""
        if not self.can_execute():
            return [{
                "status": "blocked",
                "reason": "Playwright environment not available — missing config, test files, or node_modules.",
                "scenario_count": len(scenarios),
            }]

        command = self._find_test_command()
        if command is None:
            return [{
                "status": "blocked",
                "reason": "No test command found in package.json.",
                "scenario_count": len(scenarios),
            }]

        # Execute the command in target repo
        if self.adapter:
            result = self.adapter.execute_command(command, working_directory=self.target_path, timeout=300)
        else:
            import subprocess, time
            start = time.time()
            try:
                proc = subprocess.run(command, shell=True, cwd=str(self.target_path),
                                       capture_output=True, text=True, timeout=300)
                duration = time.time() - start
                result = {
                    "status": "completed" if proc.returncode == 0 else "failed",
                    "command": command,
                    "exit_code": proc.returncode,
                    "duration": round(duration, 2),
                    "stdout": proc.stdout[:50000],
                    "stderr": proc.stderr[:50000],
                    "artifacts": [],
                    "errors": [],
                }
            except subprocess.TimeoutExpired:
                result = {
                    "status": "timeout",
                    "command": command,
                    "exit_code": -1,
                    "duration": 300,
                    "stdout": "",
                    "stderr": "Command timed out after 300 seconds.",
                    "artifacts": [],
                    "errors": ["timeout"],
                }

        # Map result to scenarios
        scenario_results = []
        for i, scenario in enumerate(scenarios):
            scenario_results.append({
                "scenario_id": scenario.get("id", f"SC-{i+1}"),
                "scenario_name": scenario.get("name", "Unknown"),
                "status": "passed" if result.get("status") == "completed" else "failed",
                "execution_status": result.get("status", "unknown"),
                "exit_code": result.get("exit_code", -1),
                "duration": result.get("duration", 0),
                "stdout": result.get("stdout", "")[:2000],
                "stderr": result.get("stderr", "")[:2000],
                "artifacts": result.get("artifacts", []),
                "errors": result.get("errors", []),
            })

        self.results = scenario_results
        return scenario_results


# ── API Specialist Agent ─────────────────────────────────────────────────────

class APIAgent(SpecialistAgent):
    """API specialist — executes REST API tests against target project."""

    def get_name(self) -> str:
        return "API Specialist"

    def can_execute(self) -> bool:
        """Check if API execution is possible."""
        if self.target_path is None or not self.target_path.is_dir():
            return False
        # Check for API server or test files
        has_server = (self.target_path / "server.js").exists() or \
                     (self.target_path / "server.py").exists() or \
                     (self.target_path / "app.py").exists()
        has_api_tests = bool(list(self.target_path.rglob("*.spec.js")) or
                             list(self.target_path.rglob("*.spec.ts")) or
                             list(self.target_path.rglob("*api*test*")))
        return has_server or has_api_tests

    def _find_api_url(self) -> str | None:
        """Find API base URL from playwright config or project config."""
        if self.target_path is None:
            return None
        # Try playwright config
        for cfg in self.target_path.glob("playwright.config.*"):
            try:
                import re
                content = cfg.read_text()
                m = re.search(r'baseURL\s*:\s*["\']([^"\']+)["\']', content)
                if m:
                    return m.group(1)
            except OSError:
                pass
        # Fall back to project config
        env = self.project_config.get("environments", {})
        if env.get("dev"):
            return "http://localhost:3000"  # default fallback
        return "http://localhost:3000"

    def execute(self, scenarios: list[dict]) -> list[dict]:
        """Execute API tests. Returns execution results per scenario."""
        if self.target_path is None:
            return [{
                "status": "blocked",
                "reason": "No target repository configured.",
                "scenario_count": len(scenarios),
            }]

        api_url = self._find_api_url()
        results = []

        for i, scenario in enumerate(scenarios):
            scenario_result = {
                "scenario_id": scenario.get("id", f"SC-{i+1}"),
                "scenario_name": scenario.get("name", "Unknown"),
                "status": "unknown",
                "api_url": api_url,
                "details": {},
            }

            # Try to execute API request if scenario has request info
            request_info = scenario.get("request") or scenario.get("api_request")
            if request_info and api_url:
                try:
                    import urllib.request
                    import urllib.error
                    import json as json_lib

                    url = api_url + request_info.get("path", "")
                    method = request_info.get("method", "GET").upper()
                    headers = request_info.get("headers", {})
                    body = request_info.get("body")

                    req = urllib.request.Request(url, data=body.encode() if body else None,
                                                 headers=headers, method=method)
                    try:
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            content = resp.read().decode()
                            scenario_result["status"] = "passed"
                            scenario_result["http_status"] = resp.status
                            scenario_result["response"] = content[:2000]
                    except urllib.error.HTTPError as e:
                        scenario_result["status"] = "failed"
                        scenario_result["http_status"] = e.code
                        scenario_result["error"] = str(e)
                    except urllib.error.URLError as e:
                        scenario_result["status"] = "blocked"
                        scenario_result["error"] = f"Connection failed: {e}"
                except Exception as e:
                    scenario_result["status"] = "error"
                    scenario_result["error"] = str(e)
            else:
                scenario_result["status"] = "blocked"
                scenario_result["reason"] = "No API request details in scenario — scenario requires manual API test implementation."

            results.append(scenario_result)

        self.results = results
        return results


# ── Factory ──────────────────────────────────────────────────────────────────

def create_specialist_agent(agent_type: str, story_id: str, project_config: dict,
                             target_path: Path | None, adapter=None) -> SpecialistAgent | None:
    """Create a specialist agent by type."""
    agents = {
        "playwright": PlaywrightAgent,
        "api": APIAgent,
    }
    cls = agents.get(agent_type)
    if cls is None:
        return None
    return cls(story_id, project_config, target_path, adapter)


def select_and_report(story_text: str, project_config: dict,
                       capability_map: dict | None = None) -> dict:
    """Convenience function: select skills and generate report."""
    selector = SkillSelector(story_text, project_config, capability_map)
    selection = selector.select()
    report = selector.generate_report(selection)
    return {
        "selection": selection,
        "report": report,
        "selector": selector,
    }
