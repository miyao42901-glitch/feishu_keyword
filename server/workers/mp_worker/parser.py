"""公众号接口 JSON 解析（字段映射 + HTML 清洗 title）。"""

from __future__ import annotations

import json
import logging
from typing import Any

from social_platform.utils.duration import parse_htmlstr_to_clean
from social_platform.utils.time_ms import to_ms_timestamp
from social_platform.utils.coercion import (
    extract_api_balance_cost,
    extract_cookies_buffer,
)
from social_platform.utils.worker_runtime import (
    split_exclude_needles,
    text_contains_any_needle,
)

logger = logging.getLogger(__name__)


def _decode_report_extinfo(report_str: str) -> dict[str, Any]:
    if not report_str or not isinstance(report_str, str):
        return {}
    try:
        data = json.loads(report_str)
    except Exception:
        try:
            decoded = report_str.encode("utf-8").decode("unicode_escape")
            data = json.loads(decoded)
        except Exception:
            return {}
    return data if isinstance(data, dict) else {}


class MpParser:
    def parse(self, raw: dict[str, Any], *, exclude_words: str = "") -> dict[str, Any]:
        needles = split_exclude_needles(exclude_words)
        data = raw.get("data") or {}
        if not isinstance(data, dict):
            data = {}
        balance, cost = extract_api_balance_cost(raw, data=data)

        # 更健壮的 items 提取，支持多种响应结构
        items_list: list[dict[str, Any]] = []
        raw_data = data.get("data")
        if isinstance(raw_data, list):
            for block in raw_data:
                if isinstance(block, dict):
                    if isinstance(block.get("items"), list):
                        items_list.extend(
                            [x for x in block["items"] if isinstance(x, dict)]
                        )
                    elif isinstance(block.get("subBoxes"), list):
                        for sub in block["subBoxes"]:
                            if isinstance(sub, dict) and isinstance(
                                sub.get("items"), list
                            ):
                                items_list.extend(
                                    [x for x in sub["items"] if isinstance(x, dict)]
                                )
                elif isinstance(block, dict):
                    items_list.append(block)
        elif isinstance(raw_data, dict):
            if isinstance(raw_data.get("items"), list):
                items_list = [x for x in raw_data["items"] if isinstance(x, dict)]
            elif isinstance(raw_data.get("list"), list):
                items_list = [x for x in raw_data["list"] if isinstance(x, dict)]

        rows: list[dict[str, Any]] = []
        for item in items_list:
            if not isinstance(item, dict):
                continue

            report_id = (
                item.get("reportId")
                or item.get("article_id")
                or item.get("post_id")
                or ""
            )
            url = item.get("doc_url") or item.get("url") or ""
            if not report_id and url:
                if "mid=" in url:
                    report_id = url.split("mid=")[-1].split("&")[0]
                elif "idx=" in url:
                    report_id = url.split("idx=")[-1].split("&")[0]

            title = parse_htmlstr_to_clean(item.get("title") or "") or "无标题"
            summary = (
                parse_htmlstr_to_clean(item.get("desc") or item.get("summary") or "")
                or ""
            )
            if text_contains_any_needle(title, needles) or text_contains_any_needle(
                summary, needles
            ):
                continue

            date_val = item.get("date") or item.get("pubTime") or 0
            # 秒级 -> 毫秒存储以保持一致
            publish_time = (
                int(date_val) * 1000
                if isinstance(date_val, (int, float)) and date_val < 1e11
                else int(date_val or 0)
            )

            url = item.get("doc_url") or ""

            source = item.get("source") or {}
            if not isinstance(source, dict):
                source = {}
            company_name = (
                item.get("company_name")
                or source.get("title")
                or item.get("nickname")
                or ""
            )

            avatar_url = item.get("thumbUrl") or item.get("avatar_url") or ""
            biz = item.get("biz") or ""
            if not biz and url and "biz=" in url:
                biz = url.split("biz=")[-1].split("&")[0]

            row = {
                "post_id": str(report_id),
                "company_name": company_name,
                "publish_time": publish_time,
                "title": title,
                "summary": summary,
                "url": url,
                "avatar_url": avatar_url,
                "biz": biz,
            }
            rows.append(row)

        cookies_buffer = extract_cookies_buffer(data)
        if data.get("cookies") and not cookies_buffer:
            logger.warning(
                "mp cookies field present but cookies_buffer empty offset=%s",
                data.get("offset", ""),
            )

        return {
            "data": rows,
            "balance": balance,
            "cost": cost,
            "error": None,
            "insufficient_balance": False,
            "next_offset": data.get("offset", ""),
            "cookies_buffer": cookies_buffer,
            "total": len(rows),
        }
