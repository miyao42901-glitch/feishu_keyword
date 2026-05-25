"""Worker 进程启动时加载 python/.env（不依赖 config 包）。"""

from __future__ import annotations

from pathlib import Path

_LOADED = False


def ensure_dotenv_loaded() -> None:
    global _LOADED
    if _LOADED:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        _LOADED = True
        return

    here = Path(__file__).resolve().parent  # .../python/social_platform
    py_root = here.parent  # .../python（.env 所在目录）
    env_file = py_root / ".env"
    if env_file.is_file():
        load_dotenv(env_file, override=False)
    local_file = py_root / ".env.local"
    if local_file.is_file():
        load_dotenv(local_file, override=True)
    elif not env_file.is_file():
        load_dotenv(override=False)
    _LOADED = True
