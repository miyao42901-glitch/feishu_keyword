"""Worker 进程启动时加载仓根 .env（不依赖 config 包）。"""

from __future__ import annotations

from pathlib import Path

_LOADED = False


def _repo_root() -> Path:
    here = Path(__file__).resolve().parent  # .../server/social_platform
    return here.parent.parent  # 仓库根


def ensure_dotenv_loaded() -> None:
    global _LOADED
    if _LOADED:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        _LOADED = True
        return

    root = _repo_root()
    for name in (".env", ".env.local"):
        candidate = root / name
        if candidate.is_file():
            load_dotenv(candidate, override=name == ".env.local")
    _LOADED = True
