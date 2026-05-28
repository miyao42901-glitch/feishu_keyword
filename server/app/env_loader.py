"""加载仓库根目录环境变量：先 .env（部署/默认），再 .env.local（本机覆盖）。"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

SERVER_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SERVER_ROOT.parent


def load_server_dotenv() -> None:
    load_dotenv(REPO_ROOT / ".env")
    local = REPO_ROOT / ".env.local"
    if local.is_file():
        load_dotenv(local, override=True)
