# Personal Bookmark Manager with Tagging

## Problem Understanding

A local, browser-accessible bookmark manager for saving research and everyday web resources. Organize URLs with tags, search by title or URL, and edit or delete saved entries. Records are stored in SQLite rather than lost when the server stops.

The product scope comes from [the specification](.github/specs/spec.md); technology and engineering boundaries come from [the constitution](.github/specs/constitution.md).

## Requirement Breakdown

- Add a URL with an optional title and tags.
- Attempt page-title retrieval when the title is omitted.
- List saved bookmarks newest first.
- Search titles/URLs and filter by a selected tag, separately or together.
- Edit URL, title, or tags.
- Confirm deletion through the dashboard modal before removing a bookmark.
- Store bookmarks locally across application restarts.
- Show validation feedback, a red duplicate notice, and empty/no-results/error states.

### API

| Method | Path | Behavior | Implemented statuses |
|---|---|---|---|
| GET | `/` | Bookmark dashboard | 200 |
| POST | `/api/bookmarks` | Create with `url`, optional `title`, and `tags` | 201; 400 for invalid input or integrity conflicts |
| GET | `/api/bookmarks` | List; optional `search` and `tag` string queries | 200, including an empty array |
| PUT | `/api/bookmarks/{id}` | Update supplied URL/title/tag fields | 200; 404 for missing ID; 400 for invalid input or integrity conflicts |
| DELETE | `/api/bookmarks/{id}` | Remove an existing bookmark | 200; 404 for missing ID |

Responses for create/list/update include `id`, `url`, `title`, `created_at`, and tag-name strings. The technical plan lists only 200/404 for PUT; its additional implemented 400 handling is documented in [the build record](docs/03-build.md).

## User Stories & Acceptance Criteria

From the dashboard:

1. Select **Add bookmark**, enter a URL, optionally supply a title and comma-separated tags, and save.
2. Use the search field for title/URL matches or select a tag to filter results.
3. Select **Edit** to change a bookmark's details.
4. Select **Delete**, then confirm removal or choose **Keep bookmark** to cancel.

An omitted or empty title initially becomes the URL hostname. A FastAPI background task attempts to retrieve the page's HTML `<title>` and updates the stored title if successful; otherwise the hostname remains. A supplied title does not trigger lookup.

These workflows are implemented in source, but end-to-end acceptance, restart persistence, and browser behavior are not demonstrated by executed tests in the build record.

## Edge Cases

- Empty or structurally malformed URLs return readable HTTP 400 feedback.
- A duplicate stored URL is rejected by the database unique constraint; the dashboard displays a red notice.
- Missing IDs on update/delete return 404.
- Empty collections and unmatched searches/filters return an empty list and corresponding dashboard state.
- Failed title retrieval retains the hostname fallback.
- Duplicate detection uses stored URL equality; URL normalization/equivalence rules are not defined.

## Non-Functional Requirements

### Stack and Storage

- Python 3.11+ and FastAPI.
- SQLite persistence through SQLAlchemy 2.
- HTML5, vanilla JavaScript, and Tailwind CSS single-page dashboard.
- Requests for background title retrieval, configured with `timeout=3.0`.

The database has `bookmarks`, `tags`, and a `bookmark_tag` association table. Bookmark URLs and tag names are unique. Both association foreign keys use `ON DELETE CASCADE`, and SQLite foreign-key enforcement is enabled on connections. See [the schema and design](docs/02-design.md).

### Local Setup

Run the following from the repository root on Windows with Python 3.11+ installed:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirement.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If Python is available through the Windows launcher instead, use `py -3.11 -m venv .venv` for the first command. These commands do not require activating the environment.

Open the dashboard at `http://127.0.0.1:8000/`; FastAPI's interactive API documentation is at `http://127.0.0.1:8000/docs`. Stop the server with `Ctrl+C`. If port 8000 is occupied, choose another `--port` and use that port in the browser URL.

Startup creates tables automatically. The SQLite URL is relative to the process working directory, so start from the same repository root each time to reuse the same database file. Tailwind and fonts load from CDNs; styling/font loading requires internet access even though the application server runs locally.

## Risks, Assumptions & Questions

- Requests' `timeout=3.0` is a connect/read timeout setting, not an absolute three-second elapsed deadline; the plan's strict-timeout wording needs reconciliation.
- Title lookup is a synchronous helper scheduled through FastAPI `BackgroundTasks`, not a separate async scraper module.
- A delayed background lookup can overwrite a later user edit, and overlapping search/filter responses can display stale results. Both are open review findings.
- Metadata fetching has no private-network destination/redirect policy. Keep the server local and do not treat it as hardened for public deployment.
- External corporate CDN references need reconciliation with the constitution's literal corporate-domain prohibition.
- Automated test execution, browser screenshots, and runtime acceptance are not recorded. Workspace error checking alone does not establish correct behavior.

## AI Interactions

AI assistance was used to draft requirements/design documentation, generate storage/API/dashboard code, and identify implementation risks. Human requests set the scope, required stack, deletion safeguard, duplicate-error presentation, and existing endpoint integration.

Source-linked evidence and plan-versus-actual decisions are recorded in [planning](docs/01-planning.md), [design](docs/02-design.md), and [build](docs/03-build.md). Generated code and completion claims require verification against repository artifacts and actual runs, not acceptance based on conversational output alone.

## Planning Outcome

The current deliverable is an implemented, locally runnable prototype with documented verification gaps, not a fully tested release. No authentication, cloud sync, import/export, or multi-user features are included in the stated scope.

### Repository Guide

| File | Purpose |
|---|---|
| [app/database.py](app/database.py) | SQLite engine, sessions, ORM base, and foreign-key enforcement |
| [app/models.py](app/models.py) | Bookmark, tag, and association mappings |
| [app/main.py](app/main.py) | Dashboard serving, CRUD API, and title lookup |
| [app/templates/index.html](app/templates/index.html) | Tailwind/vanilla-JavaScript dashboard |
| [requirement.txt](requirement.txt) | Runtime dependency manifest |
| [docs/01-planning.md](docs/01-planning.md) | Requirements and acceptance criteria |
| [docs/02-design.md](docs/02-design.md) | Schema, API, and user flow |
| [docs/03-build.md](docs/03-build.md) | Implementation decisions and evidence |

Before declaring acceptance, reconcile the open contracts, execute the functional/persistence/security checks, and record actual local-run and screenshot evidence.
