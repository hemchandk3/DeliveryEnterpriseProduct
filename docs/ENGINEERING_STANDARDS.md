# Engineering Standards (mandatory)

These standards apply to every agent and every change on the Techwave Delivery Intelligence & Governed Agent Platform. They are hard rules, not aspirations. The existing per-agent **Guardrails** remain in force in addition to these.

## 1. Live data, production quality
- Features are built and verified against the **real integrations** (GitHub, Jira, Azure DevOps, etc.) — **not mock-only paths**. A feature is not "done" until it has run against the live source.
- No demo shortcuts, stubs, or hardcoded sample values in shipped/runtime code paths.
- **Test fixtures are the one exception:** automated tests may use small committed sample datasets for determinism and speed. Fixtures make tests reliable; they never replace real-data verification of the feature itself.
- **Dependency:** live Jira/Atlassian requires the Atlassian MCP to be OAuth-authorized. Until then, Jira-backed features cannot be marked done — only staged. GitHub and Figma are live.

## 2. Documentation is part of "done"
- The **architect** owns `docs/ARCHITECTURE.md` — the technical design document (components, interface contracts, data flow, ADRs). It is updated **before** implementation for anything that changes the architecture.
- The **developer** and **frontend** engineers update the technical documentation **in the same PR** as the code (API contracts, module/README docs, and the relevant section of `docs/ARCHITECTURE.md`). A PR that changes behavior without updating docs is incomplete.

## 3. Quality gates (Definition of Done — hard merge gates)
No change merges unless all applicable gates pass:

| Gate | Threshold | Owner |
|------|-----------|-------|
| Unit-test coverage | **>= 80%** | developer / frontend, verified by qa |
| Functional tests + code review pass rate | **>= 90%** | qa |
| Security checks | **>= 99%** | security |
| Compliance (applicable SOC 2 / GDPR / HIPAA controls) | **100%** | compliance |

- Below any threshold = **blocked**. qa, security, and compliance each hold a hard gate and must not wave a change through.
- "Pass rate" means: of the defined functional test cases and code-review checks, at least 90% pass with the remainder triaged and accepted by the owner — never silently skipped.

## 4. Communication
- Progress and results are explained to the user in **plain, non-technical language** first; technical detail is available but secondary.

## Governance
Changes to these standards require explicit user approval. Agents cite this file when enforcing a gate.
