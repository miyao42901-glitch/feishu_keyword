#!/usr/bin/env python3
"""
工具函数导入路径迁移：旧 → 新（本项目已按新路径改完；本脚本供其它分支/二次核对或 --apply 批量替换）。

用法：
  python scripts/refactor_utils_imports.py           # 仅打印映射表
  python scripts/refactor_utils_imports.py --apply # 对当前目录下 .py 做替换（慎用，先 git diff）

运行目录：仓库 ``python/`` 的上级或把 ROOT 改为你的项目根。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 以 ``feishu_keyword/python`` 为根（脚本位于 python/scripts/）
ROOT = Path(__file__).resolve().parent.parent

# 旧行片段 → 新行（整行替换，按顺序应用；更长/更具体的模式放前面）
REPLACEMENTS: list[tuple[str, str]] = [
    (
        "from social_platform.str_utils import ",
        "from social_platform.utils.coercion import ",
    ),
    (
        "from social_platform.time_utils import ",
        "from social_platform.utils.time_ms import ",
    ),
    (
        "from social_platform.worker_utils import ",
        "from social_platform.utils.worker_runtime import ",
    ),
    (
        "from social_platform.services.async_task_ids import ",
        "from social_platform.utils.async_task_ids import ",
    ),
    (
        "from http_api.dajiala_params import ",
        "from social_platform.utils.param_dict import ",
    ),
    (
        "from http_api.versions import ",
        "from http_api.constants import ",
    ),
    (
        "from social_platform.task_envelope import ",
        "from social_platform.schemas.task_envelope import ",
    ),
    (
        "from social_platform.urls import ",
        "from http_api.constants import ",
    ),
]


def print_mapping() -> None:
    print("替换映射（旧 → 新）\n")
    for old, new in REPLACEMENTS:
        print(f"  {old!r}")
        print(f"  → {new!r}\n")


def apply_to_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != orig:
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Utils import path migration")
    ap.add_argument("--apply", action="store_true", help="Rewrite .py files under python/")
    args = ap.parse_args()

    print_mapping()

    if not args.apply:
        print("未指定 --apply，未修改任何文件。")
        return 0

    changed = 0
    for path in sorted(ROOT.rglob("*.py")):
        if "scripts" in path.parts and path.name == "refactor_utils_imports.py":
            continue
        if apply_to_file(path):
            print(f"updated: {path.relative_to(ROOT)}")
            changed += 1
    print(f"\n共改写 {changed} 个文件。")
    return 0


if __name__ == "__main__":
    if not ROOT.is_dir():
        print("ROOT 不是目录:", ROOT, file=sys.stderr)
        sys.exit(1)
    raise SystemExit(main())
