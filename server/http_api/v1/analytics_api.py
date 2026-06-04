"""API v1：埋点事件上报。"""

from __future__ import annotations

from typing import Annotated, Generator, Optional

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from http_api.rate_limit import ip_rate_limit
from social_platform.api_response import respond_err, respond_ok
from social_platform.api_status_codes import CODE_BAD_REQUEST, CODE_SERVICE_UNAVAILABLE, get_message
from social_platform.schemas.analytics_events import AnalyticsEventsRequest
from social_platform.schemas.analytics_events import ALLOWED_ANALYTICS_EVENTS
from social_platform.services import analytics_service, task_service

ANALYTICS_INGEST = "analytics_ingest"


def get_db() -> Generator[Optional[Session], None, None]:
    if not task_service.database_configured():
        yield None
        return
    from social_platform.database.session import get_session_factory

    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def _require_db(db: Optional[Session]) -> Session:
    if db is None:
        raise RuntimeError("database unavailable")
    return db


def build_analytics_router() -> APIRouter:
    r = APIRouter(prefix="/analytics", tags=["v1-analytics"])

    @r.post(
        "/events",
        dependencies=[
            ip_rate_limit(max_requests=120, window_seconds=60, scope=ANALYTICS_INGEST),
        ],
    )
    def ingest_analytics_events(
        body: AnalyticsEventsRequest,
        db: Annotated[Optional[Session], Depends(get_db)],
        x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
        x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    ) -> JSONResponse:
        if db is None:
            return respond_err(
                CODE_SERVICE_UNAVAILABLE,
                "异步任务未配置：请设置环境变量 DATABASE_URL",
                http_status=503,
            )

        header_user = (x_user_id or "").strip()
        events_payload: list[dict] = []
        for ev in body.events:
            name = ev.event.strip()
            if name not in ALLOWED_ANALYTICS_EVENTS:
                continue
            props = dict(ev.properties or {})
            uid = (ev.user_id or props.get("user_id") or header_user or "").strip() or None
            if x_api_key and x_api_key.strip():
                props.setdefault("api_key_present", True)
            events_payload.append(
                {
                    "event": name,
                    "user_id": uid,
                    "ts": ev.ts,
                    "properties": props,
                }
            )

        if not events_payload:
            return respond_err(
                CODE_BAD_REQUEST,
                get_message(CODE_BAD_REQUEST),
                data={"hint": "no valid events"},
                http_status=400,
            )

        try:
            accepted = analytics_service.ingest_events(_require_db(db), events_payload)
        except Exception:
            db.rollback()
            raise

        return respond_ok({"accepted": accepted, "received": len(body.events)})

    return r
