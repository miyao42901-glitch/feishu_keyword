from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from social_platform.models.base import Base


class AsyncTask(Base):
    __tablename__ = "feishu_async_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    action: Mapped[str] = mapped_column(String(128), default="", index=True)
    body_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    create_time: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.utcnow())
    update_time: Mapped[dt.datetime] = mapped_column(
        DateTime,
        default=lambda: dt.datetime.utcnow(),
        onupdate=lambda: dt.datetime.utcnow(),
    )
