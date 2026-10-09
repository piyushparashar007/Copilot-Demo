# Technical Architecture Plan

## 1. Relational Database Topography (SQLite)
- `bookmarks`: id (INTEGER PK), url (TEXT UNIQUE), title (TEXT), created_at (TIMESTAMP)
- `tags`: id (INTEGER PK), name (TEXT UNIQUE)
- `bookmark_tag`: bookmark_id (FK), tag_id (FK) with `ON DELETE CASCADE` mappings

## 2. Interface Invariants (API Specs)
- `POST /api/bookmarks` -> Request: `BookmarkCreate` schema -> Response: `201 Created` / `400 BadRequest`
- `GET /api/bookmarks` -> Queries: `search` (str), `tag` (str) -> Response: `200 OK` Array
- `PUT /api/bookmarks/{id}` -> Path param `id` -> Response: `200 OK` / `404 NotFound`
- `DELETE /api/bookmarks/{id}` -> Path param `id` -> Response: `200 OK` / `404 NotFound`

## 3. Scraper Failure Engineering
The metadata resolution module uses `requests` with a strict 3.0-second timeout. If tripped or connection fails, it falls back gracefully to the raw hostname domain.
