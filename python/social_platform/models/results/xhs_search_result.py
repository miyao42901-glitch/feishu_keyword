from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from social_platform.models.base import Base


class XhsSearchResult(Base):
    """与 `schema.sql` 中 `feishu_xhs_results` 一致（含 `xsec_token VARCHAR(64)`）。"""

    __tablename__ = "feishu_xhs_results"
    __table_args__ = (
        UniqueConstraint("post_id", name="uq_feishu_xhs_results_post_id"),
        Index("ix_feishu_xhs_results_task_id", "task_id"),
        Index("ix_feishu_xhs_results_user_id", "user_id"),
        Index("ix_feishu_xhs_results_is_upload", "is_upload"),
        Index("ix_feishu_xhs_results_create_time", "create_time"),
        Index("ix_feishu_xhs_results_keyword", "keyword"),
        Index(
            "ix_feishu_xhs_results_task_upload_ct",
            "task_id",
            "is_upload",
            "create_time",
        ),
        Index(
            "ix_feishu_xhs_results_user_upload_id",
            "user_id",
            "is_upload",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("feishu_async_tasks.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    post_id: Mapped[str] = mapped_column(String(64), nullable=False)
    keyword: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    nickname: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    sec_uid: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    content_type: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    is_upload: Mapped[int] = mapped_column(
        TINYINT(1), nullable=False, server_default="0"
    )
    create_time: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    update_time: Mapped[dt.datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    page_url: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    xsec_token: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    avatar_url: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    author_signature: Mapped[str] = mapped_column(
        String(256), nullable=False, default=""
    )
    verify_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    cover_url: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_music: Mapped[int] = mapped_column(
        TINYINT(1), nullable=False, server_default="0"
    )
    publish_time_ms: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    collect_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    primary_image_url: Mapped[str] = mapped_column(
        String(256), nullable=False, default=""
    )
    primary_video_url: Mapped[str] = mapped_column(
        String(256), nullable=False, default=""
    )
