"""读取 CI 写入的 BUILD_INFO（key=value 每行）。"""

from __future__ import annotations

from pathlib import Path


def read_build_info() -> dict[str, str]:
    p = Path(__file__).resolve().parent.parent / "BUILD_INFO"
    if not p.is_file():
        return {}
    info: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        info[k.strip()] = v.strip()
    return info
