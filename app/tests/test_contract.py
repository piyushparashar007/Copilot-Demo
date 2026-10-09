from contextlib import contextmanager
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import import_module
from pathlib import Path
from threading import Event, Thread
from time import monotonic

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select, func
from sqlalchemy.orm import sessionmaker

from app.database import Base, enable_sqlite_foreign_keys
from app.models import Bookmark, Tag, bookmark_tag
from sqlalchemy import event


main = import_module("app.main")


@pytest.fixture
def storage(tmp_path, monkeypatch):
    database_file = tmp_path / "contract.sqlite3"
    engine = create_engine(
        f"sqlite:///{database_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", enable_sqlite_foreign_keys)
    sessions = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SessionLocal", sessions)
    try:
        yield engine, sessions, database_file
    finally:
        engine.dispose()


@pytest.fixture
def client(storage):
    with TestClient(main.app) as test_client:
        yield test_client


@contextmanager
def local_page(mode="title"):
    release = Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if mode == "slow":
                release.wait(5)
            body = (
                b"<html><title> Local &amp; Research </title></html>"
                if mode == "title" else b"<html><body>No title</body></html>"
            )
            self.send_response(503 if mode == "error" else 200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, format_string, *arguments):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/page"
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def add(client, path="item", title="Research item", tags=None):
    response = client.post("/api/bookmarks", json={
        "url": f"https://source.invalid/{path}",
        "title": title,
        "tags": tags or [],
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Your bookmarks" in response.text


def test_add_tags_search_and_filter(client):
    first = add(client, "alpha", "Alpha research", ["research", "research", "reading"])
    add(client, "beta", "Beta notes", ["reading"])
    assert set(first["tags"]) == {"research", "reading"}
    for parameters in ({"search": "ALPHA"}, {"search": "/alpha"},
                       {"tag": "research"}, {"tag": "research", "search": "alpha"}):
        response = client.get("/api/bookmarks", params=parameters)
        assert response.status_code == 200
        assert [item["id"] for item in response.json()] == [first["id"]]


def test_newest_first(client, storage):
    older = add(client, "older")
    newer = add(client, "newer")
    with storage[1]() as db:
        db.get(Bookmark, older["id"]).created_at = datetime(2020, 1, 1)
        db.get(Bookmark, newer["id"]).created_at = datetime(2021, 1, 1)
        db.commit()
    assert [item["id"] for item in client.get("/api/bookmarks").json()] == [newer["id"], older["id"]]


def test_edit_and_delete(client):
    saved = add(client, tags=["old"])
    response = client.put(f"/api/bookmarks/{saved['id']}", json={
        "url": "https://source.invalid/edited", "title": "Edited", "tags": ["new"],
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Edited"
    assert response.json()["url"] == "https://source.invalid/edited"
    assert response.json()["tags"] == ["new"]
    assert client.delete(f"/api/bookmarks/{saved['id']}").status_code == 200
    assert client.get("/api/bookmarks").json() == []


@pytest.mark.parametrize("url", ["", "   ", "not a URL", "http://[", "http://source.invalid:bad"])
def test_invalid_url(client, url):
    response = client.post("/api/bookmarks", json={"url": url, "title": "Invalid"})
    assert response.status_code == 400
    assert client.get("/api/bookmarks").json() == []


def test_invalid_body(client):
    assert client.post("/api/bookmarks", json={"tags": [42]}).status_code == 400
    assert client.get("/api/bookmarks").json() == []


def test_duplicate_create_and_update_rollback(client):
    first = add(client, "first")
    second = add(client, "second")
    duplicate = client.post("/api/bookmarks", json={"url": first["url"], "title": "Duplicate"})
    collision = client.put(f"/api/bookmarks/{first['id']}", json={"url": second["url"], "title": "Discard"})
    for response in (duplicate, collision):
        assert response.status_code == 400
        assert response.json()["detail"] == "A bookmark with this URL already exists."
    remaining = {item["id"]: item for item in client.get("/api/bookmarks").json()}
    assert remaining[first["id"]]["url"] == first["url"]
    assert remaining[first["id"]]["title"] == first["title"]
    assert len(remaining) == 2


def test_missing_and_empty(client):
    for params in ({}, {"search": "missing"}, {"tag": "missing"}):
        response = client.get("/api/bookmarks", params=params)
        assert response.status_code == 200
        assert response.json() == []
    assert client.put("/api/bookmarks/999", json={"title": "Missing"}).status_code == 404
    assert client.delete("/api/bookmarks/999").status_code == 404


@pytest.mark.parametrize("parent", ["bookmark", "tag"])
def test_database_cascade(client, storage, parent):
    saved = add(client, tags=["cascade"])
    with storage[1]() as db:
        assert db.scalar(select(func.count()).select_from(bookmark_tag)) == 1
        db.execute(delete(Bookmark).where(Bookmark.id == saved["id"]) if parent == "bookmark" else delete(Tag))
        db.commit()
        assert db.scalar(select(func.count()).select_from(bookmark_tag)) == 0


def test_persistence_after_engine_reopen(client, storage):
    saved = add(client, "durable")
    reopened = create_engine(f"sqlite:///{storage[2].as_posix()}")
    try:
        with reopened.connect() as connection:
            assert connection.execute(select(Bookmark.url).where(Bookmark.id == saved["id"])).scalar_one() == saved["url"]
    finally:
        reopened.dispose()


@pytest.mark.parametrize("mode", ["title", "missing", "error", "slow"])
def test_background_title_and_fallback(client, mode):
    with local_page(mode) as url:
        started = monotonic()
        response = client.post("/api/bookmarks", json={"url": url})
        elapsed = monotonic() - started
    assert response.status_code == 201
    expected = "Local & Research" if mode == "title" else "127.0.0.1"
    assert client.get("/api/bookmarks").json()[0]["title"] == expected
    assert main.REQUEST_TIMEOUT_SECONDS == 3.0
    if mode == "slow":
        assert 2.5 <= elapsed < 4.8


def test_untrusted_input_is_data_not_sql(client):
    payload = "<script>alert('synthetic')</script>"
    saved = add(client, "untrusted", payload, ["'; DROP TABLE bookmarks; --"])
    assert saved["title"] == payload
    assert client.get("/api/bookmarks", params={"search": "' OR 1=1 --"}).json() == []
    assert len(client.get("/api/bookmarks").json()) == 1
    template = (Path(main.__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
    assert "escapeHtml(title)" in template
    assert "escapeHtml(tag)" in template
    assert "notice.textContent = message" in template