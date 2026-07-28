# Agent Team — Delivery Intelligence & Governed Agent Platform

Thirteen Claude Code subagents that build the Techwave platform end-to-end, coordinated around the product loop: **Detect → Explain → Act → Govern → Learn**. Every agent has an explicit **Guardrails** and **Verification & Validation** section.

| Agent | Role | Model | Primary loop stage |
|-------|------|-------|--------------------|
| `orchestrator` | Plans & sequences the whole team, defines handoffs and gates | opus | all (coordination) |
| `ba` | Requirements, user stories, acceptance criteria | opus | scope |
| `architect` | System design, boundaries, ADRs, interface contracts | opus | all (design) |
| `ux` | UX review against Nielsen/Norman/Gestalt/WCAG & usability laws | opus | Explain / all UI |
| `developer` | Backend: ingest, risk engine, agent runtime, governance, APIs | sonnet | Act / build |
| `frontend` | React/TS UI: dashboard, reveal, approval gate, governance view, report | sonnet | surface |
| `dba` | Schema, migrations, indexing, pgvector, RLS isolation, retention | sonnet | data layer |
| `qa` | Test strategy, verification, regression, demo-path validation | sonnet | verify |
| `analytics` | Risk model, signals, scoring, metrics, agent monitoring | sonnet | Detect / Learn |
| `usage-governor` | Token/cost/context control: budgets, prompt & context efficiency, model right-sizing | sonnet | Govern / Learn |
| `security` | Threat modeling, RBAC, secrets, PII, agent guardrails | opus | Govern |
| `compliance` | SOC 2 / GDPR / HIPAA mapping, audit logging, classification | opus | Govern |
| `devops` | CI/CD, environments, runtime ops, observability, deploy | sonnet | operate |

## Tech stack (agreed)
**Backend:** Python 3.12 + FastAPI · **AI/ML:** Anthropic SDK behind a model-agnostic provider interface + pandas/scikit-learn · **Data:** PostgreSQL (+pgvector) + Redis · **Frontend:** React + TypeScript + Tailwind + shadcn/ui · **Runtime:** Docker (cloud/hybrid/on-prem) · **Tests:** pytest / Vitest / Playwright. No stack changes without an architect ADR.

## How coordination works
Claude Code subagents cannot spawn other subagents. The `orchestrator` produces a dependency-ordered **plan**; the main thread dispatches each specialist in that order. Typical flow:

`ba → architect → (security + compliance review design) → developer → (ux + qa) → devops`, with `analytics` feeding the Detect/Learn workstreams, `ux` reviewing any UI before and after build, and `security`/`compliance` involved *by design* on anything touching agent action, data access, or PII.

## Jira delivery workflow (mandatory)
Full rules: [`docs/JIRA_WORKFLOW.md`](../../docs/JIRA_WORKFLOW.md). Epic: [SCRUM-6](https://hemchandkodali.atlassian.net/browse/SCRUM-6).

```
Backlog → To Do (BA) → In Progress (Dev) → Ready for QA (Dev) → Ready for Security (QA [+UX on UI]) → Ready for Deploy (Sec+Compliance) → Done (DevOps)
```

Fail (QA / Sec / Compliance / UX) → **In Progress** + reassign **Developer**. Until board columns exist, use status + labels `stage-todo` / `stage-dev` / `stage-qa` / `stage-security` / `stage-deploy`. Architect fills **Technical Design**; UX fills **UX Spec** in parallel on UI tickets.

## MCP integrations
Agents inherit MCP tools once servers are connected (definitions leave `tools` unset on purpose).

| Server | Status | Notes |
|--------|--------|--------|
| **GitHub** | Connected | Official remote MCP · repo [`hemchandk3/DeliveryEnterpriseProduct`](https://github.com/hemchandk3/DeliveryEnterpriseProduct) |
| **Jira / Atlassian** | Connected | Official Rovo MCP · site `hemchandkodali.atlassian.net` · project **SCRUM** (`DeliveryEnterprise`) |
| **Figma** | Connected | Design + UX spec source |

> Status: 13 agent definitions present; GitHub + Atlassian + Figma MCP live. Engineering standards in `docs/ENGINEERING_STANDARDS.md`; architecture in `docs/ARCHITECTURE.md`.
