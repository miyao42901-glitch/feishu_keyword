"""Celery broker 环境变量来源诊断（.env / 进程 / Windows User|Machine）。"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from social_platform.env_bootstrap import ensure_dotenv_loaded

_DOTENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")
_PY_ROOT = Path(__file__).resolve().parent.parent
_DOTENV_PATH = _PY_ROOT / ".env"


def _strip_dotenv_value(raw: str) -> str:
    s = raw.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    if " #" in s:
        s = s.split(" #", 1)[0].strip()
    return s


def read_dotenv_value(key: str) -> Optional[str]:
    """读取 python/.env 文件中的键（不修改 os.environ）。"""
    if not _DOTENV_PATH.is_file():
        return None
    try:
        text = _DOTENV_PATH.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _DOTENV_LINE.match(line)
        if not m or m.group(1) != key:
            continue
        val = _strip_dotenv_value(m.group(2))
        return val if val else None
    return None


def _windows_env_var(name: str, scope: str) -> Optional[str]:
    if sys.platform != "win32":
        return None
    try:
        cp = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"[Environment]::GetEnvironmentVariable('{name}','{scope}')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode != 0:
        return None
    val = (cp.stdout or "").strip()
    return val or None


def _warn_amqp_source(logger: logging.Logger, source: str, value: str) -> None:
    if "amqp://" in value or "amqps://" in value:
        logger.error(
            "检测到 RabbitMQ broker 配置 source=%s value=%s；"
            "请删除该环境变量或改为 redis://（Windows 系统变量会覆盖 .env，因 load_dotenv(override=False)）",
            source,
            value,
        )


def log_celery_broker_env(logger: logging.Logger) -> None:
    """启动时打印 broker 相关环境来源，便于排查系统变量覆盖 .env。"""
    ensure_dotenv_loaded()

    logger.warning("ENV CELERY_BROKER_URL=%s", os.environ.get("CELERY_BROKER_URL"))
    logger.warning("ENV CELERY_RESULT_BACKEND=%s", os.environ.get("CELERY_RESULT_BACKEND"))

    file_broker = read_dotenv_value("CELERY_BROKER_URL")
    file_backend = read_dotenv_value("CELERY_RESULT_BACKEND")
    proc_broker = os.environ.get("CELERY_BROKER_URL")
    proc_backend = os.environ.get("CELERY_RESULT_BACKEND")

    if file_broker is not None:
        logger.warning(".env CELERY_BROKER_URL=%s", file_broker)
    if file_backend is not None:
        logger.warning(".env CELERY_RESULT_BACKEND=%s", file_backend)

    if proc_broker and file_broker and proc_broker.strip() != file_broker.strip():
        logger.warning(
            "CELERY_BROKER_URL 被进程环境覆盖: process=%s dotenv_file=%s "
            "(load_dotenv override=False，已存在的系统/终端变量优先)",
            proc_broker,
            file_broker,
        )
    if proc_backend and file_backend and proc_backend.strip() != file_backend.strip():
        logger.warning(
            "CELERY_RESULT_BACKEND 被进程环境覆盖: process=%s dotenv_file=%s",
            proc_backend,
            file_backend,
        )

    if proc_broker:
        _warn_amqp_source(logger, "process", proc_broker)
    if proc_backend:
        _warn_amqp_source(logger, "process(CELERY_RESULT_BACKEND)", proc_backend)
    if file_broker:
        _warn_amqp_source(logger, "dotenv_file", file_broker)

    if sys.platform == "win32":
        for scope in ("User", "Machine"):
            wb = _windows_env_var("CELERY_BROKER_URL", scope)
            if wb:
                logger.warning("Windows %s CELERY_BROKER_URL=%s", scope, wb)
                _warn_amqp_source(logger, f"Windows-{scope}", wb)
                if file_broker and wb.strip() != file_broker.strip():
                    logger.warning(
                        "CELERY_BROKER_URL 可能被 Windows %s 环境变量覆盖: windows=%s dotenv_file=%s",
                        scope,
                        wb,
                        file_broker,
                    )
            wbe = _windows_env_var("CELERY_RESULT_BACKEND", scope)
            if wbe:
                logger.warning("Windows %s CELERY_RESULT_BACKEND=%s", scope, wbe)
                _warn_amqp_source(logger, f"Windows-{scope}(backend)", wbe)
