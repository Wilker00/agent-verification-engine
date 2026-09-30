# Agent Verification Engine - Project Plan

## What changed in v1.3

The IDE extension and web dashboard are deferred. The current implementation scope is the verification engine, CLI, FastAPI service, trace adapters, sample artifacts, tests, and a deployable backend. No current milestone depends on UI work.

The active delivery order is:

1. Finish the generic engine and report contract.
2. Add a real `agent-verify analyze` CLI and batch API.
3. Normalize NeMo `workflow_output.json`, OpenTelemetry JSON, and OpenShell audit events into `AgentSession`.
4. Prepare the API for Nebius deployment.
5. Validate the report against raw traces and real review outcomes.

The VS Code/Cursor extension, web dashboard, and their local review controls remain product options after the backend judgment has been validated.

## What changed in v1.2

The product is the approval judgment. NeMo Agent Toolkit and OpenShell are inputs. A screen that replays their logs is out of the project, even if it looks like a demo.

The judgment is three results no trace tool emits:

1. Plan versus actual: a planned step never happened, or an unplanned step ran.
2. Unexplained scope: a file, command, or config changed with no link to the requirement.
3. A review order: where to look first, checked later against where the real bug was.

Build that on a plain session JSON before any NVIDIA parser exists. The IDE panel shows those three results. A step list, a Gantt chart, token counts, or an embedded Weave view does not ship.

## What changed in v1.1

This revision comes from the full project conversation, not a new research pass. The previous plan treated the CLI as the product. That is no longer the focus.

**Now in scope**

- The product is a verification engine with three hackathon surfaces: an IDE plugin, a FastAPI service, and a minimal web dashboard. The CLI stays as a thin local/debug entry, not the thing we demo.
- Cursor and VS Code are the IDE targets. One VS Code-compatible extension covers both.
- Nebius is the hackathon platform. The `nebius` Python SDK (0.6.16) is installed locally and should be the optional inference/host path for NIM-style serving.
- The problem is three layers, not one dashboard: trajectory reconstruction, cognitive distance, and review tax.
- The report schema now includes unexplained changes and a verification checklist, not only divergences and hotspots.
- Customer discovery has a kill gate. If real verification is already under about five minutes, we do not keep building.

**Still true, and already in v1.0**

- Problem hypothesis, research corpus, NVIDIA backbone (NeMo Agent Toolkit, OpenShell, Weave/OTel, Skills, SkillSpector, optional NIM / TensorRT-LLM), phased roadmap, and success metrics.

**Considered and left out on purpose**

- NemoClaw / OpenClaw. Useful as a secured agent runtime, but OpenShell already covers the sandbox we need. Do not add a second runtime for the hackathon.
- A new agent framework, a full debugging IDE, custom LLM-as-judge, a database, auth, or a multi-tenant SaaS.
- GitHub/GitLab App during the hackathon. That stays post-hackathon. The IDE plugin replaces it as the workflow surface judges can actually see.

---

## Executive Summary

The Agent Verification Engine solves a critical bottleneck in autonomous coding: developers need evidence-backed understanding of long agent runs without manually replaying the work.

**Problem hypothesis (validated at the phenomenon level, not yet at the customer or payment level):**

Coding agents can now generate and modify software faster than developers can confidently understand, diagnose, and verify their work, especially as autonomous tasks become longer and more complex.

**Canonical problem:**

As developers delegate larger and more autonomous coding tasks to AI agents, understanding and verifying the resulting work becomes its own engineering task. The visible failure may occur after the action that caused it. After the run, developers inspect diffs, run tests, and re-review code they did not write. A correction can invalidate the previous review. Passing tests are only partial confidence. The bottleneck is no longer generation. It is answering: what did the agent actually do, where did it diverge, what changed because of that divergence, and is the result safe enough to approve?

**Our solution:**

Compress a long coding-agent run into causal evidence: original requirement, planned steps, actual actions, divergences, unexpected file changes, unexplained changes, and ranked review hotspots. The goal is to reduce how much of the run a developer must inspect without reducing their ability to catch meaningful failures.

**Product form:**

The engine and report contract are the product core. The current surfaces are the CLI and API; IDE and web interfaces are deferred until the judgment is validated.

| Surface | Role | When |
|---|---|---|
| Verification engine (Python) | Trace model, divergence detection, hotspot ranking, report | Hackathon, first |
| IDE plugin (Cursor + VS Code) | Future inline review workflow | Deferred |
| FastAPI | `POST /analyze` and `POST /batch` for automation and later CI | Current |
| Minimal web dashboard | Future visual report surface | Deferred |
| CLI | Local and scripted analysis across supported trace formats | Current, primary local UX |
| GitHub/GitLab App | PR checks, hotspot comments, merge gate | Post-hackathon |

### Original work versus ingest

| Build this | Leave this to the tool that already does it |
|---|---|
| Plan-versus-actual diff | NeMo's record of steps, tool calls, timing, tokens |
| Link from each changed file back to the requirement, or mark it unexplained | OpenShell's allow/block audit |
| Ranked hotspots and a local approve / needs-changes decision | Weave, Phoenix, and LangSmith trace UIs |
| What must be reviewed again after a correction run | Agent orchestration, sandboxes, model serving |

A feature is in scope only when it changes one of those four rows in the left column. Parsing `workflow_output.json` is a mapper into `AgentSession`. It stays small. The demo must still make sense if every NVIDIA name is removed and the input is the sample JSON.

Before the hackathon demo, time one failed session three ways: raw transcript plus diff, the NeMo or Weave view alone, and this report. Keep building only if the report is faster to the correct cause. If the NeMo file alone matches the report, stop and change the judgment logic.

---

## Problem & Opportunity

### Three layers

1. **Trajectory reconstruction.** A coding agent inspects files, calls tools, edits code, runs tests, fails, and changes strategy. The step where an error surfaces is often not the step that caused it. Conventional diffs and stack traces do not show that sequence.
2. **Cognitive distance.** Developers review agent-written code more stringently than code they wrote, because they did not build the mental model while typing it.
3. **Review tax.** Asking the agent to fix one issue can change already-reviewed files, so the previous approval has to be done again.

### Research foundation

- **Strong evidence:** Professional developers verify agent output with diffs, tests, debuggers, rollback, chunking, and repeated review. Agent-written code creates cognitive distance. Trajectories are hard to debug with ordinary tooling. Among studied agent-assisted PRs that merged, a large share still needed human edits.
- **Moderate evidence:** Root cause can sit upstream of the visible failure. Longer sessions drift, and cursory monitoring gets worse as tasks get longer. The field evidence for *long* runs is still thin: the strongest oversight study mostly saw short tasks.
- **Not yet known:** Whether people will pay, whether one product should cover reconstruction plus verification plus debugging, and whether Phoenix, LangSmith, or AgentStepper already close the gap.
- **Gap:** Existing tools show traces. They do not answer "can I approve this without replaying it?"

### Counterevidence we keep visible

- Many agent PRs are accepted, and more than half of merged ones in the Watanabe study needed no extra edits. Agents are already useful for well-specified work.
- Developers are broadly positive and already cope by keeping tasks small.
- If interviews show "tests passed, diff is small, I merge," and verification takes only a few minutes, we stop.

### Target customer

- Experienced developers who use Claude Code, Cursor, Codex, or Copilot daily or weekly
- Delegating tasks that run about 15-60 minutes, or who *would* if review stayed tractable
- Accountable for merge approval
- Currently spending on the order of 20+ minutes verifying a substantial agent run

### Competitive gap

| Tool | What it does | Why it is not this product |
|---|---|---|
| Phoenix / Arize, LangSmith, Weave | Trace and eval UIs for people building agents | Shows what happened. Does not map requirement, plan, diff, tests, and unexplained changes into an approval decision. |
| AgentStepper | Interactive debugger for software-development-agent trajectories | Closest research tool. Not a PR/IDE review workflow. |
| AgentDebugX | Failure attribution across LLM-agent runs | Broader than code review, diffs, and merge approval. |
| XAI-for-coding-agent-failures prototypes | Structured explanations of a failed run | Covers "where it went wrong," not the full approve path. |

The wedge is information compression: fewer lines inspected, same ability to catch real failures.

### Validation plan

Do not ask "would an agent debugger be useful?" Ask people to show the last real incident.

**Priority 1 — interviews (10 heavy users if possible; 3-5 before or during the hackathon):**

- Walk the last substantial delegated task from "the agent said it was done" to "I was willing to keep the code."
- Last time the agent claimed success and was wrong: how long did diagnosis take, and where did you look first?
- When you ask for a fix, how much of the new diff do you review again?
- Last time tests passed and the change was still wrong.
- Last unexpected file, dependency, config, or command.
- Which tasks do you deliberately keep small because a larger run would be hard to review?
- An agent failure expensive enough that faster diagnosis would have been worth paying for.

Kill gate: if verification is consistently under about five minutes, the problem is smaller than the research suggests. If a 10-minute run costs 20+ minutes to verify, we have a customer.

**Priority 2 — measurement:**

- Diary of agent tasks over one week: runtime, files changed, review time, retries, unexpected edits, kept or discarded.
- Key metric: `human verification minutes ÷ agent execution minutes`, and whether that ratio grows with trajectory length or diff size.
- Re-review tax: on correction iterations, what share of already-reviewed lines changes, and how long the next review takes.
- Test-confidence audit: among green-test agent changes, how often a second look shows the task is still wrong.

**Priority 3 — smallest prototype, then measure:**

- A/B the raw transcript against the structured timeline. Hypothesis: diagnosis time drops by 30% or more, without losing root-cause accuracy.
- Build further only if reconstruction takes material time, current tools do not remove it, and the compressed view measurably cuts time-to-confidence.

---

## Project Scope & Phases

### Phase 1: Engine, CLI, and API (current)

**Goal:** A developer or automation submits an agent session through the CLI or API and gets a verification report without reading the raw transcript.

#### Deliverables

1. **Trace capture model**
   - `AgentSession` — requirement, plan, execution steps
   - `ExecutionStep` — action, tool, result, success, metadata
   - `ChangeArtifact` — file, status, summary, risk
   - `VerificationReport` — see schema below
   - Ingest hooks, even if some are stubs: NeMo `workflow_output.json`, a generic session JSON, and a Cursor/agent-transcript shaped fixture

2. **Verification report**

   The report is the product, not a log viewer.

   - Requirement
   - Original plan
   - Actual trajectory, with expected / divergence / failure markers
   - Files changed: expected vs actual
   - Divergence points
   - Unexplained changes (why was this file touched?)
   - Review hotspots ranked by risk
   - Verification checklist: requirement addressed, scope vs plan, tests, uncovered or unexamined edits
   - Status and evidence-backed checklist; no confidence score until it can be calibrated

3. **CLI (primary local UX)**
   - `agent-verify analyze <trace.json>` with automatic source detection
   - JSON and readable terminal output
   - Generic session, NeMo workflow output, and OTel trace input
   - Batch analysis for files containing multiple sessions

4. **FastAPI service**
   - `POST /analyze` — session trace in, verification report out
   - `GET /health`
   - `POST /batch` if time allows
   - No database. In-memory is enough for the hackathon.

5. **Backend deployment preparation**
   - Container-ready FastAPI process
   - Environment-driven host and port
   - Nebius deployment guidance without requiring Nebius on the analysis hot path

6. **Sample sessions and tests**
   - Two or three realistic traces: file edits, tool calls, a failing test, a retry, and at least one unplanned file
   - Tests for divergence detection, scope creep, and hotspot ranking

7. **Deferred UI surfaces**
   - VS Code/Cursor extension
   - Web dashboard
   - Local hotspot review and approve / needs-changes controls

#### Success criteria

- From the CLI or API, a 30-minute-style session becomes a report in seconds
- The report flags plan divergence, an unexpected file, and ranked hotspots
- A developer can see where to look without reading the transcript
- The same report is available from the CLI and API

---

### Phase 2: NVIDIA stack and Nebius (Hackathon, overlapping days 3-5)

**Goal:** Show the engine sitting on NVIDIA's open stack, running in the Nebius x NVIDIA hackathon environment.

#### Deliverables

1. **NeMo Agent Toolkit**
   - Accept `workflow_output.json`
   - Read intermediate steps, tool calls, and timing
   - Map them onto `AgentSession` and the verification report
   - Do not reimplement orchestration

2. **W&B Weave / OpenTelemetry**
   - Ingest a Weave or OTel trace into the same model
   - Optional export of the verification summary back to Weave
   - Phoenix and LangSmith stay compatible exporters we can consume later. We do not build another trace UI, and we do not build our own LLM-as-judge.

3. **OpenShell**
   - Read audit or sandbox events when present
   - Treat unexpected tool use as a divergence or hotspot
   - Degrade cleanly when the trace has no OpenShell data

4. **NVIDIA Skills and SkillSpector**
   - Package "review this session" as a skill only if it helps the demo
   - Use SkillSpector ideas to flag risky tool or file actions inside hotspots
   - Full skill marketplace publishing is out of hackathon scope

5. **Nebius + optional NIM / TensorRT-LLM**
   - Hackathon host is Nebius AI Cloud
   - Use the Nebius Python SDK for any hosted inference or demo environment we actually need
   - NIM or TensorRT-LLM only if we serve a model. The verification engine itself is deterministic comparison and ranking, not a training job.
   - NemoClaw stays deferred. OpenShell is the runtime boundary.

#### Success criteria

- One NeMo (or NeMo-shaped) trace flows through the engine into the shared report
- The demo can say which NVIDIA projects we use and which we deliberately did not rebuild
- Nebius is the place the demo runs, not an unused dependency

---

### Phase 3: Review workflow and GitHub (post-hackathon)

**Goal:** Make approval stick across iterations and across the PR, after the IDE plugin is already useful locally.

#### Deliverables

1. **Web dashboard beyond the one-pager**
   - Timeline, plan vs actual, annotated diffs, test and coverage summary
   - Hotspot checklist and approval state

2. **GitHub/GitLab integration**
   - PR check with the verification report
   - Hotspots as review comments
   - Optional merge block until hotspots are acknowledged

3. **Review workflow**
   - Remember which hotspots were reviewed
   - On a correction run, show what newly changed and what must be reviewed again
   - Audit trail of approvals

#### Success criteria

- A 30-minute agent PR can be reviewed in under 10 minutes
- Hotspot-first review catches most of the issues a full replay would catch
- Re-review tax is measurable and smaller on later iterations

---

### Phase 4: Evaluation (during and after the hackathon)

**Goal:** Measure time-to-confidence. Do not treat a polished demo as validation.

#### Deliverables

1. Diary study with 5-10 developers
2. Failure-reconstruction timing on 15-30 real failed sessions, comparing normal artifacts with the structured report
3. Timeline vs raw transcript A/B on diagnosis time and accuracy
4. Hotspot precision/recall against issues a human actually found
5. Re-review tax and test-confidence measurements from the validation plan

#### Success criteria

- Verification time is lower than the participant's own baseline
- Hotspot rank tracks where people actually spend review time
- We can state, with the kill gate in view, whether to keep building

---

## Hackathon week

Build the engine, CLI, API, and trace adapters. Do not spend the current implementation phase on UI surfaces or a GitHub App.

| Day | Outcome |
|---|---|
| 1 | Sample traces. Report schema locked. Engine turns one trace into divergences, unexplained files, and hotspots. |
| 2 | CLI and batch API using the same report. Tests for scope creep. |
| 3 | FastAPI `/analyze`. Start NeMo `workflow_output.json` ingest. |
| 4 | OTel and OpenShell-aware ingest after the NeMo path works. |
| 5 | Demo polish, README, and a timed before/after on one session. |

**Demo (about five minutes):**

1. State the bottleneck: generation is cheap, confidence is expensive.
2. Analyze a long agent session with the CLI. Show requirement, plan vs actual, an unplanned file, and ranked hotspots.
3. Submit the same trace to the API and show the identical report contract.
4. Give the timing: raw transcript vs the structured report.
5. Name the stack: NeMo Agent Toolkit for capture, Weave/OTel for traces, OpenShell for the safety boundary, Nebius as the hackathon host, NIM only if we are serving a model.
6. Say what is next: GitHub checks, hosted dashboard, marketplace listing. Mention interviews only if they actually happened.

---

## Technical Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Autonomous coding agent                                     │
│  Cursor, Claude Code, Codex, Copilot, LangChain, CrewAI     │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ├─→ NeMo Agent Toolkit
                             │     workflow_output.json, intermediate steps
                             ├─→ OpenShell audit (when present)
                             ├─→ W&B Weave / OpenTelemetry
                             └─→ Generic session JSON / IDE transcript
                                          │
                                          ▼
                             Agent Verification Engine
                               normalize → plan vs actual
                               → unexplained changes
                               → risk-ranked hotspots
                               → verification report
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              ▼                           ▼                           ▼
     IDE plugin (primary)          FastAPI /analyze            One-page web UI
     Cursor + VS Code              CLI is a thin client        Judge + later SaaS
                                          │
                                          ▼
                             Post-hackathon: GitHub/GitLab App

     Nebius AI Cloud: hackathon host and optional NIM / model serving
```

### Components

1. **Ingest** — NeMo workflow output, Weave/OTel, OpenShell audit, generic session JSON, IDE transcript fixtures. One `AgentSession` shape.
2. **Engine** — plan vs actual, unexpected steps, scope creep, risk score, hotspot rank. Heuristics first. No custom judge model in the hackathon.
3. **Report** — requirement, plan, trajectory, expected vs actual files, divergences, unexplained changes, ranked findings, and checklist.
4. **API** — `/analyze`, `/health`, optional `/batch` and `/export`.
5. **IDE plugin** — deferred side panel and review controls.
6. **Web** — deferred visual report surface.
7. **CLI** — analyzes generic, NeMo, and OTel JSON for local and scripted workflows.
8. **Later hooks** — GitHub/GitLab, Slack, Weave embed.

### Hackathon technical constraints

- Python 3.11+ engine, FastAPI, Pydantic. No database and no auth.
- CLI and API use the same normalization and report code.
- Demo deploy: stateless API container on Nebius.
- `nebius` is an optional extra, not a required import on the verification hot path.

---

## Milestones & Timeline

### Week 1 (hackathon build)

- [x] Problem research and repo skeleton
- [x] Nebius SDK installed locally (`nebius` 0.6.16)
- [x] Report schema and initial sample traces
- [x] Engine: divergences, unexplained changes, hotspots
- [x] CLI and FastAPI batch workflow
- [x] NeMo, OTel, and OpenShell-aware ingest
- [x] Nebius deployment preparation
- [ ] Timed demo against raw traces
- [ ] IDE plugin side panel in Cursor/VS Code (deferred)
- [ ] One-page dashboard (deferred)

### Week 2-3 (if the hackathon runs long, or immediately after)

- [x] OTel ingest; direct Weave export remains optional
- [x] OpenShell-aware audit fields and blocking findings
- [ ] Interview notes against the kill gate
- [ ] Decide whether SkillSpector checks belong in hotspot scoring

### Post-hackathon

- [ ] Timing study and A/B against raw transcripts
- [ ] GitHub/GitLab App
- [ ] Review-state across correction runs
- [ ] Hotspot accuracy tuning
- [ ] Continue only if the decision gate passes

---

## Success Metrics

### Hackathon

- CLI and API render a real or realistic session without the raw transcript
- Report shows at least one divergence, one unexpected file, and ranked hotspots
- Same report from CLI and API
- NeMo-shaped trace ingested
- One measured diagnosis-time comparison, even if the sample is small
- NVIDIA and Nebius roles are accurate in the pitch

### Customer validation

- Verification minutes / agent minutes moves in the direction of the diary study, with a target below 0.5 only as a hypothesis
- Structured report is 30%+ faster to a correct root cause than the raw transcript
- Hotspot precision is good enough that people trust the ranking (80% is a target, not a claim we have earned)
- Kill gate checked explicitly

### Product fit, later

- Teams use the IDE plugin on real agent work
- Agent PR review commonly finishes in under 10 minutes
- Re-review on correction runs is smaller than a full second pass

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Trace formats differ across Cursor, Claude Code, Codex, and NeMo | Engine cannot read real runs | High | One normalizer per source. Hackathon fixtures first. NeMo JSON as the NVIDIA path. |
| IDE plugin takes longer than a CLI | Demo slips | Medium | Side panel plus local JSON first. No marketplace packaging during the hackathon. |
| Developers will not install a plugin | No workflow value | Medium | Same report on the web page. Plugin must beat reading the transcript on one real session. |
| Divergence false positives | People ignore hotspots | Medium | Prefer missed-file and unplanned-file signals. Allow a hotspot to be marked reviewed. |
| Long-run pain is still a hypothesis | We build for a segment that does not exist yet | Medium | Interviews and the kill gate before any post-hackathon platform work. |
| NVIDIA or Nebius scope creep | Hackathon becomes an integration tour | Medium | Use NeMo, Weave/OTel, and OpenShell only where they feed the report. Defer NemoClaw. |
| GitHub App complexity | Eats the week | High if started now | Explicitly post-hackathon. |

---

## Go-to-Market (post-hackathon)

### Positioning

Coding agents generate code faster than developers can verify it. Agent Verification Engine compresses the run into causal evidence — what was planned, where it diverged, what changed without explanation, and where to review first — inside the IDE, so a developer can approve or reject without replaying the work.

### Segments

1. **First:** developers and small teams living in Cursor or VS Code on 15-60 minute agent tasks.
2. **Next:** teams that need a PR check and an audit trail (GitHub/GitLab).
3. **Later:** compliance-heavy environments, and partnerships with IDE or agent vendors. Those are distribution, not the first product.

### Pricing sketch

- **Engine + CLI:** open source.
- **IDE plugin:** free locally, with a later paid tier for team review state.
- **Hosted dashboard:** about $49/month when there is a real hosted service. Not part of the hackathon.
- **Enterprise:** GitHub/GitLab enforcement, audit trail, and deployment help.

Prices stay a sketch until someone asks to pay.

---

## Vision

If the decision gate passes, six months out looks like: the IDE plugin is how people review agent work, a hosted report exists for teams, GitHub checks exist for merges, and review time on a substantial agent change is routinely under 10 minutes. NVIDIA alignment should be a real ingest path, not a logo slide. Fundraising follows evidence, not the hackathon demo.

---

## Next actions

1. Lock the verification report JSON and add two sample sessions, including one unplanned file and one failed-then-retried test. No NeMo file required.
2. Replace the placeholder summarizer so a plain session emits plan-versus-actual, unexplained scope, and a review order.
3. Add a thin NeMo `workflow_output.json` mapper and OTel/OpenShell-aware adapters.
4. Add CLI and API batch workflows over the same report contract.
5. Prepare and document the Nebius deployment path.
6. Run the three-way timing check on one failed session before calling the demo done.
7. Run the interview script with 3-5 people who already use coding agents. Record actual minutes, not opinions.

---

## Resources & Dependencies

### Team

- **Lead:** Wilker00 (engine, architecture)
- **IDE plugin, NVIDIA ingest, interviews, UI:** still unassigned

### Dependencies

- Python 3.11+, FastAPI, Pydantic, Uvicorn
- VS Code extension host (Cursor-compatible)
- NVIDIA NeMo Agent Toolkit, W&B Weave, OpenTelemetry
- OpenShell when we have audit events to parse
- Nebius Python SDK for hackathon hosting / optional inference
- Next.js or a single React page for the demo UI

### Infrastructure

- GitHub repo: https://github.com/Wilker00/agent-verification-engine
- Local API during the hackathon
- Nebius project for anything that must run on the hackathon cloud
- A real Cursor or Claude Code session we are allowed to sanitize and use as a fixture

---

## Decisions and open items

**Decided**

- CLI plus API are the current product surfaces.
- Cursor/VS Code extension and one-page dashboard are deferred.
- GitHub integration is post-hackathon.
- No new agent framework, no custom LLM-as-judge, no NemoClaw in the hackathon.
- NVIDIA stack we actually use: NeMo Agent Toolkit, OpenShell, Weave/OTel, and Skills/SkillSpector only where they improve the report. NIM/TensorRT-LLM only if we serve a model.

**Still open**

1. Which live agent produces the demo trace: Cursor, Claude Code, or a NeMo example we generate ourselves?
2. Do we ask the NeMo maintainers for the exact `workflow_output.json` fields before we parse them?
3. Does SkillSpector run in the hackathon build, or only inform the risk labels?
4. Is the open-source core sustainable if the hosted product is the paid part?

---

## Out of scope for the hackathon

- Replaying a NeMo, OpenShell, Weave, Phoenix, or LangSmith trace as the product UI
- Gantt charts, span waterfalls, token dashboards, and raw step lists
- Agent orchestration, a second sandbox, or model serving
- GitHub or GitLab App, OAuth, and merge blocking
- Marketplace publishing and auto-update infrastructure
- Accounts, teams, billing, and a database
- VS Code/Cursor extension and web dashboard during the current backend phase
- A general-purpose agent debugger or a new agent runtime
- Training or fine-tuning a judge model
- NemoClaw, NVIDIA Skills, SkillSpector, and NIM / TensorRT-LLM until a later gate says the judgment needs them

---

## Appendix: Research references

Claims below are grounded in 2024-2026 primary sources. The plan does not treat long-run pain or willingness to pay as settled.

- Dhanorkar, Passi & Vorvoreanu (2026): Human oversight of agentic systems in practice
- Huang, Reyna, Lerner, Xia & Hempel (2025-2026): Professional Software Developers Don't Vibe, They Control
- Hutter & Pradel (2026): AgentStepper
- Chen, Talwalkar, Brennan & Neubig (2025): Code with Me or for Me?
- Bouzenia & Pradel (2025): Understanding Software Engineering Agents
- Watanabe et al. (2025-2026): On the Use of Agentic Coding
- Zhu et al. (2026): AgentDebugX
- Majgaonkar et al. (2025): Understanding Code Agent Behaviour
- Joshi (2026): XAI for Coding Agent Failures

---

**Document Version:** 1.2
**Last Updated:** Sept 30, 2026
**Owner:** Wilker00
**Status:** Active. The product is the approval judgment; CLI and API are the current surfaces.
