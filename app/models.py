from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


bookmark_tag = Table(
    "bookmark_tag",
    Base.metadata,
    Column(
        "bookmark_id",
        ForeignKey("bookmarks.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
    ),
)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
    )

    tags: Mapped[list["Tag"]] = relationship(
        secondary=bookmark_tag,
        back_populates="bookmarks",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    bookmarks: Mapped[list[Bookmark]] = relationship(
        secondary=bookmark_tag,
        back_populates="tags",
    )