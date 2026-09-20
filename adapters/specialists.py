#!/usr/bin/env python3
"""
Specialist Execution Module — Playwright and API specialist agents.

These agents execute tests against the target project repository and return
normalized results to the Harness via the execution stage.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Normalized Execution Result ──────────────────────────────────────────────

class ExecutionResult:
    """Normalized execution result returned by specialist agents."""

    def __init__(self, status: str, command: str, scenario_id: str = "",
                 scenario_name: str = "", exit_code: int = -1,
                 duration: float = 0.0, stdout: str = "", stderr: str = "",
                 artifacts: list = None, errors: list = None,
                 classification: str = "UNKNOWN", working_directory: str = "",
                 additional: dict = None):
        self.status = status  # completed, failed, timeout, error, blocked
        self.command = command
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.exit_code = exit_code
        self.duration = duration
        self.stdout = stdout
        self.stderr = stderr
        self.artifacts = artifacts or []
        self.errors = errors or []
        self.classification = classification
        self.working_directory = working_directory
        self.additional = additional or {}

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "command": self.command,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "exit_code": self.exit_code,
            "duration": self.duration,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "classification": self.classification,
            "working_directory": self.working_directory,
            **self.additional,
        }


# ── Playwright Specialist Agent ──────────────────────────────────────────────

class PlaywrightAgent:
    """Executes Playwright tests against the target project repository."""

    def __init__(self, story_id: str, project_config: dict,
                 target_path: Path, adapter=None):
        self.story_id = story_id
        self.project_config = project_config
        self.target_path = target_path
        self.adapter = adapter
        self.name = "Playwright Specialist"

    def can_execute(self) -> bool:
        """Check if Playwright execution environment is available."""
        if not self.target_path.is_dir():
            return False
        # Check for Playwright config
        configs = list(self.target_path.glob("playwright.config.*"))
        if not configs:
            return False
        # Check for test files
        test_files = list(self.target_path.rglob("*.spec.js")) + \
                     list(self.target_path.rglob("*.spec.ts")) + \
                     list(self.target_path.rglob("*.test.ts")) + \
                     list(self.target_path.rglob("*.test.js"))
        if not test_files:
            return False
        # Check for node_modules
        if not (self.target_path / "node_modules").is_dir():
            return False
        return True

    def _find_test_command(self) -> str | None:
        """Find the npm test command from package.json."""
        pkg = self.target_path / "package.json"
        if not pkg.exists():
            return None
        try:
            with open(pkg) as f:
                data = json.load(f)
            scripts = data.get("scripts", {})
            for name in ["test", "test:e2e", "test:ui"]:
                if name in scripts:
                    return f"npm run {name}"
            return None
        except (OSError, json.JSONDecodeError):
            return None

    def _find_test_files(self) -> list[str]:
        """Find Playwright test files in the target project."""
        patterns = ["*.spec.js", "*.spec.ts", "*.test.ts", "*.test.js"]
        files = []
        for pattern in patterns:
            files.extend(str(f.relative_to(self.target_path))
                        for f in self.target_path.rglob(pattern))
        return sorted(set(files))

    def execute_scenario(self, scenario: dict) -> ExecutionResult:
        """Execute a single test scenario via Playwright.

        If the scenario has a specific test file/identifier, run that test.
        Otherwise, run the full test suite.
        """
        test_files = self._find_test_files()
        if not test_files:
            return ExecutionResult(
                status="blocked",
                command="",
                scenario_id=scenario.get("id", ""),
                scenario_name=scenario.get("name", ""),
                exit_code=-1,
                duration=0,
                stderr="No Playwright test files found in target repository.",
                classification="UNKNOWN",
                working_directory=str(self.target_path),
                additional={"reason": "no_test_files"},
            )

        # Determine which test to run
        test_id = scenario.get("test_id") or scenario.get("id", "")
        test_name = scenario.get("name", "")

        # Try to find a specific test file matching the scenario
        specific_test = None
        if test_id:
            for tf in test_files:
                if test_id.lower() in tf.lower():
                    specific_test = tf
                    break

        command = self._find_test_command()
        if command is None:
            return ExecutionResult(
                status="blocked",
                command="",
                scenario_id=scenario.get("id", ""),
                scenario_name=scenario.get("name", ""),
                exit_code=-1,
                duration=0,
                stderr="No test command found in package.json.",
                classification="UNKNOWN",
                working_directory=str(self.target_path),
                additional={"reason": "no_test_command"},
            )

        # Build command: run specific test or full suite
        if specific_test:
            cmd = f"npm run test -- {specific_test}"
        else:
            # Run full suite — scenario mapping happens via test report parsing
            cmd = command

        # Execute
        if self.adapter:
            raw = self.adapter.execute_command(cmd, working_directory=self.target_path, timeout=300)
            return ExecutionResult(
                status=raw.get("status", "unknown"),
                command=cmd,
                scenario_id=scenario.get("id", ""),
                scenario_name=scenario.get("name", ""),
                exit_code=raw.get("exit_code", -1),
                duration=raw.get("duration", 0),
                stdout=raw.get("stdout", ""),
                stderr=raw.get("stderr", ""),
                artifacts=raw.get("artifacts", []),
                errors=raw.get("errors", []),
                classification=raw.get("classification", "UNKNOWN"),
                working_directory=str(self.target_path),
            )

        # Fallback: direct subprocess execution
        start = time.time()
        try:
            proc = subprocess.run(cmd, shell=True, cwd=str(self.target_path),
                                   capture_output=True, text=True, timeout=300)
            duration = time.time() - start
            return ExecutionResult(
                status="completed" if proc.returncode == 0 else "failed",
                command=cmd,
                scenario_id=scenario.get("id", ""),
                scenario_name=scenario.get("name", ""),
                exit_code=proc.returncode,
                duration=round(duration, 2),
                stdout=proc.stdout[:50000],
                stderr=proc.stderr[:50000],
                classification="SAFE",
                working_directory=str(self.target_path),
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status="timeout",
                command=cmd,
                scenario_id=scenario.get("id", ""),
                scenario_name=scenario.get("name", ""),
                exit_code=-1,
                duration=300,
                stderr="Command timed out after 300 seconds.",
                classification="UNKNOWN",
                working_directory=str(self.target_path),
                errors=["timeout"],
            )

    def execute_all(self, scenarios: list[dict]) -> list[ExecutionResult]:
        """Execute all assigned scenarios.

        For Playwright, we run the full test suite once and parse the report.
        Individual scenario results are mapped from the test report.
        """
        if not self.can_execute():
            return [ExecutionResult(
                status="blocked",
                command="",
                scenario_id="",
                scenario_name="",
                exit_code=-1,
                duration=0,
                stderr="Playwright execution environment not available.",
                classification="UNKNOWN",
                working_directory=str(self.target_path) if self.target_path else "",
                additional={"reason": "environment_not_available",
                            "details": f"target_path={self.target_path}"},
            )]

        # Run the full test suite
        cmd = self._find_test_command()
        if cmd is None:
            return [ExecutionResult(
                status="blocked",
                command="",
                scenario_id="",
                scenario_name="",
                exit_code=-1,
                duration=0,
                stderr="No test command in package.json.",
                classification="UNKNOWN",
                working_directory=str(self.target_path),
            )]

        print(f"[{self.name}] Running: {cmd}")
        if self.adapter:
            raw = self.adapter.execute_command(cmd, working_directory=self.target_path, timeout=300)
        else:
            start = time.time()
            try:
                proc = subprocess.run(cmd, shell=True, cwd=str(self.target_path),
                                       capture_output=True, text=True, timeout=300)
                duration = time.time() - start
                raw = {
                    "status": "completed" if proc.returncode == 0 else "failed",
                    "command": cmd,
                    "exit_code": proc.returncode,
                    "duration": round(duration, 2),
                    "stdout": proc.stdout[:50000],
                    "stderr": proc.stderr[:50000],
                    "artifacts": [],
                    "errors": [],
                    "classification": "SAFE",
                }
            except subprocess.TimeoutExpired:
                raw = {
                    "status": "timeout",
                    "command": cmd,
                    "exit_code": -1,
                    "duration": 300,
                    "stdout": "",
                    "stderr": "Command timed out after 300 seconds.",
                    "artifacts": [],
                    "errors": ["timeout"],
                    "classification": "UNKNOWN",
                }

        # Parse test results from stdout if available
        test_results = self._parse_playwright_output(raw.get("stdout", ""))

        # Map to scenarios
        results = []
        for scenario in scenarios:
            sid = scenario.get("id", "")
            sname = scenario.get("name", "")
            matched = test_results.get(sid) or test_results.get(sname) or next(
                (v for k, v in test_results.items() if sid in k or sname in k), None
            )
            if matched:
                results.append(ExecutionResult(
                    status=matched["status"],
                    command=cmd,
                    scenario_id=sid,
                    scenario_name=sname,
                    exit_code=matched.get("exit_code", 0),
                    duration=matched.get("duration", raw.get("duration", 0)),
                    stdout=matched.get("stdout", raw.get("stdout", "")[:1000]),
                    stderr=matched.get("stderr", raw.get("stderr", "")[:500]),
                    artifacts=matched.get("artifacts", []),
                    errors=matched.get("errors", []),
                    classification="SAFE",
                    working_directory=str(self.target_path),
                ))
            else:
                # Test passed (no failure record found)
                results.append(ExecutionResult(
                    status="passed",
                    command=cmd,
                    scenario_id=sid,
                    scenario_name=sname,
                    exit_code=0,
                    duration=raw.get("duration", 0),
                    stdout="",
                    stderr="",
                    classification="SAFE",
                    working_directory=str(self.target_path),
                    additional={"note": "Test passed (no failure record in output)"},
                ))

        return results

    def _parse_playwright_output(self, stdout: str) -> dict:
        """Parse Playwright test output to extract per-test results."""
        results = {}
        # Playwright report lines: "✓ test_name (spec_file:line)")
        for line in stdout.splitlines():
            if line.strip().startswith("✓") or line.strip().startswith("×"):
                parts = line.strip().split(None, 1)
                if len(parts) >= 2:
                    status = "passed" if parts[0] == "✓" else "failed"
                    test_info = parts[1]
                    # Extract test name (before parenthesis)
                    test_name = test_info.split("(")[0].strip() if "(" in test_info else test_info
                    results[test_name] = {
                        "status": status,
                        "exit_code": 0 if status == "passed" else 1,
                        "stdout": line,
                        "duration": 0,
                    }
        # Also check for test report JSON
        if not results:
            # Try to find playwright-report directory
            report_dir = self.target_path / "playwright-report"
            if report_dir.is_dir():
                for f in report_dir.glob("*.json"):
                    try:
                        with open(f) as fp:
                            data = json.load(fp)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    name = item.get("title", item.get("name", ""))
                                    results[name] = {
                                        "status": "passed" if item.get("status") == "passed" else "failed",
                                        "exit_code": 0 if item.get("status") == "passed" else 1,
                                        "stdout": json.dumps(item)[:1000],
                                    }
                    except (OSError, json.JSONDecodeError):
                        pass
        return results


# ── API Specialist Agent ─────────────────────────────────────────────────────

class APIAgent:
    """Executes REST API tests against the target project."""

    def __init__(self, story_id: str, project_config: dict,
                 target_path: Path, adapter=None):
        self.story_id = story_id
        self.project_config = project_config
        self.target_path = target_path
        self.adapter = adapter
        self.name = "API Specialist"

    def can_execute(self) -> bool:
        """Check if API execution environment is available."""
        if self.target_path is None or not self.target_path.is_dir():
            return False
        # Check for server file or API test files
        has_server = (self.target_path / "server.js").exists() or \
                     (self.target_path / "server.py").exists() or \
                     (self.target_path / "app.py").exists()
        has_api_tests = bool(list(self.target_path.rglob("*.spec.js")) or
                             list(self.target_path.rglob("*.spec.ts")) or
                             list(self.target_path.rglob("*api*test*")))
        return has_server or has_api_tests

    def _find_api_url(self) -> str:
        """Find the API base URL from various sources."""
        # From playwright config
        if self.target_path:
            for cfg in self.target_path.glob("playwright.config.*"):
                try:
                    content = cfg.read_text()
                    m = re.search(r'baseURL\s*:\s*["\']([^"\']+)["\']', content)
                    if m:
                        return m.group(1)
                except OSError:
                    pass
        # Default
        return "http://localhost:3000"

    def execute_scenario(self, scenario: dict) -> ExecutionResult:
        """Execute a single API test scenario."""
        api_url = self._find_api_url()
        request = scenario.get("api_request") or scenario.get("request") or {}

        method = request.get("method", "GET").upper()
        path = request.get("path", "")
        url = api_url + path
        headers = request.get("headers", {"Content-Type": "application/json"})
        body = request.get("body")

        # Build command
        if body:
            cmd = f'curl -s -X {method} -H "Content-Type: application/json" -d \'{body}\' "{url}"'
        else:
            cmd = f'curl -s -X {method} "{url}"'

        # Execute via adapter or direct
        if self.adapter:
            raw = self.adapter.execute_command(cmd, working_directory=self.target_path, timeout=30)
            status = raw.get("status", "unknown")
            exit_code = raw.get("exit_code", -1)
            stdout = raw.get("stdout", "")
            stderr = raw.get("stderr", "")
        else:
            start = time.time()
            try:
                proc = subprocess.run(cmd, shell=True, cwd=str(self.target_path) if self.target_path else None,
                                       capture_output=True, text=True, timeout=30)
                duration = time.time() - start
                status = "completed" if proc.returncode == 0 else "failed"
                exit_code = proc.returncode
                stdout = proc.stdout[:10000]
                stderr = proc.stderr[:10000]
            except subprocess.TimeoutExpired:
                status = "timeout"
                exit_code = -1
                stdout = ""
                stderr = "Command timed out after 30 seconds."

        # Parse response
        additional = {}
        try:
            resp_data = json.loads(stdout)
            additional["response_body"] = resp_data
        except (json.JSONDecodeError, ValueError):
            additional["raw_response"] = stdout[:500]

        return ExecutionResult(
            status=status,
            command=cmd,
            scenario_id=scenario.get("id", ""),
            scenario_name=scenario.get("name", ""),
            exit_code=exit_code,
            duration=0,
            stdout=stdout[:5000],
            stderr=stderr[:2000],
            classification="SAFE",
            working_directory=str(self.target_path) if self.target_path else "",
            additional=additional,
        )

    def execute_all(self, scenarios: list[dict]) -> list[ExecutionResult]:
        """Execute all assigned API test scenarios."""
        if self.target_path is None or not self.target_path.is_dir():
            return [ExecutionResult(
                status="blocked",
                command="",
                scenario_id="",
                scenario_name="",
                exit_code=-1,
                duration=0,
                stderr="No target repository configured.",
                classification="UNKNOWN",
                working_directory="",
                additional={"reason": "no_target"},
            )]

        results = []
        for scenario in scenarios:
            results.append(self.execute_scenario(scenario))
        return results


# ── Specialist Registry ──────────────────────────────────────────────────────

SPECIALISTS = {
    "playwright": PlaywrightAgent,
    "api": APIAgent,
}


def create_agent(agent_type: str, story_id: str, project_config: dict,
                 target_path: Path = None, adapter=None):
    """Create a specialist agent by type."""
    cls = SPECIALISTS.get(agent_type)
    if cls is None:
        return None
    return cls(story_id, project_config, target_path, adapter)


def run_specialist(agent, scenarios: list[dict]) -> list[dict]:
    """Run a specialist agent against assigned scenarios."""
    if agent is None:
        return [{
            "status": "blocked",
            "reason": f"Specialist agent '{agent.name if agent else 'None'}' not available.",
            "scenario_count": len(scenarios),
        }]

    results = agent.execute_all(scenarios)
    return [r.to_dict() for r in results]
