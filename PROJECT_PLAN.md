# Agent Verification Engine - Project Plan

## Executive Summary

The Agent Verification Engine solves a critical bottleneck in autonomous coding: developers need evidence-backed understanding of long agent runs without manually replaying the work.

**Problem Statement (Research-Validated):**
As developers delegate longer and more autonomous coding tasks to AI agents, understanding and verifying the resulting work becomes an increasingly separate engineering task. The visible failure may occur after the action that caused it, forcing developers to reconstruct earlier steps, tool calls, and code modifications to locate the root cause. Corrections can create further changes that need another review, while passing tests may provide only partial confidence if test coverage doesn't capture the intended behavior.

**Our Solution:**
Compress long coding-agent runs into evidence-backed verification artifacts that answer: "What did the agent do, where did it diverge, what changed unintentionally, and is this safe to approve?"

---

## Problem & Opportunity

### Research Foundation

- **Strong Evidence (6/9 sources):** Developers use diffs, tests, debuggers, rollback, chunking, and repeated review as manual compensation for agent opacity
- **Moderate Evidence (3/9 sources):** Trajectory reconstruction is technically hard; root-cause attribution requires backward tracing; longer tasks create more drift
- **Gap:** Existing tools (Phoenix, AgentStepper, LangSmith) show traces but don't answer "can I trust this without replaying it?"

### Target Customer

- Senior/experienced developers (3+ years experience)
- Using autonomous coding agents weekly or daily
- Delegating tasks 15-60+ minutes long
- Responsible for code review and merge approval
- Currently spending 20+ minutes per agent run on verification

### Validation Plan

**Interview questions** (priority 1):
- "Show me the last agent-generated code you had to verify or fix"
- "How long did it take to understand what went wrong?"
- "What would have made diagnosis faster?"

**Measurement** (priority 2):
- Capture: agent execution time, files changed, review time, debugging time, retries
- Key metric: `human verification minutes ÷ agent execution minutes`

**Proof of concept** (priority 3):
- A/B test: raw transcript vs. structured timeline for diagnosis speed
- Hypothesis: structured timeline reduces diagnosis time by 30%+

---

## Project Scope & Phases

### Phase 1: MVP Trace Model & Verification Report (Weeks 1-2, Hackathon)

**Goal:** Build a working proof of concept that converts raw agent execution into actionable verification artifacts.

#### Deliverables

1. **Trace Capture Model**
   - `AgentSession` — session metadata, requirement, plan, execution steps
   - `ExecutionStep` — individual actions with tool calls, results, timestamps
   - `ChangeArtifact` — file-level modifications with risk scoring
   - Integration hooks for NeMo Agent Toolkit, W&B Weave, OTel

2. **Verification Report Generator**
   - Input: raw trace (plan + actual steps)
   - Output: structured report with:
     - Original requirement & intended plan
     - Actual actions taken
     - Divergence points (where plan != actual)
     - Files changed (expected vs unexpected)
     - Risk-scored review hotspots
     - Verification status & confidence score

3. **CLI Tool**
   - `agent-verify analyze <session.json>` — produces verification report
   - `agent-verify report <session.json> --format json|html|terminal` — format options
   - Human-readable terminal output with colored hotspots

4. **FastAPI Service**
   - `POST /analyze` — accepts session trace, returns verification report
   - `GET /health` — health check
   - `POST /batch` — analyze multiple sessions

5. **Sample Session & Test Cases**
   - Real or realistic coding-agent traces (file modifications, tests, retries, errors)
   - Test cases for divergence detection, scope creep, risk scoring

#### Success Criteria

- CLI tool successfully analyzes a 30-minute agent session
- Report identifies 3+ divergence points
- Developers can review report in <5 minutes
- Confidence score correlates with actual safety of the change

---

### Phase 2: NVIDIA Stack Integration (Weeks 2-3)

**Goal:** Wire the core pipeline into NVIDIA's open-source ecosystem.

#### Deliverables

1. **NeMo Agent Toolkit Integration**
   - Capture `workflow_output.json` from NeMo runs
   - Parse `intermediate_steps`, tool calls, timing data
   - Extract requirement, planned steps, actual actions
   - Plug into Phase 1 verification report

2. **W&B Weave / OpenTelemetry Export**
   - Ingest Weave traces for trace reconstruction
   - Export verification reports back to Weave dashboard
   - OTel collector support for self-hosted deployments

3. **OpenShell Runtime Safety**
   - Parse OpenShell audit logs (restricted tool execution)
   - Flag unexpected tool access in verification report
   - Integrate sandbox boundaries into divergence detection

4. **NVIDIA Skills Registration**
   - Create a "code-review" skill for agents
   - Package verification logic as inspectable agent capability
   - SkillSpector validation for risk-flagged changes

#### Success Criteria

- NeMo Agent Toolkit workflow → verification report (end-to-end)
- W&B Weave dashboard shows verification hotspots alongside traces
- OpenShell audit logs inform scope-creep detection
- Skills framework recognizes and validates review actions

---

### Phase 3: Developer Verification UI (Weeks 3-4)

**Goal:** Create an interactive interface for reviewing and approving agent work.

#### Deliverables

1. **Web Dashboard (Next.js / React)**
   - Timeline view of agent execution
   - Plan vs actual comparison
   - File diff browser with risk annotations
   - Test results and coverage summary
   - Review hotspots highlighted and ranked
   - Approval/rejection workflow

2. **GitHub/GitLab Integration**
   - Create PR check with verification report
   - Show hotspots as code comments
   - Block merge until hotspots reviewed
   - One-click approval from dashboard

3. **Review Workflow Engine**
   - Track which hotspots were reviewed
   - Flag new hotspots if agent makes corrections
   - Detect scope creep in re-runs
   - Audit trail of approvals

#### Success Criteria

- Developer can review a 30-minute agent PR in <10 minutes
- Hotspot-first review catches 80%+ of real issues
- Re-review tax measurable and reduced (e.g., 20% → 5%)

---

### Phase 4: Evaluation & Metrics (Week 4-5)

**Goal:** Validate problem and measure product impact.

#### Deliverables

1. **Diary Study (5-10 developers)**
   - Track agent tasks over 1 week
   - Measure: execution time, review time, debugging time, retries
   - Calculate human verification / agent execution ratio
   - Identify pain points and workarounds

2. **Failure Reconstruction Timing Study (15-30 sessions)**
   - Capture real failed coding-agent sessions
   - Give developers normal artifacts (diff, transcript, tests)
   - Measure time to root cause
   - Compare against structured timeline approach

3. **A/B Test: Timeline vs Transcript**
   - Convert one agent session to structured timeline
   - Randomly assign: raw transcript to dev A, timeline to dev B
   - Measure diagnosis accuracy and time
   - Statistical significance on diagnosis success

4. **Hotspot Accuracy Audit**
   - Review flagged hotspots against actual bugs/issues
   - Calculate precision, recall, F1
   - Tune risk-scoring algorithm

#### Success Criteria

- Verification time is measurably reduced vs baseline
- Developers report increased confidence in agent approval
- Hotspot ranking predicts actual review effort
- Plan: pursue customer validation based on results

---

## Technical Architecture

### Stack: NVIDIA-Aligned

```
┌─────────────────────────────────────────────────────────────┐
│  Autonomous Coding Agent                                    │
│  (LangChain ReAct / CrewAI / Claude Code / Cursor / etc)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├─→ [NVIDIA NeMo Agent Toolkit]
                     │     ├─ Orchestration & planning
                     │     ├─ Captures workflow_output.json
                     │     ├─ Intermediate steps + tool calls
                     │     └─ Timing & token usage
                     │
                     ├─→ [OpenShell Runtime]
                     │     ├─ Safe execution boundary
                     │     ├─ Restrict tool access
                     │     └─ Audit trail of actions
                     │
                     ├─→ [W&B Weave / OpenTelemetry]
                     │     ├─ Distributed tracing
                     │     ├─ Full execution trace
                     │     └─ Export for analysis
                     │
                     └─→ [Agent Verification Engine]
                           ├─ Trace normalization
                           ├─ Plan vs actual analysis
                           ├─ Divergence detection
                           ├─ Risk scoring
                           └─ Verification report

                     ↓ OUTPUT ↓

            ✅ Verification Report (JSON)
            ✅ Web Dashboard (Next.js)
            ✅ GitHub/GitLab PR check
            ✅ Approval workflow
```

### Core Components

1. **Trace Ingest**
   - Parse NeMo `workflow_output.json`
   - Parse Weave/OTel traces
   - Parse OpenShell audit logs
   - Normalize to AgentSession model

2. **Verification Engine**
   - Plan vs actual comparison
   - Divergence detection (planned steps not taken, unexpected steps)
   - Scope-creep detection (files modified outside requirement)
   - Risk scoring (based on file type, change size, test coverage)
   - Review hotspot ranking

3. **Report Generator**
   - Requirement adherence summary
   - Divergence points with context
   - File-level change summary
   - Test coverage analysis
   - Risk-ranked hotspots for review

4. **API Server (FastAPI)**
   - `/analyze` — POST session trace, get report
   - `/batch` — process multiple sessions
   - `/export` — send report to Weave/Slack/GitHub
   - `/health` — status check

5. **CLI Tool**
   - `agent-verify analyze <trace.json>`
   - `agent-verify report <trace.json> --format html|json`
   - `agent-verify compare <trace1.json> <trace2.json>` — diff runs

6. **Web Dashboard**
   - Timeline visualization of execution
   - Plan vs actual side-by-side
   - File diff browser with annotations
   - Test results and coverage
   - Hotspot review checklist
   - Approval workflow

7. **Integration Hooks**
   - GitHub/GitLab PR checks
   - Slack notifications
   - Weave dashboard embeds
   - OTel exporters

---

## Milestones & Timeline

### Week 1 (Hackathon Prep)
- ✅ Problem research & validation (DONE)
- ✅ Repo skeleton & architecture (DONE)
- [ ] Phase 1.1: Trace model & verification report
- [ ] Phase 1.2: CLI tool & sample session

### Week 2 (Hackathon Core)
- [ ] Phase 1.3: FastAPI service & test coverage
- [ ] Phase 2.1: NeMo Agent Toolkit integration
- [ ] Phase 2.2: W&B Weave export
- [ ] Demonstrate: end-to-end NeMo → verification report

### Week 3 (Hackathon Final + Evaluation)
- [ ] Phase 2.3: OpenShell integration
- [ ] Phase 3.1: Web dashboard (minimal)
- [ ] Phase 4.1: Diary study setup & initial interviews
- [ ] Demonstrate: dashboard showing hotspots + approval workflow

### Week 4-5 (Post-Hackathon)
- [ ] Phase 4.2: Timing study & A/B test
- [ ] Phase 3.2: GitHub/GitLab integration
- [ ] Phase 4.3: Accuracy audit & tuning
- [ ] Decision: continue → seed round validation

---

## Success Metrics

### Hackathon (Week 2-3)

- ✅ End-to-end pipeline: NeMo → verification report
- ✅ CLI analyzes real agent session (15-60 min run)
- ✅ Report identifies 3+ divergence types
- ✅ Dashboard shows plan vs actual timeline
- ✅ Live demo with NVIDIA judges

### Customer Validation (Week 4+)

- Diary study: verification time / agent execution time < 0.5 (target)
- Timing study: structured timeline diagnosis 30%+ faster
- A/B test: statistical significance on diagnosis accuracy
- Hotspot precision > 80%

### Product Fit (Month 2+)

- 10+ customers using for PR review
- Avg review time per agent PR < 10 minutes
- Hotspot-first review catches 80%+ of actual issues
- Re-review tax reduced by 50%+

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Trace format variability across agent frameworks | Can't normalize traces | Medium | Support NeMo, LangChain, CrewAI explicitly; design extensible ingest layer |
| Developers don't actually use new tool | No product-market fit | Medium | Validate with real agents & developers early; measure time savings empirically |
| GitHub/GitLab integration complexity | Launch delay | Medium | Start with API-only, add integrations in Phase 3+ |
| NVIDIA stack maturity | Dependency risk | Low | NeMo & Weave are stable; OpenShell & Skills are newer but we can degrade gracefully |
| Divergence detection false positives | Low trust in report | Medium | Start conservative; tune on diary study data; allow manual override |
| Re-review tax hard to measure | Can't validate improvement | Low | Instrument actual agent corrections; measure file delta per iteration |

---

## Go-to-Market (Post-Hackathon)

### Positioning

"Coding agents can now generate code faster than developers can confidently understand it. Agent Verification Engine turns long autonomous runs into evidence-backed artifacts so teams can review and approve safely in minutes, not hours."

### Target Customer Segments

1. **Tier 1 (Fastest adoption):**
   - Startups using Claude Code / Cursor daily
   - Teams running 15-60 min agent tasks regularly
   - High velocity, low process friction

2. **Tier 2 (Broader reach):**
   - Enterprise DevOps teams (automation auditing)
   - Financial services (compliance + agent usage audit)
   - Healthcare (safety-critical code review)

3. **Tier 3 (Platform play):**
   - IDE vendors (Cursor, Copilot, etc.)
   - Code review platforms (GitHub, GitLab)
   - Agent platforms (Anthropic, OpenAI)

### Pricing (Future)

- **Free tier:** CLI tool + 10 analyses/month
- **Pro:** $49/month, unlimited analyses + dashboard
- **Enterprise:** custom, includes GitHub/GitLab integration + audit trail

---

## Success Looks Like (Vision)

6 months from now:

- 500+ developers using the CLI or dashboard
- 10+ teams using it for production PR review
- Average agent PR review time: 8 minutes (vs. 25-30 baseline)
- Hotspot-first review prevents 3+ issues per team per month
- NVIDIA uses it as reference implementation for agent verification workflows
- Raised seed round for team expansion

---

## Next Immediate Actions

### This Week (Before Hackathon)

1. **Create Phase 1 sample trace**
   - Real or realistic 30-minute coding agent session
   - File modifications, tool calls, test runs, retries, errors
   - Format: JSON matching AgentSession model

2. **Implement trace parser**
   - Parse sample session
   - Extract plan, actual steps, divergences
   - Output structured VerificationReport

3. **CLI proof of concept**
   - `agent-verify analyze sample-session.json`
   - Terminal output with colored hotspots
   - Show plan vs actual, divergence points, review hotspots

4. **Interview script**
   - Prepare questions from research memo
   - Recruit 3-5 agents users (Discord, Reddit, GitHub)
   - Schedule for week 1 of hackathon

### Hackathon Week

1. **Daily standup:**
   - Phase 1.1, 1.2 complete by day 2
   - Phase 2.1 integration by day 3
   - Dashboard demo by day 4

2. **Live coding sessions:**
   - Show how to run agent → verification report
   - Interview live customer (time permitting)
   - Demo dashboard with real trace

3. **Metrics tracking:**
   - Measure diagnosis time reduction
   - Capture developer feedback
   - Adjust based on feedback

---

## Resources & Dependencies

### Team

- **Lead:** Wilker00 (architecture, core engine)
- **NVIDIA Integration:** TBD (NeMo, Weave, OpenShell liaisons)
- **Interviewer:** TBD (customer discovery)
- **UI/Dashboard:** TBD (if Phase 3 in scope)

### External Dependencies

- NVIDIA NeMo Agent Toolkit (1.0.0+)
- W&B Weave SDK
- OpenTelemetry SDK
- OpenShell runtime
- FastAPI, Pydantic, Uvicorn
- Next.js / React (Phase 3)

### Infrastructure

- GitHub (repo + Actions CI/CD)
- Heroku or similar for demo API (Phase 2+)
- Weave / W&B account for telemetry
- Test agent setup (Claude Code, Cursor, or mock)

---

## Questions & Open Items

1. **NVIDIA Collaboration:** Should we reach out to NeMo team for direct integration support?
2. **Agent Source:** For hackathon demo, which agent should we use? (Claude Code, Cursor, LangChain mock, CrewAI example)
3. **Scope Creep:** Should we include SkillSpector validation in Phase 2, or defer to Phase 3+?
4. **Pricing:** Free-tier sustainability if open-source core?
5. **Competition:** How closely should we follow AgentStepper's trajectory debugger approach vs. diverge?

---

## Appendix: Research References

All claims derived from 2024-2026 published research:

- Dhanorkar et al. (2026): Human oversight of agentic systems in practice
- Huang et al. (2025-2026): Professional Software Developers Don't Vibe, They Control
- Hutter & Pradel (2026): AgentStepper: Interactive Debugging of Software Development Agents
- Chen et al. (2025): Code with Me or for Me?
- Bouzenia & Pradel (2025): Understanding Software Engineering Agents
- Watanabe et al. (2025-2026): On the Use of Agentic Coding
- Zhu et al. (2026): AgentDebugX: Failure Observability in LLM Agents
- Majgaonkar et al. (2025): Understanding Code Agent Behaviour
- Joshi (2026): XAI for Coding Agent Failures

---

**Document Version:** 1.0  
**Last Updated:** Sept 30, 2026  
**Owner:** Wilker00  
**Status:** Active (Hackathon Phase)
