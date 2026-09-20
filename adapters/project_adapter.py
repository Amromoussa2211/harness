# QA Agent Harness — Target Project Integration
# Copyright (c) 2026 Hermes QA Agent Harness
# MIT License — see LICENSE file for details.

"""
Project Adapter — discovers and interacts with a target project repository.

The Harness is an independent control plane. It does NOT live inside the
target project. The adapter bridges the gap: it discovers the target repo's
structure, detects its capabilities, and provides a safe command execution
contract for specialists that need to run tests in the target environment.

Separation of concerns:
  - Harness repository: orchestration, analysis, skills, reporting
  - Target project repository: application code, existing tests, configuration
  - Project Adapter: discovery + safe interaction bridge between the two
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Constants ────────────────────────────────────────────────────────────────

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SIX_STATUSES = {"pending", "in_progress", "completed", "blocked", "failed", "skipped"}


# ── Project Adapter ──────────────────────────────────────────────────────────

class ProjectAdapter:
    """Discovers and interacts with a target project repository.

    The adapter is initialized from a project.yaml that MAY include a
    `target_repository` section. When present, the adapter inspects the
    target repository to build a capability map and discovery report.

    The adapter NEVER:
      - copies secrets into shared-state
      - prints credentials or secret values
      - installs dependencies automatically
      - runs destructive commands automatically
      - modifies the target project's source code
    """

    def __init__(self, project_config: dict, project_name: str, project_dir: str):
        """
        Args:
            project_config: the full project.yaml dict
            project_name: the project name (e.g. 'demo')
            project_dir: path to the project directory containing project.yaml
        """
        self.project_config = project_config
        self.project_name = project_name
        self.project_dir = Path(project_dir).resolve()
        self.adapter_path = self.project_dir / "project.yaml"
        self._target_path: Path | None = None
        self._capability_map: dict[str, Any] = {}
        self._discovery_cache: dict[str, Any] = {}

    # ── Target Repository Resolution ────────────────────────────────────────

    def get_target_repository_path(self) -> Path | None:
        """Resolve the target repository path from project config.

        Returns:
            Path to the target repository, or None if not configured.
        """
        if self._target_path is not None:
            return self._target_path

        target = self.project_config.get("target_repository", {})
        path_val = target.get("path", "")

        if not path_val:
            return None

        # Support both absolute and relative paths.
        # Relative paths are resolved relative to the Harness root (where qa-run lives).
        path = Path(path_val)
        if not path.is_absolute():
            harness_root = Path(__file__).resolve().parent.parent  # adapters/ -> harness root
            path = (harness_root / path_val).resolve()

        if not path.is_dir():
            return None

        self._target_path = path
        return self._target_path

    # ── Capability Detection ─────────────────────────────────────────────────

    def detect_capabilities(self) -> dict[str, Any]:
        """Build a machine-readable capability map for the target project.

        The capability map drives dynamic skill selection. It reflects what
        the target project actually has, not what the Harness assumes.

        Returns:
            A dict with boolean flags for each capability.
        """
        if self._capability_map:
            return self._capability_map

        target = self.get_target_repository_path()
        base = {
            "web": False,
            "api": False,
            "mobile": False,
            "playwright": False,
            "cypress": False,
            "selenium": False,
            "appium": False,
            "pytest": False,
            "java_test": False,
            "graphql": False,
            "webhooks": False,
            "event_driven": False,
            "database": False,
            "docker": False,
            "ci": False,
            "existing_automation": False,
            "test_directory": None,
            "package_manager": None,
            "language": None,
            "framework_version": None,
        }

        if target is None:
            self._capability_map = base
            return base

        self._capability_map = self._inspect_target(target, base)
        return self._capability_map

    def _inspect_target(self, target: Path, base: dict) -> dict:
        """Inspect a target repository and update the capability map."""
        repo = target

        # ── Language and package manager ──
        pkg_json = repo / "package.json"
        requirements_txt = repo / "requirements.txt"
        pyproject_toml = repo / "pyproject.toml"
        pom_xml = repo / "pom.xml"
        build_gradle = repo / "build.gradle"

        if pkg_json.exists():
            base["language"] = self._detect_node_language(pkg_json)
            base["package_manager"] = "npm" if (repo / "package-lock.json").exists() else "yarn" if (repo / "yarn.lock").exists() else "npm"
        elif requirements_txt.exists() or pyproject_toml.exists():
            base["language"] = "python"
            base["package_manager"] = "pip"
        elif pom_xml.exists():
            base["language"] = "java"
            base["package_manager"] = "maven"
        elif build_gradle.exists():
            base["language"] = "java"
            base["package_manager"] = "gradle"

        # ── Web / API detection ──
        if base["language"] in ("javascript", "typescript", "node"):
            base["web"] = True
        if (repo / "openapi.yaml").exists() or (repo / "openapi.json").exists() or (repo / "swagger.yaml").exists() or (repo / "swagger.json").exists():
            base["api"] = True
            base["graphql"] = False

        # Check for GraphQL
        gql_indicators = ["graphql", ".gql", "graphql-tag", "@graphql"]
        for f in repo.rglob("*"):
            if f.is_file():
                try:
                    content = f.read_text()
                    if any(g.lower() in content.lower() for g in gql_indicators):
                        base["graphql"] = True
                        base["api"] = True
                        break
                except (OSError, UnicodeDecodeError):
                    pass

        # ── Test framework detection ──
        base = self._detect_test_frameworks(repo, base)

        # ── Docker ──
        if (repo / "Dockerfile").exists() or list(repo.glob("docker-compose*")):
            base["docker"] = True

        # ── CI ──
        ci_indicators = [".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile", "circle.yml"]
        for ci_path in ci_indicators:
            if (repo / ci_path).exists():
                base["ci"] = True
                break

        # ── Webhooks ──
        webhook_indicators = ["webhook", "webhooks", "callback", "callbacks"]
        for f in repo.rglob("*"):
            if f.is_file() and f.suffix in {".js", ".ts", ".py", ".java", ".json", ".yaml", ".yml", ".md"}:
                try:
                    content = f.read_text().lower()
                    if any(w in content for w in webhook_indicators):
                        base["webhooks"] = True
                        break
                except (OSError, UnicodeDecodeError):
                    pass

        # ── Test directory ──
        test_dirs = [
            "tests", "test", "e2e", "spec", "cypress/e2e", "cypress/integration",
            "src/test", "src/e2e", "playwright/tests", "playwright/test"
        ]
        for td in test_dirs:
            if (repo / td).is_dir():
                base["test_directory"] = str(repo / td)
                break
        if not base["test_directory"]:
            for d in repo.iterdir():
                if d.is_dir() and d.name.lower() in ("tests", "test", "e2e", "spec"):
                    base["test_directory"] = str(d)
                    break

        # ── Application type from project.yaml ──
        app = self.project_config.get("application", {})
        if app.get("web"):
            base["web"] = True
        if app.get("api"):
            base["api"] = True
        if app.get("mobile"):
            base["mobile"] = True

        # ── Automation framework from project.yaml ──
        autom = self.project_config.get("automation", {})
        fw = autom.get("framework", "")
        if fw == "playwright":
            base["playwright"] = True
        elif fw == "cypress":
            base["cypress"] = True
        elif fw == "selenium":
            base["selenium"] = True
        elif fw == "appium":
            base["appium"] = True

        return base

    def _detect_node_language(self, pkg_json: Path) -> str:
        """Detect TypeScript vs JavaScript from package.json."""
        try:
            with open(pkg_json) as f:
                data = json.load(f)
            scripts = data.get("scripts", {})
            if "build" in scripts and ("tsc" in scripts.get("build", "") or "typescript" in str(data)):
                return "typescript"
            dev_deps = data.get("devDependencies", {})
            if "typescript" in dev_deps:
                return "typescript"
            return "javascript"
        except (OSError, json.JSONDecodeError):
            return "javascript"

    def _detect_test_frameworks(self, repo: Path, base: dict) -> dict:
        """Detect existing test frameworks in the target repository."""
        # Playwright
        playwright_configs = list(repo.glob("playwright.config.*"))
        if playwright_configs:
            base["playwright"] = True
            base["existing_automation"] = True
            # Get version
            pkg_json = repo / "package.json"
            if pkg_json.exists():
                try:
                    with open(pkg_json) as f:
                        data = json.load(f)
                    deps = {**data.get("devDependencies", {}), **data.get("dependencies", {})}
                    if "@playwright/test" in deps:
                        base["framework_version"] = deps["@playwright/test"]
                except (OSError, json.JSONDecodeError):
                    pass

        # Cypress
        cypress_config = repo / "cypress.config.js"
        if not cypress_config.exists():
            cypress_config = repo / "cypress.config.ts"
        if cypress_config.exists() or (repo / "cypress").is_dir():
            base["cypress"] = True
            base["existing_automation"] = True

        # Selenium
        selenium_indicators = ["selenium-webdriver", "selenium.java", "WebDriver"]
        for f in repo.rglob("*"):
            if f.is_file() and f.suffix in {".js", ".ts", ".py", ".java"}:
                try:
                    content = f.read_text()
                    if any(s.lower() in content.lower() for s in selenium_indicators):
                        base["selenium"] = True
                        base["existing_automation"] = True
                        break
                except (OSError, UnicodeDecodeError):
                    pass

        # Appium
        appium_indicators = ["appium", "Appium", "wd.io", "webdriverio"]
        for f in repo.rglob("*"):
            if f.is_file() and f.suffix in {".js", ".ts", ".py"}:
                try:
                    content = f.read_text()
                    if any(a.lower() in content.lower() for a in appium_indicators):
                        base["appium"] = True
                        base["existing_automation"] = True
                        base["mobile"] = True
                        break
                except (OSError, UnicodeDecodeError):
                    pass

        # pytest
        if (repo / "pytest.ini").exists() or (repo / "tox.ini").exists() or (repo / "pyproject.toml").exists():
            try:
                if repo / "pyproject.toml":
                    with open(repo / "pyproject.toml") as f:
                        content = f.read()
                    if "pytest" in content or "pytest-" in content:
                        base["pytest"] = True
                        base["existing_automation"] = True
            except OSError:
                pass
        if (repo / "setup.cfg").exists():
            try:
                with open(repo / "setup.cfg") as f:
                    if "[tool:pytest]" in f.read():
                        base["pytest"] = True
                        base["existing_automation"] = True
            except OSError:
                pass

        # Java test frameworks
        java_test_indicators = ["junit", "JUnit", "testng", "TestNG", "@Test", "@Test("]
        for f in repo.rglob("*"):
            if f.is_file() and f.suffix in {".java", ".kt"}:
                try:
                    content = f.read_text()
                    if any(j.lower() in content.lower() for j in java_test_indicators):
                        base["java_test"] = True
                        base["existing_automation"] = True
                        break
                except (OSError, UnicodeDecodeError):
                    pass

        return base

    # ── Environment Discovery ────────────────────────────────────────────────

    def discover_environments(self) -> list[dict]:
        """Discover environment configuration from the target repository.

        Returns a list of environment dicts with source attribution.
        Never exposes secret values.
        """
        environments = []
        target = self.get_target_repository_path()
        if target is None:
            return environments

        # Read playwright.config.* for base URL
        for cfg in target.glob("playwright.config.*"):
            env = self._parse_playwright_config(cfg)
            if env:
                environments.append(env)

        # Check for .env.example
        env_example = target / ".env.example"
        if env_example.exists():
            env_vars = self._parse_env_example(env_example)
            if env_vars:
                environments.append({
                    "type": "examples",
                    "source": str(env_example),
                    "variables": env_vars,
                })

        # Check package.json for scripts
        pkg_json = target / "package.json"
        if pkg_json.exists():
            scripts = self._parse_package_scripts(pkg_json)
            if scripts:
                environments.append({
                    "type": "scripts",
                    "source": str(pkg_json),
                    "scripts": scripts,
                })

        # Check for README with environment info
        readme = target / "README.md"
        if readme.exists():
            env_from_readme = self._parse_readme_env(readme)
            if env_from_readme:
                environments.append({
                    "type": "readme",
                    "source": str(readme),
                    "information": env_from_readme,
                })

        return environments

    def _parse_playwright_config(self, cfg: Path) -> dict | None:
        """Extract base URL and environment info from playwright.config.*"""
        try:
            content = cfg.read_text()
        except OSError:
            return None

        result = {
            "source": str(cfg),
            "base_url": None,
            "api_url": None,
            "port": None,
            "test_dir": None,
        }

        # Base URL — match various JS/TS patterns
        # Pattern 1: baseURL: "http://..."
        base_url_match = re.search(r'baseURL\s*:\s*["\']([^"\']+)["\']', content)
        if base_url_match:
            result["base_url"] = base_url_match.group(1)
        else:
            # Pattern 2: baseURL: process.env.BASE_URL || "http://..."
            base_url_or = re.search(r'baseURL\s*:\s*process\.env\.BASE_URL\s*\|\|\s*["\']([^"\']+)["\']', content)
            if base_url_or:
                result["base_url"] = base_url_or.group(1)
            else:
                # Pattern 3: baseURL: process.env.BASE_URL
                base_url_env = re.search(r'baseURL\s*:\s*process\.env\.BASE_URL', content)
                if base_url_env:
                    result["base_url"] = "PROCESS_ENV_BAS_URL"

        # API URL
        api_url_match = re.search(r'apiURL\s*[=:]\s*["\']([^"\']+)["\']', content)
        if api_url_match:
            result["api_url"] = api_url_match.group(1)

        # Port
        port_match = re.search(r'port\s*[=:]\s*(\d+)', content)
        if port_match:
            result["port"] = int(port_match.group(1))

        # Test directory
        projects_match = re.search(r'projects\s*\(\s*\[?\s*["\']([^"\']+)["\']', content)
        if projects_match:
            result["test_dir"] = projects_match.group(1)
        cases_match = re.search(r'fullyParallel.*?testDir\s*[=:]\s*["\']([^"\']+)["\']', content, re.DOTALL)
        if cases_match:
            result["test_dir"] = cases_match.group(1)

        # Only return if we found something useful
        if any(v is not None and v != "PROCESS_ENV_BAS_URL" for v in result.values()):
            return result
        # Return even if base_url is PROCESS_ENV_BAS_URL
        if result["base_url"] == "PROCESS_ENV_BAS_URL":
            return result
        return None

    def _parse_env_example(self, env_file: Path) -> list[dict]:
        """Parse .env.example and return variable names without values."""
        vars_found = []
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        name = line.split("=", 1)[0].strip()
                        if name:
                            vars_found.append({
                                "name": name,
                                "source": str(env_file),
                                "value": "NOT EXPOSED",
                            })
        except OSError:
            pass
        return vars_found

    def _parse_package_scripts(self, pkg_json: Path) -> dict:
        """Extract test-related scripts from package.json."""
        try:
            with open(pkg_json) as f:
                data = json.load(f)
            scripts = data.get("scripts", {})
            test_scripts = {}
            for name, cmd in scripts.items():
                if any(w in name.lower() for w in ["test", "e2e", "playwright", "cypress", "lint", "build"]):
                    test_scripts[name] = cmd
            return test_scripts
        except (OSError, json.JSONDecodeError):
            return {}

    def _parse_readme_env(self, readme: Path) -> list[str]:
        """Extract environment-related information from README."""
        info = []
        try:
            with open(readme) as f:
                for line in f:
                    line = line.strip()
                    if any(w in line.lower() for w in ["base url", "api url", "port", "environment", "docker", "npm run", "yarn run", "prerequisite"]):
                        info.append(line)
        except OSError:
            pass
        return info[:10]  # Limit to 10 lines

    # ── Test Data Discovery ───────────────────────────────────────────────────

    def discover_test_data(self) -> list[dict]:
        """Discover test data locations in the target repository."""
        target = self.get_target_repository_path()
        if target is None:
            return []

        locations = []
        test_data_dirs = ["test-data", "test_data", "fixtures", "test/fixtures", "tests/fixtures"]
        for td in test_data_dirs:
            path = target / td
            if path.is_dir():
                locations.append({
                    "path": str(path),
                    "type": td.replace("-", "_"),
                    "source": "target repository directory",
                })

        # Check for seed scripts
        seed_indicators = ["seed", "seed-data", "seed-data"]
        for f in target.rglob("*"):
            if f.is_file() and f.suffix in {".js", ".ts", ".py", ".sh"}:
                try:
                    content = f.read_text().lower()
                    if any(s in f.name.lower() for s in seed_indicators) or any(s in content for s in ["seed", "factory", "fixture"]):
                        locations.append({
                            "path": str(f),
                            "type": "seed/factory script",
                            "source": "target repository file",
                        })
                except (OSError, UnicodeDecodeError):
                    pass

        return locations

    # ── Safe Command Execution ────────────────────────────────────────────────

    def classify_command(self, command: str) -> str:
        """Classify a command as SAFE, REQUIRES APPROVAL, DESTRUCTIVE, or UNKNOWN.

        This is a heuristic classification. It does not execute the command.
        """
        cmd_lower = command.lower()

        # Destructive indicators
        destructive = [
            "rm -rf", "rm -r", "rm ", "dd ", "mkfs", "format",
            "drop table", "drop database", "truncate", "delete from",
            "kill -9", "killall", "pkill",
            "docker rm", "docker rmi", "docker volume rm",
            "git reset --hard", "git clean -fdx",
            "chmod -R 777", "chown -R",
        ]
        for d in destructive:
            if d in cmd_lower:
                return "DESTRUCTIVE"

        # Approval-required indicators
        approval = [
            "npm publish", "yarn publish", "npm deploy", "yarn deploy",
            "git push", "git pull", "git merge", "git rebase",
            "ssh", "scp", "rsync",
            "curl -X POST", "curl -X PUT", "curl -X DELETE",
            "kubectl apply", "kubectl delete", "helm upgrade", "helm install",
            "terraform apply", "terraform destroy",
            "production", "prod", "live",
        ]
        for a in approval:
            if a in cmd_lower:
                return "REQUIRES APPROVAL"

        # Safe indicators
        safe = [
            "npm test", "yarn test", "npm run test", "yarn run test",
            "npx playwright", "npx cypress",
            "pytest", "python -m pytest",
            "npm run lint", "yarn lint",
            "npm run build", "yarn build",
            "echo", "cat", "ls", "pwd", "whoami",
            "npm install", "yarn install",
        ]
        for s in safe:
            if s in cmd_lower:
                return "SAFE"

        return "UNKNOWN"

    def execute_command(
        self,
        command: str,
        working_directory: Path | None = None,
        timeout: int = 300,
        env: dict | None = None,
    ) -> dict:
        """Execute a command in the target repository with safety checks.

        Args:
            command: the shell command to execute
            working_directory: directory to run the command in (defaults to target repo)
            timeout: max seconds to wait
            env: optional environment variables (does NOT expose secrets)

        Returns:
            A normalized execution result dict.
        """
        classification = self.classify_command(command)
        if classification == "DESTRUCTIVE":
            return {
                "status": "blocked",
                "command": command,
                "classification": classification,
                "reason": "Command classified as DESTRUCTIVE and will not be executed automatically.",
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "duration": 0,
                "artifacts": [],
            }
        if classification == "REQUIRES APPROVAL":
            return {
                "status": "blocked",
                "command": command,
                "classification": classification,
                "reason": "Command classified as REQUIRES APPROVAL. Human authorization required before execution.",
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "duration": 0,
                "artifacts": [],
            }

        target = self.get_target_repository_path()
        cwd = working_directory or target or Path.cwd()

        start = time.time()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, **(env or {})},
            )
            duration = time.time() - start
            return {
                "status": "completed" if proc.returncode == 0 else "failed",
                "command": command,
                "classification": classification,
                "working_directory": str(cwd),
                "exit_code": proc.returncode,
                "duration": round(duration, 2),
                "stdout": proc.stdout[:50000] if proc.stdout else "",
                "stderr": proc.stderr[:50000] if proc.stderr else "",
                "artifacts": [],
                "errors": [],
            }
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            return {
                "status": "timeout",
                "command": command,
                "classification": classification,
                "working_directory": str(cwd),
                "exit_code": -1,
                "duration": round(duration, 2),
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds.",
                "artifacts": [],
                "errors": ["timeout"],
            }
        except OSError as e:
            duration = time.time() - start
            return {
                "status": "error",
                "command": command,
                "classification": classification,
                "working_directory": str(cwd),
                "exit_code": -1,
                "duration": round(duration, 2),
                "stdout": "",
                "stderr": str(e),
                "artifacts": [],
                "errors": [str(e)],
            }

    # ── Discovery Report ──────────────────────────────────────────────────────

    def generate_discovery_report(self) -> dict:
        """Generate a comprehensive discovery report for the target project.

        Returns a dict suitable for serialization to the discovery output.
        """
        capabilities = self.detect_capabilities()
        environments = self.discover_environments()
        test_data = self.discover_test_data()

        # Existing tests
        existing_tests = []
        test_dir = capabilities.get("test_directory")
        if test_dir:
            test_path = Path(test_dir)
            if test_path.is_dir():
                for f in test_path.rglob("*"):
                    if f.is_file() and f.suffix in {".js", ".ts", ".py", ".java", ".feature"}:
                        existing_tests.append({
                            "path": str(f.relative_to(target := self.get_target_repository_path() or Path.cwd())),
                            "type": f.suffix.lstrip("."),
                        })

        return {
            "target_repository": {
                "path": str(self.get_target_repository_path()) if self.get_target_repository_path() else None,
                "resolved": self.get_target_repository_path() is not None,
            },
            "capabilities": capabilities,
            "environments": environments,
            "test_data": test_data,
            "existing_tests": existing_tests,
            "summary": self._generate_summary(capabilities, environments, test_data, existing_tests),
        }

    def _generate_summary(self, caps: dict, envs: list, test_data: list, tests: list) -> dict:
        """Generate a human-readable summary of the discovery."""
        parts = []

        target = self.get_target_repository_path()
        if target:
            parts.append(f"Target repository: {target}")
        else:
            parts.append("No target repository configured.")

        lang = caps.get("language", "unknown")
        pm = caps.get("package_manager", "unknown")
        parts.append(f"Language: {lang}, Package manager: {pm}")

        fw = []
        if caps.get("playwright"):
            fw.append(f"Playwright (version: {caps.get('framework_version') or 'unknown'})")
        if caps.get("cypress"):
            fw.append("Cypress")
        if caps.get("selenium"):
            fw.append("Selenium")
        if caps.get("appium"):
            fw.append("Appium")
        if caps.get("pytest"):
            fw.append("pytest")
        if caps.get("java_test"):
            fw.append("JUnit/TestNG")
        if not fw:
            fw.append("No existing test framework detected")
        parts.append(f"Test framework(s): {'; '.join(fw)}")

        if caps.get("existing_automation"):
            parts.append("Existing automation: YES")
        else:
            parts.append("Existing automation: NO")

        if caps.get("test_directory"):
            parts.append(f"Test directory: {caps['test_directory']}")

        env_parts = []
        for e in envs:
            if e.get("type") == "examples":
                env_parts.append(f"Environment variables from {e['source']}: {len(e.get('variables', []))} variables defined (values not exposed)")
            elif e.get("type") == "scripts":
                env_parts.append(f"Package scripts from {e['source']}: {len(e.get('scripts', {}))} scripts")
            elif e.get("type") == "readme":
                env_parts.append(f"README environment info from {e['source']}")
            elif e.get("base_url"):
                env_parts.append(f"Base URL (from {e['source']}): {e['base_url']}")
        if env_parts:
            parts.append("Environment: " + " | ".join(env_parts))
        else:
            parts.append("Environment: Not configured")

        if test_data:
            parts.append(f"Test data locations: {len(test_data)} found")
        else:
            parts.append("Test data: Not found")

        if tests:
            parts.append(f"Existing tests: {len(tests)} found")
        else:
            parts.append("Existing tests: None detected")

        return {"summary": " | ".join(parts)}


# ── Factory ───────────────────────────────────────────────────────────────────

def create_adapter(project_config: dict, project_name: str, project_dir: str) -> ProjectAdapter:
    """Create a ProjectAdapter for the given project configuration."""
    return ProjectAdapter(project_config, project_name, project_dir)
