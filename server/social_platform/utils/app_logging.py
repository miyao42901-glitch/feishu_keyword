"""统一应用日志：控制台 + 按天滚动文件，自动清理超过 retention_days 的历史文件。"""

from __future__ import annotations

import logging
import sys
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_PY_ROOT = Path(__file__).resolve().parent.parent.parent
_ROOT_CONFIGURED = False


class AppLogConfig:
    """应用日志初始化（进程内幂等）。"""

    DEFAULT_RETENTION_DAYS = 7
    LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def setup(
        cls,
        service_name: str,
        *,
        log_dir: Path | str | None = None,
        level: str | int = "INFO",
        retention_days: int = DEFAULT_RETENTION_DAYS,
        console: bool = True,
    ) -> None:
        global _ROOT_CONFIGURED
        if _ROOT_CONFIGURED:
            return

        name = (service_name or "app").strip() or "app"
        retention = max(1, int(retention_days))
        resolved_dir = Path(log_dir) if log_dir else _PY_ROOT / "logs"
        resolved_dir.mkdir(parents=True, exist_ok=True)
        cls.purge_old_files(resolved_dir, retention_days=retention)

        root = logging.getLogger()
        root.setLevel(cls._resolve_level(level))

        formatter = logging.Formatter(cls.LOG_FORMAT, datefmt=cls.DATE_FORMAT)

        if console:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(formatter)
            root.addHandler(stream_handler)

        file_handler = TimedRotatingFileHandler(
            filename=str(resolved_dir / f"{name}.log"),
            when="midnight",
            interval=1,
            backupCount=retention,
            encoding="utf-8",
            delay=True,
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

        cls._quiet_noisy_loggers()

        _ROOT_CONFIGURED = True
        logging.getLogger(__name__).info(
            "logging configured service=%s dir=%s level=%s retention_days=%d",
            name,
            resolved_dir,
            logging.getLevelName(root.level),
            retention,
        )

    @staticmethod
    def _quiet_noisy_loggers() -> None:
        """热重载等第三方库 INFO 默认不刷屏（仍可通过 LOG_LEVEL=DEBUG 看细节）。"""
        for logger_name in ("watchfiles", "watchfiles.main"):
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    @staticmethod
    def purge_old_files(log_dir: Path, *, retention_days: int) -> None:
        """删除 log_dir 下修改时间早于 retention_days 的 *.log* 文件。"""
        cutoff = time.time() - max(1, int(retention_days)) * 86400
        for path in log_dir.glob("*.log*"):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
            except OSError:
                continue

    @staticmethod
    def _resolve_level(level: str | int) -> int:
        if isinstance(level, int):
            return level
        text = str(level or "INFO").strip().upper()
        return getattr(logging, text, logging.INFO)
