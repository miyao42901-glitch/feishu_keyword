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


class MpSearchResult(Base):
    """公众号文章搜索结果表（feishu_mp_results）。"""

    __tablename__ = "feishu_mp_results"
    __table_args__ = (
        UniqueConstraint("post_id", name="uq_feishu_mp_results_post_id"),
        Index("ix_feishu_mp_results_task_id", "task_id"),
        Index("ix_feishu_mp_results_user_id", "user_id"),
        Index("ix_feishu_mp_results_is_upload", "is_upload"),
        Index("ix_feishu_mp_results_create_time", "create_time"),
        Index("ix_feishu_mp_results_keyword", "keyword"),
        Index(
            "ix_feishu_mp_results_task_upload_ct",
            "task_id",
            "is_upload",
            "create_time",
        ),
        Index(
            "ix_feishu_mp_results_user_upload_id",
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
    company_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    biz: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    avatar_url: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    publish_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
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
