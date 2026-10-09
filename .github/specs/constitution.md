# Repository Constitution

## 1. Core Engineering Directives
- **Spec Over Code**: Code is a transient artifact of this specification. If the implementation conflicts with the specification files, the code is incorrect.
- **Zero Vibe Coding**: No routes, parsing logic, or fields may be implemented based on intuition. Every line must map to an item in `tasks.md`.
- **Anonymization Invariant**: Zero real-world PII (names, corporate domains, tokens) is permitted in code, test files, or logs.

## 2. Technical Stack Boundaries
- **Backend Architecture**: Python 3.11+ using FastAPI.
- **Persistence Tier**: Local SQLite engine using SQLAlchemy.
- **Client Presentation**: Single-Page Interface using HTML5, Vanilla JS, and Tailwind CSS.
