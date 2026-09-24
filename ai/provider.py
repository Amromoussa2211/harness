#!/usr/bin/env python3
"""
AI Provider Abstraction — provider-agnostic LLM interface for the QA Agent Harness.

Supported providers:
  - openai (OpenAI API, GPT-4/o1/etc.)
  - local   (any OpenAI-compatible local server, e.g. LM Studio, Ollama)

Add new providers by implementing the LLMProvider interface.

No provider is required at install time. AI mode fails safely when
no provider is configured.
"""

from __future__ import annotations

import json
import os
import sys
import time
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable

# ── Token/Cost tracking ──────────────────────────────────────────────────────

@dataclass
class TokenUsage:
    """Track token usage for a single LLM call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class ProviderStats:
    """Aggregate token usage and call metrics for a provider session."""
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_estimated_cost_usd: float = 0.0
    calls: list[dict] = field(default_factory=list)

    def record_call(self, model: str, usage: TokenUsage, duration_ms: float, success: bool) -> None:
        self.total_calls += 1
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        self.total_estimated_cost_usd += usage.estimated_cost_usd
        self.calls.append({
            "model": model,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "estimated_cost_usd": usage.estimated_cost_usd,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": time.time(),
        })


# ── Provider interface ───────────────────────────────────────────────────────

class LLMProvider:
    """
    Abstract interface for LLM providers.

    Implementations must provide:
      - name: provider identifier
      - model: model identifier
      - chat_completion(messages, **kwargs) -> dict
      - embed(text) -> list[float]  (optional, None if not supported)
    """

    name: str = "base"
    model: str = "unknown"

    def chat_completion(self, messages: list[dict], **kwargs: Any) -> dict:
        """Send a chat completion request and return the parsed response."""
        raise NotImplementedError

    def embed(self, text: str) -> list[float] | None:
        """Return an embedding vector for the given text, or None if unsupported."""
        return None

    def compute_sha256(self, content: str) -> str:
        """Compute a content hash for cache/dedup support."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


# ── OpenAI Provider ──────────────────────────────────────────────────────────

try:
    import openai as _openai
    from openai import RateLimitError, APIError, APITimeoutError

    class OpenAIProvider(LLMProvider):
        """OpenAI API provider (GPT-4, GPT-3.5, o1, etc.)."""

        name: str = "openai"
        model: str = "gpt-4o-mini"

        def __init__(self, api_key: str | None = None, model: str | None = None,
                     temperature: float = 0.3, timeout_s: float = 60.0) -> None:
            self.api_key = api_key or os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI provider requires an API key (AI_API_KEY or OPENAI_API_KEY env var)")
            self.model = model or os.environ.get("AI_MODEL", "gpt-4o-mini")
            self.temperature = float(os.environ.get("AI_TEMPERATURE", temperature))
            self.timeout_s = float(os.environ.get("AI_TIMEOUT_S", timeout_s))
            self._client = _openai.OpenAI(api_key=self.api_key, timeout=self.timeout_s)

        def chat_completion(self, messages: list[dict], **kwargs: Any) -> dict:
            """Call the OpenAI Chat Completions API."""
            start = time.time()
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    response_format={"type": "json_object"},
                    **kwargs,
                )
                duration_ms = (time.time() - start) * 1000
                choice = response.choices[0]
                content = choice.message.content or "{}"
                usage = getattr(response, "usage", None)

                token_usage = TokenUsage()
                if usage:
                    token_usage.prompt_tokens = usage.prompt_tokens or 0
                    token_usage.completion_tokens = usage.completion_tokens or 0
                    token_usage.total_tokens = usage.total_tokens or 0
                    # Very rough cost estimate: ~$0.15/1M input, ~$0.60/1M output for gpt-4o-mini
                    token_usage.estimated_cost_usd = (
                        (token_usage.prompt_tokens * 0.00000015) +
                        (token_usage.completion_tokens * 0.00000060)
                    )

                return {
                    "content": content,
                    "role": choice.message.role,
                    "finish_reason": choice.finish_reason,
                    "duration_ms": duration_ms,
                    "token_usage": token_usage,
                    "raw_model": self.model,
                    "raw_provider": self.name,
                }
            except (_openai.APIError, RateLimitError, APITimeoutError) as e:
                duration_ms = (time.time() - start) * 1000
                return {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": duration_ms,
                    "token_usage": TokenUsage(),
                }

        def embed(self, text: str) -> list[float] | None:
            """Return text embedding via OpenAI Embeddings API (optional)."""
            try:
                response = self._client.embeddings.create(model="text-embedding-3-small", input=text)
                return response.data[0].embedding
            except Exception:
                return None

except ImportError:

    class OpenAIProvider(LLMProvider):
        """Stub — raised when openai is not installed."""
        name: str = "openai"

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("openai package is not installed. Run: pip install openai")

        def chat_completion(self, *args: Any, **kwargs: Any) -> dict:
            raise RuntimeError("openai package is not installed.")


# ── Local / OpenAI-compatible Provider ──────────────────────────────────────

class LocalProvider(LLMProvider):
    """
    Provider for any OpenAI-compatible local server (LM Studio, Ollama, vLLM, etc.).

    Configuration via environment variables:
      LOCAL_LLM_BASE_URL  — e.g. http://localhost:1234/v1
      LOCAL_LLM_MODEL     — model name
      LOCAL_LLM_API_KEY   — optional API key
    """

    name: str = "local"

    def __init__(self, base_url: str | None = None, model: str | None = None,
                 api_key: str | None = None, temperature: float = 0.3) -> None:
        self.base_url = base_url or os.environ.get("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
        self.model = model or os.environ.get("LOCAL_LLM_MODEL", "local-model")
        self.api_key = api_key or os.environ.get("LOCAL_LLM_API_KEY", "")
        self.temperature = float(os.environ.get("AI_TEMPERATURE", temperature))

        if not self.base_url.startswith("http"):
            raise ValueError(f"Invalid LOCAL_LLM_BASE_URL: {self.base_url}")

        # Build HTTP opener with optional auth
        self._opener = urllib.request.build_opener(urllib.request.HTTPHandler)
        if self.api_key:
            self._opener.addheaders = [("Authorization", f"Bearer {self.api_key}")]

    def chat_completion(self, messages: list[dict], **kwargs: Any) -> dict:
        """Call a local OpenAI-compatible server via urllib."""
        import urllib.request
        import urllib.error

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
            **kwargs,
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        data = json.dumps(payload).encode("utf-8")
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
        })
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")

        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                parsed = json.loads(raw)
                choice = parsed.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "{}")
                usage = parsed.get("usage", {})

                token_usage = TokenUsage()
                if usage:
                    token_usage.prompt_tokens = usage.get("prompt_tokens", 0)
                    token_usage.completion_tokens = usage.get("completion_tokens", 0)
                    token_usage.total_tokens = usage.get("total_tokens", 0)

                duration_ms = (time.time() - start) * 1000
                return {
                    "content": content,
                    "role": choice.get("message", {}).get("role", "assistant"),
                    "finish_reason": choice.get("finish_reason", "unknown"),
                    "duration_ms": duration_ms,
                    "token_usage": token_usage,
                    "raw_model": self.model,
                    "raw_provider": self.name,
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            duration_ms = (time.time() - start) * 1000
            return {
                "error": f"HTTP {e.code}: {body[:500]}",
                "error_type": "HTTPError",
                "duration_ms": duration_ms,
                "token_usage": TokenUsage(),
            }
        except urllib.error.URLError as e:
            duration_ms = (time.time() - start) * 1000
            return {
                "error": f"Connection error: {e.reason}",
                "error_type": "URLError",
                "duration_ms": duration_ms,
                "token_usage": TokenUsage(),
            }
        except json.JSONDecodeError as e:
            duration_ms = (time.time() - start) * 1000
            return {
                "error": f"Invalid JSON response: {e}",
                "error_type": "JSONDecodeError",
                "duration_ms": duration_ms,
                "token_usage": TokenUsage(),
            }

    def embed(self, text: str) -> list[float] | None:
        return None


# ── Null Provider (fails safely) ─────────────────────────────────────────────

class NoOpProvider(LLMProvider):
    """Provider that returns structured canned responses for demonstration.

    When AI mode is requested but no real LLM is configured, this provider
    returns valid JSON structured outputs for each agent role so the harness
    can demonstrate the full AI pipeline without a live LLM connection.
    """

    name: str = "noop"
    model: str = "noop-demo"

    def __init__(self) -> None:
        self.name = "noop"
        self.model = "noop-demo"
        self.temperature = 0.0

    def _get_canned_response(self, prompt_preview: str) -> dict:
        """Generate a canned response based on the prompt content."""
        prompt_lower = prompt_preview.lower()

        # Detect which agent is being called from the prompt
        if "qa analyst" in prompt_lower or "understand a software story" in prompt_lower or "analyst" in prompt_lower:
            return {
                "summary": "Story describes a web application with user authentication and dashboard access.",
                "actors": ["Authenticated User", "Anonymous Visitor"],
                "inputs": ["username", "password", "login credentials"],
                "outputs": ["login success/failure message", "dashboard access or redirect to login"],
                "acceptance_criteria": [
                    {"id": "AC1", "text": "User can log in with valid credentials", "type": "functional"},
                    {"id": "AC2", "text": "Invalid credentials show error message", "type": "negative"},
                    {"id": "AC3", "text": "Unauthenticated users are redirected to login", "type": "functional"},
                ],
                "ambiguities": [
                    {"issue": "What constitutes 'valid' credentials?", "impact": "Test data setup", "confidence": "medium"},
                    {"issue": "Is there a 'Remember me' feature?", "impact": "Cookie/session testing", "confidence": "low"},
                ],
                "missing_requirements": [
                    {"requirement": "Error message format for failed login", "why_needed": "Test assertion needs exact text"},
                    {"requirement": "Session timeout behavior", "why_needed": "Security test coverage"},
                ],
                "dependencies": [
                    {"dependency": "User database or auth service", "type": "external_system"},
                    {"dependency": "Login page URL", "type": "external_system"},
                ],
                "assumptions": [
                    {"assumption": "Login page is accessible at a known URL", "justification": "Standard web app pattern", "risk": "low"},
                    {"assumption": "Credentials are passed via form fields", "justification": "Standard login pattern", "risk": "low"},
                ],
                "unknowns": [
                    {"unknown": "Exact URL of login page", "impact": "Test navigation setup"},
                    {"unknown": "Expected success/error message text", "impact": "Test assertions"},
                ],
                "questions": [
                    {"question": "What are the exact login credentials for testing?", "priority": "high"},
                    {"question": "What error message is shown for failed login?", "priority": "high"},
                    {"question": "Is there a maximum login attempt limit?", "priority": "medium"},
                ],
                "confidence": "medium",
            }

        if "Grill Master" in prompt_preview or "challenge a software story" in prompt_preview:
            return {
                "questions": [
                    {"id": "Q1", "question": "What happens when the login form is submitted with empty fields?", "motivation": "Story doesn't specify empty input behavior", "risk_if_unanswered": "Test may miss validation gap"},
                    {"id": "Q2", "question": "How are passwords transmitted and stored?", "motivation": "Security consideration for login flow", "risk_if_unanswered": "Security testing scope unclear"},
                    {"id": "Q3", "question": "What happens after multiple failed login attempts?", "motivation": "No rate limiting mentioned in story", "risk_if_unanswered": "Brute force vulnerability untested"},
                    {"id": "Q4", "question": "Is the login page accessible via HTTPS only?", "motivation": "Security requirement not specified", "risk_if_unanswered": "Credential exposure risk"},
                    {"id": "Q5", "question": "What happens if the auth service is unavailable during login?", "motivation": "External dependency failure scenario", "risk_if_unanswered": "No graceful degradation tested"},
                ],
                "ambiguities_found": [
                    "Credentials format not specified (username only? email? both?)",
                    "Password requirements not defined",
                    "Session duration after login not specified",
                ],
                "missing_requirements": [
                    "Error messages for invalid input formats",
                    "Account lockout policy after failed attempts",
                    "Password complexity requirements",
                ],
                "risk_flags": [
                    "No mention of HTTPS requirement for login — credential exposure risk",
                    "No account lockout mentioned — brute force vulnerability",
                    "No session timeout specified — session hijacking risk",
                ],
                "clarification_needed": [
                    "What is the expected login URL?",
                    "What are the valid test credentials?",
                    "What should happen on successful login? Redirect to dashboard?",
                ],
            }

        if "QA Risk Analyst" in prompt_preview or "identify and assess risks" in prompt_preview:
            return {
                "risks": [
                    {
                        "risk_id": "RR-001",
                        "category": "SECURITY_RISK",
                        "description": "Credentials transmitted without encryption if HTTPS not enforced",
                        "reason": "Story does not specify HTTPS requirement for login page",
                        "impact": "User credentials could be intercepted on untrusted networks",
                        "likelihood": "medium",
                        "priority": "high",
                        "affected_area": "Authentication Flow",
                        "mitigation": "Enforce HTTPS on login page; test for HTTP access",
                        "evidence": "No HTTPS requirement in story; standard security practice requires it",
                    },
                    {
                        "risk_id": "RR-002",
                        "category": "SECURITY_RISK",
                        "description": "No account lockout mechanism after repeated failed attempts",
                        "reason": "Story is silent on brute-force protection",
                        "impact": "Attacker could enumerate valid usernames or guess passwords",
                        "likelihood": "medium",
                        "priority": "high",
                        "affected_area": "Authentication Flow",
                        "mitigation": "Implement rate limiting; test locked account behavior",
                        "evidence": "No mention of login attempt limits in requirements",
                    },
                    {
                        "risk_id": "RR-003",
                        "category": "TECHNICAL_RISK",
                        "description": "Test environment may not have the same auth configuration as production",
                        "reason": "External auth service dependency not fully specified",
                        "impact": "Tests may pass in dev but fail in staging/production",
                        "likelihood": "medium",
                        "priority": "medium",
                        "affected_area": "Test Environment",
                        "mitigation": "Use test-specific credentials; validate auth flow in target env",
                        "evidence": "Auth service dependency identified but configuration unknown",
                    },
                    {
                        "risk_id": "RR-004",
                        "category": "REGRESSION_RISK",
                        "description": "Login changes could break existing user sessions",
                        "reason": "Authentication is a critical path affecting all authenticated features",
                        "impact": "Dashboard and other authenticated features become inaccessible",
                        "likelihood": "low",
                        "priority": "medium",
                        "affected_area": "Session Management",
                        "mitigation": "Test existing session behavior after login flow changes",
                        "evidence": "Login is entry point for authenticated workflows",
                    },
                ],
                "summary": "4 risks identified: 2 security (high priority), 1 technical (medium), 1 regression (medium). Primary concerns are credential security and brute-force protection.",
            }

        if "QA Test Architect" in prompt_preview or "design the test architecture" in prompt_preview:
            return {
                "test_strategy": {
                    "ui_e2e": {
                        "recommended": True,
                        "rationale": "Login is a user-facing flow that must be tested via the UI to validate the complete interaction including form rendering, input, submission, and result display.",
                        "scope": "Login form submission with valid and invalid credentials; redirect behavior after login; error message display"
                    },
                    "api": {
                        "recommended": False,
                        "rationale": "The story focuses on user-facing login behavior. API-level testing would bypass the UI and not validate the full user experience. API tests are better suited for service-layer validation when the UI is stable.",
                        "scope": "Not recommended for this story — defer to integration tests if auth service API needs separate validation"
                    },
                    "contract": {
                        "recommended": False,
                        "rationale": "No external API contracts are involved in the login flow as described. Contract testing applies when multiple services exchange data via defined interfaces.",
                        "scope": "Not applicable to this story"
                    },
                    "performance": {
                        "recommended": False,
                        "rationale": "Login is an infrequent operation for most users. Performance testing the login endpoint is low value unless the story explicitly requires sub-second login or high-concurrency login scenarios.",
                        "scope": "Not recommended unless performance requirements are specified"
                    },
                    "security": {
                        "recommended": True,
                        "rationale": "Login is the primary security boundary. Testing for credential handling, HTTPS enforcement, error message leakage, and brute-force resistance is essential.",
                        "scope": "HTTPS enforcement, error message content (no credential enumeration), input validation, session cookie security"
                    },
                    "accessibility": {
                        "recommended": True,
                        "rationale": "Login forms must be accessible to all users including those using screen readers. WCAG compliance for form labels, error announcement, and keyboard navigation should be verified.",
                        "scope": "Form label association, error message accessibility, keyboard navigation, focus management"
                    },
                },
                "rationale_summary": "The login story calls for UI/E2E testing as the primary approach since it's a user-facing flow. Security testing is essential given the sensitivity of authentication. Accessibility testing ensures inclusive access. API and contract testing are not recommended at this level — they apply at lower test pyramid layers for the auth service itself.",
                "recommendations": [
                    {"recommendation": "Prioritize UI E2E tests for login flow (happy path + negative)", "priority": "high", "why": "Validates complete user experience"},
                    {"recommendation": "Add security-focused tests for HTTPS, error messages, and input validation", "priority": "high", "why": "Login is the security boundary"},
                    {"recommendation": "Include accessibility checks on login form", "priority": "medium", "why": "WCAG compliance for authentication entry point"},
                    {"recommendation": "Use test-specific credentials via environment variables", "priority": "high", "why": "Avoid hardcoded credentials in test code"},
                ],
            }

        if "Specification Writer" in prompt_preview or "detailed, testable specifications" in prompt_preview:
            return {
                "specifications": [
                    {
                        "spec_id": "SPEC-001",
                        "linked_ac": "AC1",
                        "preconditions": ["User is on the login page", "Valid test credentials are available"],
                        "test_data": ["valid_username: process.env.TEST_USERNAME", "valid_password: process.env.TEST_PASSWORD"],
                        "steps": [
                            "1. Navigate to the login page",
                            "2. Enter valid username in the username field",
                            "3. Enter valid password in the password field",
                            "4. Click the login/submit button"
                        ],
                        "expected_results": [
                            "Login page loads successfully",
                            "Login form is visible with username and password fields",
                            "After submission, user is redirected to the dashboard or home page",
                            "User is logged in (session established)"
                        ],
                        "negative_behavior": ["N/A — this is the happy path"],
                        "edge_cases": ["Rapid repeated clicks on login button"],
                        "dependencies": ["Login page URL (TO_BE_DEFINED)", "Valid test credentials (TO_BE_DEFINED)"],
                        "notes": "Verify redirect destination matches expected post-login page"
                    },
                    {
                        "spec_id": "SPEC-002",
                        "linked_ac": "AC2",
                        "preconditions": ["User is on the login page", "Invalid test credentials are available"],
                        "test_data": ["invalid_username: process.env.INVALID_USERNAME or 'wronguser'", "invalid_password: process.env.INVALID_PASSWORD or 'wrongpass'"],
                        "steps": [
                            "1. Navigate to the login page",
                            "2. Enter invalid username in the username field",
                            "3. Enter invalid password in the password field",
                            "4. Click the login/submit button"
                        ],
                        "expected_results": [
                            "Login form remains visible (user not logged in)",
                            "Error message is displayed indicating invalid credentials",
                            "Error message does not reveal whether username or password was wrong",
                            "No access is granted to protected pages"
                        ],
                        "negative_behavior": ["N/A — this IS the negative test"],
                        "edge_cases": ["SQL injection characters in username field", "XSS characters in password field"],
                        "dependencies": ["Error message text (TO_BE_DEFINED)"],
                        "notes": "Verify error message does not leak whether username exists"
                    },
                    {
                        "spec_id": "SPEC-003",
                        "linked_ac": "AC3",
                        "preconditions": ["User attempts to access a protected page without authentication"],
                        "test_data": ["Protected page URL (TO_BE_DEFINED)"],
                        "steps": [
                            "1. Clear any existing session cookies",
                            "2. Navigate directly to a protected page URL",
                            "3. Observe the response"
                        ],
                        "expected_results": [
                            "User is redirected to the login page",
                            "Original destination is preserved for post-login redirect (if applicable)",
                            "No protected content is accessible without authentication"
                        ],
                        "negative_behavior": ["N/A — this is the redirect test"],
                        "edge_cases": ["Direct API access without auth token"],
                        "dependencies": ["Protected page URL (TO_BE_DEFINED)", "Login page URL (TO_BE_DEFINED)"],
                        "notes": "Test both page navigation and API endpoint access without auth"
                    },
                ],
                "traceability": "SPEC-001 -> AC1 (happy path login), SPEC-002 -> AC2 (invalid credentials), SPEC-003 -> AC3 (unauthenticated redirect)",
                "gaps": ["Exact error message text for failed login", "Exact protected page URLs", "Login page URL"],
                "to_be_defined": ["Error message text", "Login page URL", "Dashboard/protected page URL", "Test credentials"],
            }

        if "Test Designer" in prompt_preview or "design concrete test scenarios" in prompt_preview:
            return {
                "scenarios": [
                    {"id": "TC-001", "name": "Valid login redirects to dashboard", "description": "User with valid credentials logs in and is redirected to the dashboard", "linked_spec": "SPEC-001", "test_level": "UI", "automation_candidate": "yes", "manual_validation_required": False, "required_test_data": ["valid username", "valid password"], "required_environment": ["Login page accessible", "Dashboard page accessible"], "notes": "Primary happy path — highest priority"},
                    {"id": "TC-002", "name": "Invalid credentials show error", "description": "User with invalid credentials sees error message and remains on login page", "linked_spec": "SPEC-002", "test_level": "UI", "automation_candidate": "yes", "manual_validation_required": False, "required_test_data": ["invalid username", "invalid password"], "required_environment": ["Login page accessible"], "notes": "Primary negative test — verify error message quality"},
                    {"id": "TC-003", "name": "Unauthenticated access redirects to login", "description": "Attempting to access a protected page without login redirects to login page", "linked_spec": "SPEC-003", "test_level": "UI", "automation_candidate": "yes", "manual_validation_required": False, "required_test_data": [], "required_environment": ["Protected page accessible", "Login page accessible"], "notes": "Verify redirect preserves intended destination"},
                    {"id": "TC-004", "name": "Empty login fields show validation", "description": "Submitting login form with empty fields shows validation error", "linked_spec": "SPEC-002", "test_level": "UI", "automation_candidate": "yes", "manual_validation_required": False, "required_test_data": [], "required_environment": ["Login page accessible"], "notes": "Form validation — not explicitly in story but standard practice"},
                    {"id": "TC-005", "name": "Login page has accessible form labels", "description": "Login form fields have proper labels for screen readers", "linked_spec": "SPEC-001", "test_level": "Accessibility", "automation_candidate": "maybe", "manual_validation_required": True, "required_test_data": [], "required_environment": ["Login page accessible"], "notes": "Accessibility validation — may require manual or axe-core testing"},
                ],
                "scenario_count": 5,
                "coverage_summary": {
                    "happy_path": True,
                    "negative_paths": True,
                    "edge_cases": False,
                    "error_handling": True,
                    "state_transitions": True,
                },
                "gaps": ["Edge case: SQL injection in login fields", "Edge case: XSS in password field", "Edge case: Session timeout during login"],
                "uncertainties": ["Exact error message text", "Protected page URL", "Login page URL"],
            }

        if "Playwright Test Generator" in prompt_preview or "generate executable Playwright test code" in prompt_preview:
            return {
                "generated_specs": [
                    {
                        "file_path": "STORY-BASIC-001.spec.js",
                        "content": "const { test, expect } = require('@playwright/test');\n\n// STORY-BASIC-001: Web Application Login\n// Generated by QA Agent Harness AI Brain\n// Prompt version: v1.0\n\n// NOTE: Credentials and URLs must be set via environment variables.\n//   BASE_URL = process.env.BASE_URL || 'http://localhost:8080'\n//   TEST_USERNAME = process.env.TEST_USERNAME\n//   TEST_PASSWORD = process.env.TEST_PASSWORD\n\ndescribe('STORY-BASIC-001 — Login Flow', () => {\n  let page;\n  let baseUrl;\n\n  beforeEach(async ({ browser }) => {\n    page = await browser.newPage();\n    baseUrl = process.env.BASE_URL || 'http://localhost:8080';\n  });\n\n  afterEach(async () => {\n    if (page) await page.close();\n  });\n\n  test('TC-001: Valid login redirects to dashboard', async () => {\n    // Navigate to login page\n    await page.goto(baseUrl + '/login');\n    await expect(page).toHaveTitle(/.*Login.*/i);\n\n    // Fill in credentials\n    await page.fill('input[name=\"username\"]', process.env.TEST_USERNAME || 'testuser');\n    await page.fill('input[name=\"password\"]', process.env.TEST_PASSWORD || 'testpass');\n\n    // Click login\n    await page.click('button[type=\"submit\"]');\n\n    // Verify redirect to dashboard\n    await expect(page).toHaveURL(/.*dashboard.*/i, { timeout: 10000 });\n    await expect(page.locator('body')).toContainText(/.*Dashboard.*/i, { timeout: 5000 });\n  });\n\n  test('TC-002: Invalid credentials show error message', async () => {\n    await page.goto(baseUrl + '/login');\n    await expect(page).toHaveTitle(/.*Login.*/i);\n\n    await page.fill('input[name=\"username\"]', 'wronguser');\n    await page.fill('input[name=\"password\"]', 'wrongpass');\n    await page.click('button[type=\"submit\"]');\n\n    // Verify error message is shown\n    const errorMsg = page.locator('.error-message, [class*=\"error\"], #error');\n    await expect(errorMsg).toBeVisible({ timeout: 5000 });\n    await expect(errorMsg).toContainText(/.*invalid|error|credentials|failed/i, { timeout: 2000 });\n\n    // Verify still on login page\n    await expect(page).toHaveURL(/.*login.*/i);\n  });\n\n  test('TC-003: Unauthenticated access redirects to login', async () => {\n    // Try to access protected page without login\n    await page.goto(baseUrl + '/dashboard');\n\n    // Should redirect to login\n    await expect(page).toHaveURL(/.*login.*/i, { timeout: 10000 });\n    await expect(page.locator('body')).toContainText(/.*login|sign in|sign-in/i, { timeout: 5000 });\n  });\n});\n",
                        "scenario_ids": ["TC-001", "TC-002", "TC-003"],
                        "framework": "playwright",
                    }
                ],
                "spec_count": 1,
                "spec_paths": ["STORY-BASIC-001.spec.js"],
                "traceability": {
                    "TC-001": "STORY-BASIC-001.spec.js",
                    "TC-002": "STORY-BASIC-001.spec.js",
                    "TC-003": "STORY-BASIC-001.spec.js",
                },
                "validation_notes": "Generated tests use environment variables for credentials and URLs. Adjust selectors (input[name=\"username\"], etc.) to match actual page structure. The test assumes a standard login form layout.",
                "credential_requirements": ["TEST_USERNAME", "TEST_PASSWORD"],
                "environment_requirements": ["BASE_URL"],
            }

        if "QA Failure Analyst" in prompt_preview or "analyze test failures" in prompt_preview:
            return {
                "failures": [],
                "failure_count": 0,
                "classifications": {},
                "root_causes": [],
                "recommended_actions": [],
                "unresolved": [],
                "summary": "No test failures to analyze. All tests passed.",
            }

        # Default fallback for reviewer and other agents
        return {
            "summary": "Analysis complete. See detailed output for full findings.",
            "actors": [],
            "inputs": [],
            "outputs": [],
            "acceptance_criteria": [],
            "ambiguities": [],
            "missing_requirements": [],
            "dependencies": [],
            "assumptions": [],
            "unknowns": [],
            "questions": [],
            "confidence": "medium",
        }

    def chat_completion(self, messages: list[dict], **kwargs: Any) -> dict:
        """Return a canned JSON response based on the prompt content."""
        import time

        start = time.time()
        user_msg = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break

        content_obj = self._get_canned_response(user_msg[:500])
        content_str = json.dumps(content_obj, indent=2)

        # Estimate tokens (rough: 1 token ~ 4 chars)
        prompt_tokens = max(len(user_msg) // 4, 10)
        completion_tokens = max(len(content_str) // 4, 10)

        elapsed = (time.time() - start) * 1000

        return {
            "content": content_str,
            "raw_provider": self.name,
            "raw_model": self.model,
            "duration_ms": round(elapsed, 1),
            "token_usage": TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=0.0,  # noop is free
            ),
        }


# ── Provider factory ─────────────────────────────────────────────────────────

def create_provider(provider_name: str | None = None, **kwargs: Any) -> LLMProvider:
    """
    Create an LLM provider by name.

    Order of precedence:
      1. Explicit provider_name parameter
      2. AI_PROVIDER environment variable
      3. Default: "noop" (fails safely)

    Returns a configured LLMProvider instance.
    """
    name = provider_name or os.environ.get("AI_PROVIDER", "").strip().lower()

    if not name or name == "noop":
        return NoOpProvider()

    if name == "openai":
        return OpenAIProvider(**kwargs)

    if name == "local":
        return LocalProvider(**kwargs)

    # Unknown provider — fall back to noop with a warning
    print(f"WARNING: Unknown AI provider '{name}'. Falling back to noop.", file=sys.stderr)
    return NoOpProvider()


# ── Convenience: detect if any real provider is configured ───────────────────

def is_ai_configured() -> bool:
    """Return True if a real (non-noop) LLM provider can be created."""
    provider_name = os.environ.get("AI_PROVIDER", "").strip().lower()
    if not provider_name or provider_name == "noop":
        return False
    if provider_name == "openai":
        return bool(os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    if provider_name == "local":
        return bool(os.environ.get("LOCAL_LLM_BASE_URL"))
    return False


# ── Structured output helper ─────────────────────────────────────────────────

def parse_json_response(content: str) -> dict | None:
    """Try to parse a JSON response from an LLM. Returns None on failure."""
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code fences
        import re
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # Try to find JSON object anywhere
        m = re.search(r'\{.*\}', content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return None
