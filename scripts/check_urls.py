# -*- coding: utf-8 -*-
"""检查产物引用的外部规则 URL：404/410 视为失败（上游改名或删除），超时等网络问题只告警。"""
from __future__ import annotations

import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = "gh/mrc991/lc-network-rules@"  # 本仓库文件由 tests.py 检查本地是否存在


def urls() -> list[str]:
    found: set[str] = set()
    ini = (ROOT / "clash" / "Custom_Clash.ini").read_text(encoding="utf-8")
    found.update(re.findall(r"clash-(?:domain|classic|ipcidr):(https://[^,\s]+)", ini))
    sr = (ROOT / "shadowrocket" / "Custom_Shadowrocket_whitelist_ad.conf").read_text(encoding="utf-8")
    found.update(re.findall(r"^RULE-SET,(https://[^,\s]+)", sr, re.M))
    return sorted(u for u in found if SELF not in u)


def status(url: str) -> int:
    for i in range(3):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "lc-network-rules-builder"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return e.code
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3 * (i + 1))
    return 0


def main() -> None:
    missing, flaky = [], []
    items = urls()
    for u in items:
        c = status(u)
        if c in (404, 410):
            missing.append(f"{c} {u}")
        elif c != 200:
            flaky.append(f"{c or 'timeout'} {u}")
    for f in flaky:
        print(f"::warning::url check inconclusive: {f}")
    if missing:
        print("\n".join(missing))
        raise SystemExit(f"[check_urls] FAILED: {len(missing)} referenced rule URL(s) missing")
    print(f"[check_urls] {len(items)} urls ok ({len(flaky)} inconclusive)")


if __name__ == "__main__":
    main()
