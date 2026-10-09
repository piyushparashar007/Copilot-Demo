## Implementation Plan vs. Actual

| Change | Intended | Built | Deviations and reasons |
|---|---|---|---|
| Storage layer | Persistent local SQLite via SQLAlchemy with bookmarks, tags, and a cascade-enabled junction. | Added `app/database.py` and `app/models.py`; configured SQLite foreign-key enforcement and a timestamp for newest-first listing. | The junction uses the two foreign keys specified by the plan. No unrequested association identifier was added. |
| API and title resolution | Implement the four planned bookmark routes, expected status codes, and metadata title retrieval with a 3.0-second Requests timeout and hostname fallback. | Added `app/main.py`; integrity failures on create/update are rolled back and returned as readable 400 responses. An omitted title starts as the hostname while a FastAPI background task requests and parses the page title. | The task checklist calls for a background async scraper module, but the implementation keeps a synchronous Requests helper in `main.py` and schedules it with FastAPI `BackgroundTasks`; there is no separate scraper module. Requests receives `timeout=3.0`, which is not an absolute wall-clock deadline. The plan does not define update-conflict status; 400 is used for integrity conflicts as explicitly requested. |
| Dashboard | Build a Tailwind and vanilla-JavaScript UI connected to the API with search, tag filters, editing, and deletion protection. | Added `app/templates/index.html` and a `GET /` file response. Search/tag interactions call the list API; the UI adds editor and delete-confirmation modals plus a red duplicate banner. | No template/static serving route existed, so a minimal root route was added. Tailwind and the chosen font load from CDNs because the workspace has no frontend build configuration; those visual assets require network access. |

## Feature Evidence Matrix

Status describes implementation presence only. Workspace static validation passed for the edited source and documentation; API/browser behavior was not executed in this session.

| Requirement | Status | How AI helped | What I changed/decided | How I verified |
|---|---|---|---|---|
| Add Bookmark | Implemented; runtime unverified | Generated the create form and `POST /api/bookmarks` integration for URL, optional title, and tags. | Kept title optional and follows the API's hostname fallback while background title retrieval runs. | Checked the UI request path/body against `BookmarkCreate`; static validation only. |
| Tags | Implemented; runtime unverified | Added comma-separated entry, tag rendering, and API request fields. | Tag filter choices are derived from the unfiltered bookmark list because there is no separate tags endpoint. | Checked response tag shape and `tag` query usage against the API source. |
| List/Newest First | Implemented; runtime unverified | Connected the dashboard list to `GET /api/bookmarks`. | Kept ordering on the server; the UI uses `created_at` only for the displayed date. | Confirmed the endpoint orders by `created_at.desc()`; no database run performed. |
| Filter by Tag | Implemented; runtime unverified | Wired selection chips to the `tag` query parameter. | Filter changes reload results immediately. | Checked query parameter spelling against the API signature. |
| Search | Implemented; runtime unverified | Added title/URL search input and debounced list requests. | Search runs on input with a short debounce to limit request churn. | Checked that the client sends `search` and the API filters title/URL. |
| Edit Bookmark | Implemented; runtime unverified | Added the edit modal and `PUT /api/bookmarks/{id}` request. | Reuses the same form for add and edit to keep fields consistent. | Compared request method/path/body with the update schema; no HTTP test run. |
| Delete | Implemented; runtime unverified | Added a confirmation modal and `DELETE /api/bookmarks/{id}` request. | Requires an explicit confirmation click; cancel leaves the bookmark untouched. | Inspected the cancel/confirm event paths; no browser interaction test run. |
| Persistence | Implemented; runtime unverified | Generated the local SQLAlchemy engine and relational mappings in the prior change. | Uses the specified SQLite database and foreign-key cascade behavior. | Static validation only; persistence across restart was not exercised. |
| Validation | Implemented; runtime unverified | Connected form submission to API validation feedback. | Server rejects empty or clearly malformed URLs with 400; client shows the detail in the form. | Inspected `_validate_url` and request-error handling; no HTTP request test run. |
| Duplicate Handling | Implemented; runtime unverified | Connected unique-integrity 400 details to a dedicated red banner. | The UI identifies duplicate/unique-conflict messages and keeps them visually distinct from ordinary errors. | Checked the API's rollback/400 path and client message matching; not exercised against a live database. |
| Empty/Error States | Implemented; runtime unverified | Added empty-library, no-match, load-error, retry, form-error, and banner states. | Separates an empty collection from filtered no-results and exposes a retry action for load failure. | Inspected render/error branches; no browser screenshot or interaction test was captured. |

## Troubleshooting

1. **The dashboard entry point did not exist.** The template path was absent and source inspection showed `main.py` exposed only API routes. Added `app/templates/index.html` and a `GET /` route using a path relative to `main.py`, avoiding dependence on the process working directory. This was diagnosed by source inspection; runtime confirmation remains pending.
2. **Update duplicate detection could match the row being edited.** Review of the `IntegrityError` path showed that rollback restores the original URL, so checking that value could identify the current bookmark as its own conflict. The implementation now preserves the attempted URL and excludes the current ID when looking for another bookmark with that URL. Static validation passed; this was not exercised against a live database.
3. **A filtered count could misreport the whole collection.** Review showed the All bookmarks badge was updated from filtered results. Added a separate `totalCount` populated from an unfiltered list request. Static validation passed; the rendered behavior remains untested in a browser.
4. **Duplicate failures must not expose database errors.** The create/update handlers roll back `IntegrityError` and return user-readable 400 details; the dashboard recognizes duplicate wording and shows the red banner above open dialogs. The code paths were inspected, not exercised with a live duplicate request.

## Significant Human Changes

- The requested behavior explicitly calls for deletion confirmation, so the dashboard uses a confirmation modal rather than issuing deletion immediately.
- The duplicate case was specified as a red banner; ordinary request failures use a separate error treatment so duplicate feedback remains unmistakable.
- Search and tag changes were directed to update results as the user types or selects a tag; they call the existing query parameters rather than filtering a partial client-side collection.
- The architecture checklist names a separate async scraper module. The implementation currently keeps the title helper in `main.py`; this is recorded as a deviation rather than claimed as a completed module.
- The build record was reshaped to the requested plan-vs-actual comparison, full requirement matrix, troubleshooting, evidence records, and local-run status.
- No local execution or screenshots were available in this session. The documentation marks them pending instead of presenting generated or assumed screenshots as evidence.

## AI Interactions

The Participant Guide referenced by the request was not present in the workspace paths checked. These records use stable evidence IDs and include the request/source, AI contribution, human decision, and verification state so they remain auditable; confirm against the guide's exact Section 7 schema when that guide is available.

### Evidence E-BUILD-01

- **Source / request:** Storage task and technical plan database section.
- **AI contribution:** Produced SQLAlchemy engine/session setup and bookmark/tag/junction mappings with foreign-key cascades.
- **Human decision:** Retained the specified tables and local SQLite persistence; did not add unrelated data entities.
- **Verification:** Static workspace validation reported no errors. Database creation, uniqueness, and cascade behavior were not run.

### Evidence E-BUILD-02

- **Source / request:** Technical plan API section and product acceptance criteria.
- **AI contribution:** Implemented the planned create/list/update/delete endpoints, query filters, and response statuses.
- **Human decision:** Kept the UI client aligned with the existing endpoint names and payload fields rather than introducing alternative routes.
- **Verification:** Source signatures and client calls were cross-checked; no FastAPI TestClient suite was run.

### Evidence E-BUILD-03

- **Source / request:** Technical plan scraper section; request for a bounded background title parser.
- **AI contribution:** Added an HTML title parser scheduled as a FastAPI background task using `requests` with `timeout=3.0` and a hostname fallback.
- **Human decision:** Kept the supplied 3.0-second timeout and fallback behavior; did not add a new scraper endpoint.
- **Verification:** Static source validation passed. Network success, timeout, and connection-failure cases were not run.

### Evidence E-BUILD-04

- **Source / request:** Task 4 and request for a Tailwind/vanilla-JavaScript dashboard wired to FastAPI.
- **AI contribution:** Added the dashboard template, root file-serving route, and client calls to the existing API.
- **Human decision:** Requested an in-app dashboard with search, tag filters, add/edit, empty/error states, and deletion protection; approved adding only the root route needed to serve it.
- **Verification:** Workspace validation reported no errors for the template and route. Browser rendering and endpoint integration were not exercised.

### Evidence E-BUILD-05

- **Source / request:** Explicit interaction requirements for duplicate banners, text search, and immediate tag filtering.
- **AI contribution:** Added the red duplicate notice, debounced search input, and tag-selection reload behavior.
- **Human decision:** Kept duplicate messaging distinct from general errors and retained server-side filtering through `search` and `tag`.
- **Verification:** Client selectors and API parameter names were inspected. No live duplicate, search, or filter requests were run.

### Evidence E-BUILD-06

- **Source / request:** Requested deletion modal and latest build-document structure.
- **AI contribution:** Added a confirmation/cancel flow and reorganized this document around the specified sections and requirement matrix.
- **Human decision:** Required explicit deletion confirmation and asked that all last three changes be recorded together; required honest disclosure of missing run and screenshot evidence.
- **Verification:** Static validation passed for edited documentation. Screenshot capture remains pending a browser session.

## Local Run Evidence

The application was not launched in this editing session, and no browser or screenshot tool was available. Therefore there are no authentic screenshots or live endpoint results to attach. The following is the local procedure to run and verify; it is not a claim that these steps have already succeeded:

1. From the repository root, install the project dependencies, including FastAPI, SQLAlchemy, Requests, and an ASGI server if they are not already installed.
2. Start the app with `uvicorn app.main:app --reload`.
3. Open `http://127.0.0.1:8000/` and verify initial load, create, edit, search, tag filter, confirmed/cancelled deletion, duplicate feedback, and reload persistence.
4. Capture screenshots of the initial dashboard, a populated/filter state, and the delete-confirmation or duplicate-banner state, then add those image paths here.

| Evidence target | Status |
|---|---|
| Dashboard initial-load screenshot | Not captured; requires running app in a browser. |
| Search/tag-filter screenshot | Not captured; requires live data and browser. |
| Delete confirmation or duplicate banner screenshot | Not captured; requires live interaction. |
| API and persistence checks | Not run; workspace validation was static only. |
