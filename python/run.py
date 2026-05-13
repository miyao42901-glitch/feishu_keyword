"""启动统一 HTTP 服务（单端口）。在 python 目录下执行: python run.py"""
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
    uvicorn.run("http_service:app", host=host, port=port, reload=reload)
