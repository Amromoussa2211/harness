---
name: qa-run
description: Runtime entry point for starting or resuming a QA run for a story. Initializes shared state, detects existing runs, resolves the first incomplete stage, and drives the workflow defined in orchestrator/workflow.md.
version: 0.1.0
---

# QA Run

## Purpose

Provide the runtime entry point for the QA Agent Harness. A user points the runtime at a story file, and the runtime either initializes a new QA run or resumes an existing one, then drives the workflow stage by stage until the run reaches a terminal status.

This skill is the narrow bridge between a user's story file and the workflow defined in `orchestrator/workflow.md`. It does not implement any QA methodology itself. It does not invent project-specific information. It owns only the run lifecycle: initialize, resume, advance, block, fail, restart, and finish.

## Inputs

### Required

- A story file path of the form `projects/<project-name>/stories/<story-id>.md`, or an equivalent reference that resolves to the same content.
- The story file must contain the story text and, if present, the acceptance criteria.

### Optional

- A directive to resume an existing run for the same story.
- A directive to restart a specific stage.
- A directive to abort the run.
- Answers to clarification questions, if any exist in shared state.

## Rules

- Follow AGENTS.md.
- Never invent requirements.
- Never invent credentials.
- Never invent URLs.
- Never invent selectors.
- Never invent API contracts.
- Never invent database schemas.
- Never invent business rules.
- Never bypass safety gates.
- Never execute destructive production actions without explicit authorization from the project safety configuration.
- Never create real financial transactions without explicit authorization.
- Never assume a specific company, application, URL, framework, database, or CI provider.
- Read the project adapter before acting.
- Read existing shared-state artifacts before resuming.
- Mark a stage as blocked when required information is missing, and record the reason.
- Mark a stage as failed when an agent fails, and preserve its artifacts.
- When tests fail, continue to Failure Analysis rather than treating the whole QA run as failed.
- Do not modify application code during orchestration unless a specialist stage explicitly requires implementation and the project configuration allows it.
- Do not over-engineer.
- Keep the runtime company-independent. The same runtime works for any project that provides a conforming project adapter and story file.

## Story Path Validation

### Valid path shape

A story path is valid when it matches the pattern:

```
projects/<project-name>/stories/<story-id>.md
```

Where:

- `<project-name>` is a non-empty directory name under `projects/`.
- `<story-id>` is a non-empty identifier without path separators.
- The file exists and is readable.

### Validation steps

1. Resolve the path.
2. Confirm the file exists.
3. Confirm the file is readable.
4. Extract `<project-name>` and `<story-id>` from the path.
5. Confirm that `projects/<project-name>/` exists and contains a project adapter.

If the path does not match the expected shape, the runtime reports the path as invalid and stops. Do not guess the project name or story id from other sources.

### Story file content

Read the story file. The runtime uses the file's content as the story text for intake. If the file is empty or cannot be parsed as text, the runtime reports the story file as unusable and stops.

## Project Identification

The project is identified from the story path, not from the story content and not from assumptions.

1. Extract `<project-name>` from the path.
2. Confirm that `projects/<project-name>/` exists.
3. Confirm that `projects/<project-name>/project.yaml` exists and is readable.
4. Load the project adapter.

If the project directory or adapter does not exist, the runtime reports that the project cannot be identified and stops. Do not search other directories for a project adapter.

## Project Adapter Loading

Load `projects/<project-name>/project.yaml`.

The runtime treats the project adapter as the sole source of project-specific configuration. It reads, at minimum:

- Application type flags.
- API type flags.
- Database flag and type.
- Environment declarations.
- Safety configuration.
- CI provider, if declared.
- Automation framework and language hints, if declared.

The runtime does not modify the project adapter. The runtime does not invent values that are missing from it. Missing values are recorded as unknowns or as blocking missing information where the workflow requires them.

## Run Initialization

### When to initialize

Initialize a new run when no existing run is detected for the story id (see Detection of an Existing Run).

### What initialization creates

Under `shared-state/<story-id>/`, the runtime creates:

- `story-intake.md` — copied or referenced from the story file content, with the story text and acceptance criteria captured.
- `stage-status.json` — the stage status document for the whole run.
- The stage output directories listed in the workflow, ready for later use.

### Story intake

The runtime creates `shared-state/<story-id>/story-intake.md` containing:

- The story text.
- The acceptance criteria, if present in the story file.
- The source path.
- The project name.
- The story id.
- The initialization timestamp.

The runtime does not invent acceptance criteria. If the story file does not contain acceptance criteria, the intake records that acceptance criteria are absent.

### Stage status creation

The runtime creates `shared-state/<story-id>/stage-status.json` with all fourteen workflow stages set to `pending`, except Stage 1, which is set to `in_progress` and then immediately to `completed` once story intake is written.

The stage list in `stage-status.json` must match the workflow stages exactly:

1. story-intake
2. discovery
3. analysis
4. grill
5. risk
6. architecture
7. specification
8. test-design
9. delegation
10. execution
11. failure-analysis
12. review
13. evidence
14. final-report

Each entry records:

- `status` — one of the six statuses.
- `started_at` — when the stage was last started, if applicable.
- `completed_at` — when the stage was last completed, if applicable.
- `blocked_reason` — why the stage is blocked, if blocked.
- `failed_reason` — why the stage failed, if failed.
- `skip_reason` — why the stage was skipped, if skipped.
- `artifacts` — a list of artifact paths produced by the stage, if any.

### Run metadata

The runtime records run metadata alongside stage status, including:

- The project name.
- The story id.
- The story source path.
- The project adapter path.
- The workflow version referenced.
- The overall run status, initially `running`.

## Detection of an Existing Run

Before initializing, the runtime checks whether `shared-state/<story-id>/` already exists and contains a `stage-status.json`.

### If an existing run is detected

The runtime treats the run as resumable. It proceeds to Resume Behavior.

### If no existing run is detected

The runtime treats the run as new. It proceeds to Run Initialization.

### Ambiguous case

If `shared-state/<story-id>/` exists but `stage-status.json` is missing or unreadable, the runtime reports the existing run state as corrupt, lists what it found, and asks whether to restart the run from scratch. The runtime does not guess the stage status.

## Resume Behavior

When resuming an existing run, the runtime:

1. Reads `shared-state/<story-id>/stage-status.json`.
2. Reads the run metadata.
3. Validates that the project adapter at `projects/<project-name>/project.yaml` still exists and is readable.
4. If the project adapter has been removed or is unreadable, the runtime reports that the project adapter is missing and blocks the run. The run cannot resume without a project adapter.
5. Reads the shared-state artifacts that exist for the completed stages, so the runtime can pass them to downstream stages.
6. Finds the first stage whose status is not `completed` and not `skipped`.
7. Acts on that stage according to its status and the Stage Transition Rules.

The runtime does not assume a run is healthy just because a `stage-status.json` exists. It validates the file and the artifacts it references before resuming.

## Detection of the First Non-Compducted/Non-Skipped Stage

The runtime scans `stage-status.json` in workflow order and finds the first stage where `status` is not `completed` and not `skipped`.

### If that stage is `pending`

The runtime starts the stage. It sets the stage to `in_progress`, records `started_at`, and invokes the stage.

### If that stage is `in_progress`

The runtime asks whether to resume or restart the stage. If resuming, the runtime continues the stage from its current state. If restarting, the runtime applies Safe Restart Behavior.

### If that stage is `blocked`

The runtime reports the block reason and stops advancing. The run remains blocked until the block is resolved. The runtime does not auto-clear a block.

### If that stage is `failed`

The runtime reports the failure reason and stops advancing. The run remains failed until the failure is resolved. The runtime does not auto-recover from a failure.

### If all stages are `completed` or `skipped`

The runtime calculates the final run status and produces or finalizes the final report. It does not re-run completed stages.

## Invocation of the Workflow

The runtime drives the workflow defined in `orchestrator/workflow.md` stage by stage. For each stage:

1. Confirm the stage's preconditions are met, using the shared-state artifacts from upstream stages and the project adapter.
2. Set the stage to `in_progress` if it is not already.
3. Invoke the responsible agent or skill named in the workflow for that stage.
4. Pass the required inputs and shared-state inputs named in the workflow.
5. Collect the stage's output artifacts.
6. Validate the stage's outputs using the validation checks named in the workflow.
7. On success, set the stage to `completed`, record `completed_at`, and record the artifact paths.
8. On block, set the stage to `blocked`, record the reason, and stop advancing.
9. On failure, set the stage to `failed`, record the reason, preserve the artifacts, and stop advancing.
10. On skip, set the stage to `skipped`, record the reason, and continue to the next stage.

The runtime does not implement the QA logic of any stage. It delegates that logic to the agents and skills named in the workflow. The runtime is responsible for orchestration, state, validation, and transition rules only.

## Reading and Writing Shared-State Artifacts

### Reading

Before each stage, the runtime reads the shared-state artifacts that the workflow requires for that stage. The runtime reads them from `shared-state/<story-id>/`. If a required artifact is missing, the runtime treats that as a missing-input condition and blocks the stage with the reason recorded.

### Writing

After each completed stage, the runtime records the artifact paths the stage produced in `stage-status.json`. The runtime does not rewrite or edit the artifacts themselves. The runtime only records what the stage produced.

### Integrity

The runtime does not assume an artifact exists just because its path is recorded. If a later stage references an artifact that is missing, the runtime blocks the later stage with the reason `referenced artifact missing`.

## Stage Transition Validation

Before transitioning a stage from `in_progress` to `completed`, the runtime validates:

1. The stage's output artifacts exist.
2. The stage's outputs satisfy the validation checks named in the workflow for that stage.
3. The stage did not invent project-specific information that is not in the project adapter or shared state. The runtime cannot fully check this automatically, but it records the expectation and surfaces any evidence of invented information that the stage's output or a later review reveals.
4. The stage's status is consistent with its artifacts.

If validation fails, the runtime does not mark the stage `completed`. It marks the stage `failed` with the validation failure reason and preserves the artifacts for diagnosis.

## Blocked-Stage Handling

When a stage is blocked:

1. The runtime sets the stage to `blocked`.
2. The runtime records the block reason.
3. The runtime stops advancing the workflow.
4. The runtime reports the block to the user, including the stage, the reason, and what is needed to unblock it.
5. The runtime does not proceed to downstream stages.

A blocked stage can be unblocked by a human providing the missing information or by the conditions that caused the block being resolved. Once unblocked, the stage is set back to `pending` and the workflow resumes from that stage.

The runtime does not invent the missing information to clear a block.

## Failed-Stage Handling

When a stage fails:

1. The runtime sets the stage to `failed`.
2. The runtime records the failure reason.
3. The runtime preserves the stage's artifacts.
4. The runtime stops advancing the workflow.
5. The runtime reports the failure to the user, including the stage, the reason, and the artifacts that were preserved.

A failed stage can be restarted if the failure is resolved. Restarting a failed stage follows Safe Restart Behavior. Once restarted, the downstream stages are reset to `pending`.

The runtime does not silently treat a failed stage as completed.

## Safe Restart Behavior

A stage restart is safe when:

1. The stage is explicitly marked for restart by a user directive or by the runtime detecting that its artifacts are incomplete or invalid.
2. The stage and all downstream stages are reset to `pending`.
3. Upstream completed stages are preserved.
4. The restarted stage re-runs its preconditions and validation checks.
5. Any shared-state artifacts that the restarted stage is expected to produce are removed or marked stale before the restart, so the restarted stage does not accidentally read stale output from the failed attempt.

The runtime does not restart a stage without an explicit reason. It does not restart a stage silently during resume.

## Final Run Status Calculation

When the workflow reaches a point where no further stage can advance, the runtime calculates the final run status.

### Completed

All stages are `completed` or `skipped` with recorded reasons. The final status is `completed`.

### Partial

The workflow ended, but some stage outputs are missing or the final report is partial. The final status is `partial`.

### Blocked

The workflow stopped at a stage that is `blocked` and the block was not resolved. The final status is `blocked`.

### Failed

The workflow stopped at a stage that is `failed` and the failure was not resolved. The final status is `failed`.

### Aborted

The user aborted the run. The final status is `aborted`.

The runtime records the final status in `stage-status.json` and in the run metadata. The runtime does not claim a run is `completed` when it is not.

## Stage Status Reference

The runtime uses exactly these six statuses:

- `pending` — not yet started.
- `in_progress` — started but not completed.
- `completed` — finished, artifacts present, validated.
- `blocked` — cannot proceed; reason recorded.
- `failed` — the stage itself failed; reason recorded, artifacts preserved.
- `skipped` — deliberately skipped with a recorded reason.

No other status values are allowed.

## Command/Interface Example

### Start a new QA run

Provide a story file:

```
projects/demo/stories/STORY-001.md
```

The runtime:

1. Validates the story path.
2. Identifies the project as `demo`.
3. Loads `projects/demo/project.yaml`.
4. Detects that no existing run exists for `STORY-001`.
5. Initializes the run under `shared-state/STORY-001/`.
6. Writes `story-intake.md` and `stage-status.json`.
7. Sets the first stage, `story-intake`, to `completed`.
8. Finds the first non-completed, non-skipped stage.
9. Invokes that stage per the workflow.
10. Advances stage by stage until the run reaches a terminal status.

### Resume an existing QA run

Provide the same story file again:

```
projects/demo/stories/STORY-001.md
```

The runtime:

1. Validates the story path.
2. Identifies the project as `demo`.
3. Loads `projects/demo/project.yaml`.
4. Detects that `shared-state/STORY-001/stage-status.json` exists.
5. Reads the stage status.
6. Finds the first non-completed, non-skipped stage.
7. If that stage is `pending`, starts it.
8. If that stage is `in_progress`, asks whether to resume or restart.
9. If that stage is `blocked` or `failed`, reports the state and waits.
10. Advances from there per the workflow.

### Restart a stage

The user can request a restart of a specific stage by name. The runtime:

1. Confirms the stage exists.
2. Resets the stage and all downstream stages to `pending`.
3. Preserves upstream completed stages.
4. Removes or marks stale any artifacts the restarted stage is expected to produce.
5. Sets the restarted stage to `pending`.
6. Resumes from that stage.

### Abort a run

The user can request an abort. The runtime:

1. Sets the overall run status to `aborted`.
2. Records the abort reason and the stage at which the run was aborted.
3. Stops advancing.
4. Preserves existing artifacts.

## What the Runtime Does Not Do

The runtime does not:

- Invent requirements, acceptance criteria, credentials, URLs, selectors, API contracts, database schemas, or business rules.
- Implement QA methodology. That belongs to the agents and skills.
- Modify application code unless a specialist stage explicitly requires implementation and the project configuration allows it.
- Override safety gates.
- Execute destructive production actions without explicit authorization.
- Create real financial transactions without explicit authorization.
- Assume a specific company, application, URL, framework, database, or CI provider.
- Clear a block or failure automatically.
- Pretend a run is complete when it is not.

## Safety Notes

The runtime enforces the safety gates defined in the workflow at delegation and execution time. The runtime does not enforce them at intake or discovery time, because those stages do not act on environments. The runtime records the safety configuration from the project adapter and passes it to the stages that need it.

The runtime never asks the user to provide invented credentials, URLs, selectors, API contracts, or database schemas. If a stage reports that such information is missing, the runtime records the block and asks the user to provide the missing project-specific information through the project adapter or the appropriate channel, not through invented values in the conversation.

## Output

At the end of a run, the runtime reports:

- The story id and project.
- The overall run status.
- The stage status of every stage.
- The location of the final report, if produced.
- Any blocked or failed stages and their reasons.
- Any remaining actions that require human follow-up.

The runtime does not produce a final report itself. The final report is produced by Stage 14 as defined in the workflow. The runtime only drives Stage 14 and reports its outcome.

## Quality Checks

Before finishing a run, the runtime verifies:

- `stage-status.json` is valid and complete.
- The overall run status matches the stage statuses.
- The final report location is recorded if the final report stage completed.
- Any blocked or failed stage has a recorded reason.
- Any skipped stage has a recorded reason.
- No stage is left in `in_progress` unless the run was aborted or interrupted.
- The project adapter used for the run is recorded in the run metadata.

## Relationship to the Workflow

This skill implements the runtime that executes the workflow in `orchestrator/workflow.md`. It does not redefine the stages, the agents, the skills, or the handoffs. It reads the workflow to determine which agent or skill owns each stage, what inputs each stage requires, what outputs each stage must produce, and what validation checks each stage must satisfy. If the workflow changes, this skill must be updated to match.
