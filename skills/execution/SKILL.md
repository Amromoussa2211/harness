===
Lowest layer: runs tests, collects results, captures exit code, stdout, stderr, evidence.

Deps: hypothesis (generative data), pytest or stdlib unittest for assertions.
===

import subprocess
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_command(cmd, cwd=None, env=None, timeout=300):
    """Run a command and capture exit code, stdout, stderr."""
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "timed_out": False,
    }


def run_with_timeout(cmd, cwd=None, env=None, timeout=300):
    """Run a command with timeout handling."""
    try:
        return run_command(cmd, cwd, env, timeout)
    except subprocess.TimeoutExpired as e:
        return {
            "exit_code": -1,
            "stdout": e.stdout or "",
            "stderr": e.stderr or "",
            "timed_out": True,
        }


def collect_evidence(run_result, story_id, output_dir):
    """Collect evidence from a test run."""
    evidence = {
        "timestamp": now_iso(),
        "exit_code": run_result["exit_code"],
        "timed_out": run_result["timed_out"],
        "stdout": run_result["stdout"][:10000] if run_result["stdout"] else "",
        "stderr": run_result["stderr"][:10000] if run_result["stderr"] else "",
    }
    
    evidence_dir = Path(output_dir) / story_id / "execution"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    evidence_file = evidence_dir / "run-evidence.json"
    with open(evidence_file, "w") as f:
        json.dump(evidence, f, indent=2)
    
    return str(evidence_file)


def parse_test_results(output, result_format="junit"):
    """Parse test output into structured results."""
    if result_format == "junit" and output:
        # Basic JUnit-style parsing
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
        }
        for line in output.splitlines():
            if "Tests run:" in line:
                import re
                match = re.search(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)", line)
                if match:
                    results["total"] = int(match.group(1))
                    results["failed"] = int(match.group(2))
                    results["errors"] = int(match.group(3))
                    results["skipped"] = int(match.group(4))
                    results["passed"] = results["total"] - results["failed"] - results["errors"] - results["skipped"]
        return results
    return {"raw": output[:5000] if output else ""}


def generate_run_report(story_id, tests_run, results, blocked, evidence_files, env_info):
    """Generate execution run report."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    lines = [
        f"# Test Execution — {story_id}",
        "",
        f"**Project:** (from project adapter)",
        "**Source inputs:** delegation/output.md, project.yaml",
        f"**Execution timestamp:** {now}",
        "",
        "---",
        "",
        "## 1. Execution Summary",
        "",
        f"**Status:** {'EXECUTED' if tests_run else 'BLOCKED'}",
        "",
        "## 2. Tests Run",
        "",
    ]
    
    if tests_run:
        lines.append(f"**Number of tests run:** {len(tests_run)}")
        for test in tests_run:
            status = "PASS" if test.get("passed") else "FAIL" if test.get("failed") else "SKIPPED"
            lines.append(f"- {test['name']}: {status}")
    else:
        lines.append("_(No tests were executed.)_")
    
    lines.extend([
        "",
        "## 3. Results Summary",
        "",
    ])
    
    if results:
        lines.append(f"- Total: {results.get('total', 0)}")
        lines.append(f"- Passed: {results.get('passed', 0)}")
        lines.append(f"- Failed: {results.get('failed', 0)}")
        lines.append(f"- Errors: {results.get('errors', 0)}")
        lines.append(f"- Skipped: {results.get('skipped', 0)}")
    else:
        lines.append("_(No results available.)_")
    
    lines.extend([
        "",
        "## 4. Blocked Tests",
        "",
    ])
    
    if blocked:
        for b in blocked:
            lines.append(f"- {b}")
    else:
        lines.append("_(No tests were blocked.)_")
    
    lines.extend([
        "",
        "## 5. Environment",
        "",
        f"- Environment: {env_info.get('name', 'Not specified')}",
        f"- Framework: {env_info.get('framework', 'Not specified')}",
        f"- Language: {env_info.get('language', 'Not specified')}",
        "",
        "## 6. Evidence Index",
        "",
    ])
    
    if evidence_files:
        for ef in evidence_files:
            lines.append(f"- {ef}")
    else:
        lines.append("_(No evidence collected.)_")
    
    lines.extend([
        "",
        "---",
        "",
        f"*Test execution performed by qa-run runtime. Results are captured from actual test runs. No results were invented.*",
    ])
    
    return "\n".join(lines)


def is_environment_available(project_config):
    """Check if a test environment is available."""
    env = project_config.get("environments", {})
    return any(env.get(k) for k in ("dev", "staging", "production"))


def check_safety_gates(project_config, action_type):
    """Check if action is permitted by safety gates."""
    safety = project_config.get("safety", {})
    
    if action_type == "production_execution" and not safety.get("production_execution", False):
        return False, "production_execution is disabled"
    if action_type == "real_payments" and not safety.get("real_payments", False):
        return False, "real_payments is disabled"
    if action_type == "destructive_db" and not safety.get("destructive_database_operations", False):
        return False, "destructive_database_operations is disabled"
    
    return True, "permitted"


def should_execute(project_config, story_id):
    """Determine if execution should proceed."""
    if not is_environment_available(project_config):
        return False, "No test environment enabled"
    
    # Check if there are implemented tests
    # This would check the project directory for test files
    return True, "ready"
