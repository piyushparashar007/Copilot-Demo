## Problem Understanding

Review date: 2026-10-02. Recommendation: **do not mark the assignment fully verified yet**. The core bookmark workflows are present in source, but there are correctness risks and missing test evidence.

This review compares [the product specification](../.github/specs/spec.md), [constitution](../.github/specs/constitution.md), [technical plan](../.github/specs/plan.md), and [task checklist](../.github/specs/tasks.md) with the implemented API, storage models, dashboard, and dependency manifest. It is a static review, not a runtime acceptance test. No application code was changed during this review.

Prioritized findings:

1. **High - background title lookup can overwrite an edit.** In [app/main.py](../app/main.py), `_resolve_title_in_background` finds a bookmark by ID and replaces its title without verifying the current URL or title. If the user edits either while the original lookup is running, the old lookup can overwrite the new title or assign a title from the previous URL. Use an atomic conditional update tied to the original URL and expected fallback title, and test an edit during a delayed fetch.
2. **High - metadata fetching can reach unintended network destinations.** `_validate_url` checks structural components but does not establish an HTTP/HTTPS allowlist or reject private/local destinations; `_fetch_page_title` follows Requests' default redirect behavior. A submitted URL can therefore trigger a server-side request to internal services. Local-only usage limits exposure but does not remove this risk. Approve a fetch policy in the specification/tasks before implementation; verify initial destinations and redirects. This is a security risk, not an assertion that the original specification already defines a specific network-blocking policy.
3. **High - verification completion is unsupported by repository artifacts.** Task 5 is checked complete, but the requested contract test file could not be found and [docs/04-testing.md](04-testing.md) is empty. Earlier conversational claims of a written suite are not proof of implementation or execution. Add the suite, record real results, and reconcile the checklist; no passing-test count can be reported now.
4. **Medium - the strict 3.0-second timeout contract is not enforced as an elapsed deadline.** `_fetch_page_title` calls `requests.get(..., timeout=3.0)`, which sets connect/read timeout behavior rather than a total elapsed-time cap. Redirects, DNS, and a response that continues delivering data can exceed three seconds; `response.text` also reads the entire response without a size limit. Reconcile the intended timeout meaning with the plan and verify slow/streaming responses before claiming compliance.
5. **Medium - old search/filter responses can replace newer results.** In [app/templates/index.html](../app/templates/index.html), multiple `loadBookmarks` requests can overlap, and every completed response writes shared state. A delayed older search may overwrite a newer search/tag selection. Use request cancellation or an increasing request identifier, then test out-of-order responses.
6. **Medium - graceful error handling does not cover general database failures.** Create/update catch `IntegrityError`; delete commits without a corresponding friendly database-error response. A locked, unwritable, or unavailable database can produce a server error. Add approved rollback/error handling and failure-path tests; do not return success after a failed commit.

## Requirement Breakdown

Status means implementation found in source, not an acceptance-test pass.

| Requirement | Implementation evidence | Review assessment |
|---|---|---|
| Add Bookmark | `BookmarkCreate`, POST endpoint, dashboard form; blank title starts as hostname and schedules lookup. | Present; title-edit race and fetch safety require follow-up. |
| Tags | `Tag`, `bookmark_tag`, tag-name lists in payloads/responses. | Present; filter list retains previously seen tags after their last bookmark is removed. |
| List/Newest First | GET query orders by `created_at.desc()`. | Present; SQLite timestamps may tie within the same second, with no explicit tie-breaker. |
| Filter by Tag | GET `tag` query uses the bookmark/tag relationship; UI submits selected tags. | Present; overlapping requests can display stale results. |
| Search | GET uses title/URL `ilike`; UI sends `search`. | Present; `%` and `_` act as SQL LIKE wildcards, and literal-match behavior is unspecified. |
| Edit | PUT changes URL, title, and tags and returns 404 for absent IDs. | Present; background lookup can undo title edits. |
| Delete | DELETE endpoint, confirmation/cancel modal, foreign-key cascade configuration. | Present; runtime confirmation and cascade tests are missing. |
| Persistence | File-backed SQLite engine, committed changes, startup table creation. | Present; restart durability has not been demonstrated. |
| Validation | URL structural checks, Pydantic schemas, request-validation handler returning 400. | Partial assurance; accepted schemes and explicit null URL updates need a documented policy. |
| Duplicate Handling | Unique stored URL/tag name; integrity rollback and readable 400. | Present for exact stored URL equality; URL normalization is not defined. |
| Empty/Error States | Empty/no-match views, load retry, form/delete errors, duplicate notice. | Present; metadata failure uses fallback without a separate failure indicator, and general database errors remain unhandled. |

Architecture checks:

- [app/database.py](../app/database.py) uses SQLAlchemy with local SQLite and enables `PRAGMA foreign_keys=ON` on connections.
- [app/models.py](../app/models.py) contains the planned bookmark columns, unique tag names, and both junction foreign keys with `ON DELETE CASCADE`. The plan does not specify a junction primary key, so its absence is not itself a contract violation.
- The backend is FastAPI and the client is HTML5, vanilla JavaScript, and Tailwind. [requirement.txt](../requirement.txt) lists the runtime packages, including SQLAlchemy 2 and Pydantic 2 compatible ranges; installation was not performed during this review.
- Task 3 calls for a background async scraper module. The actual implementation is a synchronous Requests helper inside the API module, scheduled by FastAPI `BackgroundTasks`. Record this distinction instead of claiming a separate async module exists.

## User Stories & Acceptance Criteria

The following acceptance checks remain to be executed:

- Save a valid URL with a supplied title and multiple tags; confirm 201 and the stored values.
- Save without a title against a controlled page; confirm successful title retrieval or hostname fallback. Delay retrieval and edit the bookmark to verify the edit is preserved.
- List bookmarks with distinct creation times and verify newest-first order; separately check equal timestamps.
- Search by title and URL, filter by a selected tag, combine both queries, and verify an empty array for no matches.
- Edit URL/title/tags; verify absent IDs return 404 and a conflicting URL returns a friendly 400 without changing either stored record.
- Cancel deletion and verify no request removes the record; confirm deletion and verify the bookmark/junction rows disappear.
- Restart the application against the same database file and verify bookmarks remain.
- Submit empty/malformed URLs and duplicate URLs; verify 400, understandable feedback, and no unintended additional records.
- Exercise empty-library, no-results, fetch failure, and failed mutation states in the browser.

These checks should use synthetic data and controlled local test fixtures, not personal bookmarks, corporate domains, or tokens.

## Edge Cases

- **Fetch/edit race:** a title lookup completes after the user changes the URL or supplies a new title.
- **Out-of-order requests:** two search/tag requests return in reverse order; only the latest should affect the displayed results.
- **Deleted record during lookup:** the current helper checks whether the bookmark still exists, so the missing-row branch is present; verify it does not recreate a deleted record.
- **Stale tags:** `collectTags` merges names into existing state rather than rebuilding from the current collection. Tags may remain selectable after all their bookmarks are deleted; this is a usability issue, with tag lifecycle policy still unspecified.
- **Unexpected schemes/redirects:** structurally accepted input can have a non-web scheme or lead to an internal destination. Validate rendering and metadata-fetch behavior separately.
- **Database location:** `sqlite:///./bookmarks.db` is relative to the process working directory. Starting from another directory can open a different file and appear to lose data.
- **Untrusted title/tag text:** the dashboard escapes interpolated text and uses `textContent` for notices. These are useful safeguards, but only a browser test can verify the complete rendering path.
- **Explicit null update:** `{"url": null}` is accepted by the update schema and ignored by the route. Decide whether this is intentional instead of assuming it is invalidated.

## Non-Functional Requirements

| Target | Source-review evidence | Remaining check |
|---|---|---|
| Required technology stack | Python/FastAPI API, SQLite/SQLAlchemy models, Tailwind/vanilla-JS client; compatible dependency ranges. | Install dependencies and run under Python 3.11+. |
| Local browser access | GET `/` serves the template; API paths use the same origin. | Launch locally and exercise the browser workflow. Tailwind/fonts currently require CDN network access; fully offline styling is not promised by the spec. |
| Durable storage | SQLite file and commits exist. | Restart using the same file and verify retained records. |
| Graceful feedback | Expected 400/404 responses and dashboard error states exist. | Test database failure, metadata failure, and modal error behavior. |
| Strict metadata timeout | Requests receives 3.0 seconds. | Resolve the elapsed-deadline mismatch and measure controlled slow responses. |
| Anonymization invariant | Reviewed files contain no observed personal names or secret tokens. The template includes Google Fonts/Tailwind corporate CDN hostnames. | The literal corporate-domain prohibition conflicts with those source URLs; reconcile the constitution or replace external references with approved local assets. No full log/history scan was possible. |
| Specification/task traceability | Broad tasks exist for storage, API, scraper, UI, and tests. | Checked boxes do not establish line-level traceability or test completion. Record parsing/status choices and correct unsupported completion claims. |

The agreements define no numeric general performance, browser-support, or accessibility-conformance targets. This review does not invent them. Keyboard focus containment/restoration in dialogs and mobile layout verification remain useful usability checks, not claimed conformance certifications.

## Risks, Assumptions & Questions

- Review scope covered the four known app implementation files, runtime manifest, governing spec/plan/constitution/tasks, target review file, and testing-document state. A repository-wide file inventory, logs, and history were not available; this is not an exhaustive secret/PII audit.
- No executable test runner, shell, or browser tool was available for this review. Findings are grounded in control flow and source, not reproduced runtime traces.
- The contract test path was absent on direct inspection. This does not prove that no tests exist at another path, but the requested suite is not available at its expected location.
- Is the 3.0-second requirement a total deadline or Requests' connect/read timeout setting? Resolve this before approving title-fetch behavior.
- Should unsafe/non-HTTP schemes and private-network metadata targets be rejected? Any policy and implementation must be authorized in the spec/task breakdown.
- Should invalid edit URLs return 400 in the architecture plan as well as in code? PUT currently supports 400 conflicts although the plan lists only 200/404.
- Should CSS/fonts be fully local, or should the corporate-CDN references be explicitly exempted from the anonymization invariant?
- No repairs are included in this document-only change. Recommendations require approved tasks and focused retesting.

## AI Interactions

### Evidence E-REVIEW-01

- **Source:** Specification, architecture plan, API source, and dashboard event handlers.
- **AI contribution:** Compared all eleven functional requirements to their API/storage/client implementation and identified title-update and stale-response races.
- **Decision:** Report code presence separately from verified acceptance; recommend guarded updates and latest-request protection without changing implementation during review.
- **Verification:** Static source inspection only. Race reproduction tests remain pending.

### Evidence E-REVIEW-02

- **Source:** Architecture timeout contract, `_fetch_page_title`, URL validation, and external asset references.
- **AI contribution:** Identified that Requests' timeout is not a total deadline, metadata requests lack a destination policy, and corporate CDN references conflict with the literal constitution wording.
- **Decision:** Treat the strict-timeout mismatch as a contract concern and network-fetch protection as a security recommendation needing an approved policy.
- **Verification:** Inspected source/configuration; no network timing, redirect, or browser security tests were run.

### Evidence E-REVIEW-03

- **Source:** Task checklist, empty testing document, and failed read of the expected contract-test path.
- **AI contribution:** Flagged the discrepancy between a checked test task and missing test artifacts/evidence.
- **Decision:** Do not invent passing results or accept conversational completion claims as repository evidence.
- **Verification:** Direct file inspection confirmed the empty testing document and unavailable requested test path; test execution remains pending.

## Planning Outcome

The app is an implemented but unverified prototype, not a demonstrated complete submission. Preserve the existing core scope; do not add accounts, synchronization, import/export, or unrelated features.

Recommended next steps, in order:

1. Restore the requested automated contract suite and populate the testing document with real results; align Task 5 with actual evidence.
2. Authorize and repair background-title edit protection and metadata fetch/deadline policy, then run focused regression/security tests.
3. Prevent stale dashboard responses, exercise friendly database-failure handling, and resolve timestamp/tag lifecycle decisions as necessary.
4. Reconcile CDN references with the anonymization boundary and the scraper/API plan deviations.
5. Run all eleven acceptance workflows, restart-persistence and cascade checks, and desktop/mobile browser verification; capture genuine screenshots.

Release/assignment acceptance remains pending those checks. Static document validation does not establish that the application passes its contracts.
