## AI Usage Summary

AI was most useful for quickly structuring the product requirements into planning/design documents, drafting the SQLAlchemy models and FastAPI routes, and building the dashboard from the specified API contract. It also helped review edge cases that happy-path implementation could miss, including the title-fetch/edit race, stale search responses, and duplicate handling after transaction rollback.

AI was least useful when its output was treated as verified without checking the workspace or running the app. At one point, a test suite was discussed as if it existed, but later repository inspection found the expected `tests/test_contract.py` missing and `docs/04-testing.md` empty. Static inspection also cannot establish that a browser flow or database transaction behaves correctly. Generated content therefore needed direct source checking, and unverified claims were corrected to say “pending” or “not run.”

The AI did not determine product scope or independently validate the deliverable. The user supplied the governing constraints and decisions; the human author remains responsible for confirming the final declaration and recording actual run evidence.

## Approximate SDLC Time

No timer or time log was kept. The following are retrospective estimates of active effort based on the recorded work, not measured durations. Testing time represents test planning and environment investigation; it does not imply a completed suite or test run. Waiting time, uncompleted remediation, and demo recording are excluded.

| SDLC phase | Estimated active effort | Included work |
|---|---:|---|
| Planning | 30-45 minutes | Scope, requirements, acceptance criteria, constraints, and risks. |
| Design | 35-55 minutes | SQLite schema, API contract, status mapping, user flow, and open questions. |
| Build | 100-150 minutes | Storage, API, title lookup, dashboard, and implementation corrections. |
| Testing | 20-35 minutes | Test scenarios, isolation approach, and environment investigation; execution unverified. |
| Review | 25-40 minutes | Source-to-contract comparison, findings, and follow-up recommendations. |
| **Estimated total** | **210-325 minutes (3 hours 30 minutes to 5 hours 25 minutes)** | Sum of phase estimates; not an elapsed-time measurement. |

Documentation/reflection time, demo production, and future fixes are not included. There is no manual-only baseline, so no credible AI time-savings percentage can be calculated.

## Rework

AI reduced drafting and implementation setup effort: endpoint/schema scaffolding, repeated documentation structure, and client/API wiring were produced faster than starting from blank files. It also surfaced useful review hypotheses, such as an older title-fetch result overwriting a later edit.

AI-created work also required rework:

- The first duplicate-update error check could compare against a URL restored by rollback. It was revised to preserve the attempted URL and exclude the current bookmark ID.
- The dashboard’s all-bookmarks counter could show a filtered count. A separate total count was introduced.
- A duplicate alert could be obscured by an open modal. Its stacking position was changed and delete errors were moved into the dialog.
- Some earlier completion statements were not supported by repository artifacts or execution. The test file/document absence was recorded rather than claiming success.
- Static review found unresolved races and contract mismatches. They remain follow-up work, not completed fixes.

No numeric estimate of minutes saved or added by AI is supported by timing data. The practical benefit was quicker first drafts; the cost was careful verification and correction of generated assumptions.

## Human Judgment

1. **Maintained the assignment’s local, single-user scope and required stack.** The human kept implementation aligned to FastAPI, SQLite/SQLAlchemy, and the vanilla-JavaScript/Tailwind interface. Without that constraint, the work could have drifted into accounts, cloud sync, or additional technologies that the assignment does not request.
2. **Required explicit deletion protection and visible duplicate feedback.** The human specified a confirmation modal and a red duplicate notice. Without this decision, an AI-generated interface might delete immediately or display a duplicate collision as an indistinguishable generic error.
3. **Required evidence-based reporting instead of accepting assumed verification.** The human requested matrices, troubleshooting, and test evidence, and the review corrected unsupported claims when the expected test artifacts were absent. Without this judgment, the documents could imply tests, screenshots, or runtime checks had passed when none were recorded.

These decisions shaped scope and evidence; they do not mean all implementation choices are settled. In particular, the metadata-fetch policy, exact elapsed-time guarantee, and CDN/anonymization conflict still need resolution.

## What You Would Do Differently

- Start by inventorying the repository, task list, guide, dependency manifest, and available test/runtime tools. Do not rely on conversational claims that a file was created; verify the path and content immediately.
- Ask for the participant guide’s evidence schema at the beginning and use it consistently in each document.
- Define the title-fetch semantics before coding: allowed destinations, redirect policy, size limits, fallback, and whether 3.0 seconds means a wall-clock deadline.
- Implement storage and CRUD first, then add a contract test with a temporary SQLite database before building the UI. Run the tests after each layer and record exact commands/results.
- Add explicit concurrency tests for edits during title lookup and out-of-order search responses before considering those behaviors complete.
- Keep a decision/change log during implementation so actual human corrections and AI-generated changes are not conflated after the fact.
- Produce screenshots and a demo only after a successful local run; never fill evidence placeholders with assumed results.

## Self-Assessment

- **Strongest phase:** Planning and design. The requirements, stack, routes, schema, and unresolved policy questions were made visible in structured artifacts.
- **Weakest phase:** Testing. A test strategy was described, but the expected contract-test file and test execution evidence were absent when reviewed. This is the largest gap between implementation presence and acceptance confidence.
- **Confidence:** Moderate that the code and documents cover the intended functional scope; low that all workflows are correct under real API, browser, persistence, and concurrency conditions. The application should not be described as fully verified until tests and local run evidence exist.

### Demo Video

- **Filename:** `PiyushParashar_3201231-NAGP.mkv` (planned placeholder; file not recorded)
- **Duration:** 6 minutes planned, within the requested 5-8 minute range; actual duration unavailable because no demo was recorded.
- **Reviewer link:** Pending recording and upload to an accessible location. No accessible link is currently available.

### Declaration

**Author confirmation required before submission:** “I confirm that this reflection and the accompanying documentation accurately describe the work completed, the AI assistance used, the human decisions made, and the verification actually performed. Estimated times are identified as estimates, and pending tests/demo evidence are not represented as completed.”
