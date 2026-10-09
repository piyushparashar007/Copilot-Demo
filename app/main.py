from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextlib import asynccontextmanager
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import requests
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Bookmark, Tag


REQUEST_TIMEOUT_SECONDS = 3.0


class BookmarkCreate(BaseModel):
    url: str
    title: str | None = None
    tags: list[str] = Field(default_factory=list)


class BookmarkUpdate(BaseModel):
    url: str | None = None
    title: str | None = None
    tags: list[str] | None = None


class BookmarkResponse(BaseModel):
    id: int
    url: str
    title: str | None
    created_at: datetime
    tags: list[str]


class _PageTitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._inside_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self._parts.append(data)

    @property
    def title(self) -> str | None:
        value = " ".join("".join(self._parts).split())
        return value or None


def _validate_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid URL.",
        ) from error

    if not url.strip() or not parsed.scheme or not parsed.netloc or not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid URL.",
        )

    return hostname


def _get_or_create_tags(db: Session, names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for name in dict.fromkeys(names):
        tag = db.query(Tag).filter(Tag.name == name).one_or_none()
        if tag is None:
            tag = Tag(name=name)
        tags.append(tag)
    return tags


def _response(bookmark: Bookmark) -> BookmarkResponse:
    return BookmarkResponse(
        id=bookmark.id,
        url=bookmark.url,
        title=bookmark.title,
        created_at=bookmark.created_at,
        tags=[tag.name for tag in bookmark.tags],
    )


def _integrity_error_detail(
    db: Session,
    url: str,
    exclude_bookmark_id: int | None = None,
) -> str:
    db.rollback()
    duplicate_query = db.query(Bookmark.id).filter(Bookmark.url == url)
    if exclude_bookmark_id is not None:
        duplicate_query = duplicate_query.filter(Bookmark.id != exclude_bookmark_id)
    if duplicate_query.first() is not None:
        return "A bookmark with this URL already exists."
    return "The bookmark conflicts with an existing unique value."


def _fetch_page_title_now(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        parser = _PageTitleParser()
        parser.feed(response.text)
        return parser.title
    except (requests.RequestException, ValueError, UnicodeError):
        return None


def _fetch_page_title(url: str) -> str | None:
    # requests' timeout only bounds connect/read gaps, not total elapsed time,
    # so enforce the specified 3.0-second deadline as a hard wall-clock cap.
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_fetch_page_title_now, url)
        try:
            return future.result(timeout=REQUEST_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            return None


def _resolve_title_in_background(bookmark_id: int, url: str, fallback_title: str) -> None:
    title = _fetch_page_title(url)
    if title is None:
        return

    with SessionLocal() as db:
        try:
            bookmark = db.get(Bookmark, bookmark_id)
            # Only apply the fetched title if the bookmark still has the same
            # URL and untouched fallback title; otherwise the user already
            # edited it while the lookup was in flight, so discard this result.
            if (
                bookmark is not None
                and bookmark.url == url
                and bookmark.title == fallback_title
            ):
                bookmark.title = title
                db.commit()
        except SQLAlchemyError:
            db.rollback()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
INDEX_FILE = Path(__file__).parent / "templates" / "index.html"


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.exception_handler(RequestValidationError)
async def invalid_request_handler(_request: Request, _error: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "The request data is invalid."},
    )


@app.post(
    "/api/bookmarks",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bookmark(
    payload: BookmarkCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> BookmarkResponse:
    hostname = _validate_url(payload.url)
    title = payload.title if payload.title else hostname
    bookmark = Bookmark(
        url=payload.url,
        title=title,
        tags=_get_or_create_tags(db, payload.tags),
    )
    db.add(bookmark)

    try:
        db.commit()
        db.refresh(bookmark)
    except IntegrityError as error:
        detail = _integrity_error_detail(db, payload.url)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        ) from error

    if not payload.title:
        background_tasks.add_task(
            _resolve_title_in_background, bookmark.id, bookmark.url, title
        )

    return _response(bookmark)


@app.get("/api/bookmarks", response_model=list[BookmarkResponse])
def list_bookmarks(
    search: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[BookmarkResponse]:
    query = db.query(Bookmark)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(Bookmark.title.ilike(pattern), Bookmark.url.ilike(pattern))
        )
    if tag:
        query = query.filter(Bookmark.tags.any(Tag.name == tag))

    bookmarks = query.order_by(Bookmark.created_at.desc()).all()
    return [_response(bookmark) for bookmark in bookmarks]


@app.put("/api/bookmarks/{id}", response_model=BookmarkResponse)
def update_bookmark(
    id: int,
    payload: BookmarkUpdate,
    db: Session = Depends(get_db),
) -> BookmarkResponse:
    bookmark = db.get(Bookmark, id)
    if bookmark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found.",
        )

    changes = payload.model_dump(exclude_unset=True)
    if "url" in changes and changes["url"] is not None:
        _validate_url(changes["url"])
        bookmark.url = changes["url"]
    if "title" in changes:
        bookmark.title = changes["title"]
    if changes.get("tags") is not None:
        bookmark.tags = _get_or_create_tags(db, changes["tags"])

    attempted_url = bookmark.url
    try:
        db.commit()
        db.refresh(bookmark)
    except IntegrityError as error:
        detail = _integrity_error_detail(
            db,
            attempted_url,
            exclude_bookmark_id=id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        ) from error

    return _response(bookmark)


@app.delete("/api/bookmarks/{id}")
def delete_bookmark(id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    bookmark = db.get(Bookmark, id)
    if bookmark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found.",
        )

    db.delete(bookmark)
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The bookmark could not be deleted.",
        ) from error
    return {"detail": "Bookmark deleted."}