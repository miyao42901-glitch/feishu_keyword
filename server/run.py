"""启动统一 HTTP 服务（单端口）。在 server 目录下执行: python run.py"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import uvicorn  # noqa: E402

if __name__ == "__main__":
    host = os.environ.get("HTTP_HOST", "0.0.0.0")
    port = int(os.environ.get("HTTP_PORT", "8765"))
    reload = os.environ.get("HTTP_RELOAD", "").strip() in ("1", "true", "yes")
    workers = max(1, int(os.environ.get("HTTP_WORKERS", "1")))
    kwargs: dict = {"host": host, "port": port}
    if reload:
        kwargs["reload"] = True
    elif workers > 1:
        kwargs["workers"] = workers
    uvicorn.run("http_service:app", **kwargs)

    # 启动命令
    # uvicorn http_service:app --host 0.0.0.0 --port 8765 --workers 4
