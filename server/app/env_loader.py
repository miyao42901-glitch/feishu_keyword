"""加载 server 目录下环境变量：先 .env（部署/默认），再 .env.local（本机局域网开发，覆盖）。"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

SERVER_ROOT = Path(__file__).resolve().parent.parent


def load_server_dotenv() -> None:
    load_dotenv(SERVER_ROOT / ".env")
    local = SERVER_ROOT / ".env.local"
    if local.is_file():
        load_dotenv(local, override=True)
