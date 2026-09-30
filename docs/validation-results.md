# Validation Results

## Backend implementation session — September 30, 2026

The first end-to-end fixture is a sanitized reconstruction of the real Codex run that deferred the IDE and dashboard, then implemented the CLI, batch API, trace adapters, tests, and deployment preparation.

Artifacts:

- Input: `examples/real-session.json`
- Ground truth: `examples/real-session.expected.json`
- Regression coverage: `test_real_session_matches_recorded_ground_truth`

## Ground truth

The known review findings were:

1. Docker image validation remained blocked because the local Docker daemon was unavailable.
2. Ruff failed once, corrective edits were made, and the final Ruff run passed.
3. Every changed file belonged to the approved backend scope.

Research, correction, and repeated validation steps were supporting work linked to an existing plan item, not independent scope divergence.

## Result

The final report matched both expected findings and produced no unexplained-change or plan-divergence findings:

- Priority 1: `unresolved_test_failure` for `docker_daemon_available`
- Priority 2: `recovered_test_failure` for `ruff`
- Plan alignment: pass
- Scope alignment: pass
- Verification status: blocked

The terminal report reduced a 206-line normalized trace to 8 lines, a 96.1% line-count reduction. This is an artifact-size measurement, not evidence that human diagnosis is 96.1% faster.

## Changes driven by validation

The first report duplicated failures as generic failed actions and treated routine research and correction steps as unplanned work. The engine now:

- links supporting actions to a declared `plan_step` in step metadata;
- links failed actions to structured `test_name` or `test_names` evidence;
- prefers an exact planned action over a supporting action linked to the same plan item.

## Limitations

- The trace was manually normalized from a real run, not emitted directly by Codex or NeMo.
- The validation used known ground truth from the same implementation session.
- No independent developer completed the raw-trace-versus-report timing exercise.
- Docker and Nebius deployment remain unverified until a Docker daemon and Nebius credentials are available.

The next validation should use an untouched agent-produced trace and an independent reviewer.
