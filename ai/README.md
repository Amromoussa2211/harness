# AI Brain for QA Agent Harness

This directory contains the AI reasoning layer for the QA Agent Harness.

## Architecture

```
ai/
  __init__.py    — package init, re-exports
  provider.py    — LLM provider abstraction (OpenAI, local, noop)
  config.py      — AI configuration (env + project.yaml, secrets from env only)
  context.py     — context builder (selects relevant artifacts per agent)
  agent.py       — base agent framework, structured outputs, validation, retry
  engine.py      — AI engine orchestrator (run management, agent routing)
  agents/        — individual agent implementations
  prompts/       — versioned prompt templates (future)
  schemas/       — JSON schemas for agent output validation (future)
```

## Provider Abstraction

```
LLMProvider (abstract)
  ├── OpenAIProvider  — OpenAI API (GPT-4, o1, etc.)
  ├── LocalProvider   — any OpenAI-compatible server (LM Studio, Ollama, etc.)
  └── NoOpProvider    — returns structured canned responses (demo, no LLM)
```

## Execution Modes

- **Deterministic mode** (default): uses existing 14-stage deterministic logic
- **AI mode**: routes reasoning stages through LLM agents
  - Same story, same project, isolated AI run artifacts
  - LLM is optional — if not configured, AI mode is blocked with clear message
  - AI does NOT execute tests — deterministic execution remains

## Agent Roles

| Agent | Stage(s) | Responsibility |
|-------|----------|----------------|
| Analyst | analysis | Requirement interpretation, ambiguity detection |
| Grill | grill | QA questioning, challenge assumptions |
| Risk | risk | Risk identification and assessment |
| Architect | architecture | Test strategy and architecture recommendations |
| Specification | specification | Detailed testable specifications |
| Test Designer | test-design | Concrete test scenarios from specs |
| Test Generator | execution | Playwright test code generation |
| Failure Analysis | failure-analysis | Root cause analysis of failures |
| Reviewer | review | Independent QA review of work product |

## Configuration

Environment variables (take precedence):
```
AI_ENABLED=true|false
AI_PROVIDER=openai|local|noop
AI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.3
AI_API_KEY=sk-...            # required for openai/local
LOCAL_LLM_BASE_URL=http://localhost:1234/v1
LOCAL_LLM_MODEL=...
```

Project.yaml ai: section (environment overrides):
```yaml
ai:
  enabled: true
  provider: openai
  model: gpt-4o-mini
  temperature: 0.3
  prompt_version: v1.0
```

## Security

- No API keys from project.yaml — env only
- AI agents receive ONLY relevant artifacts, not the full repository
- AI output is validated against expected schemas
- AI does NOT execute arbitrary commands
- AI does NOT make HTTP calls outside provider abstraction
- Secrets are never exposed in AI prompts or outputs

## Prompt Versioning

Each agent has a `prompt_version` field. The orchestrator records it
in all agent results and the final report. This enables:
- Reproducibility (same prompt version = same behavior)
- Comparison across runs
- Upgrade tracking

## Run Isolation

Each AI-enabled run creates an isolated `ai-runs/<run_id>/` directory
under shared-state with all context, prompts, and results.
This allows comparison between deterministic and AI runs of the same story.

## Comparison Reporting

When both deterministic and AI runs exist for the same story,
the harness generates a comparison report showing:
- Which agents succeeded/failed in each mode
- Output quality comparison
- Execution results (deterministic is authoritative)
- Recommendations
