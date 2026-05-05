from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.storage import Base


class AppInfo(Base):
    """ORM model storing detailed information about a single RuStore app."""

    __tablename__ = 'app_info'

    app_id: Mapped[str] = mapped_column(String, primary_key=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    ratings_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    downloads: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size: Mapped[str | None] = mapped_column(String, nullable=True)
    age: Mapped[str | None] = mapped_column(String, nullable=True)

    developer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    developer_url: Mapped[str | None] = mapped_column(String, nullable=True)

    support_email: Mapped[str | None] = mapped_column(String, nullable=True)
    support_vk: Mapped[str | None] = mapped_column(String, nullable=True)
    support_website: Mapped[str | None] = mapped_column(String, nullable=True)

    min_android_version: Mapped[str | None] = mapped_column(String, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshots: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    requested_data: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    last_version: Mapped[str | None] = mapped_column(String, nullable=True)
    last_update_date: Mapped[str | None] = mapped_column(String, nullable=True)
    last_update_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
