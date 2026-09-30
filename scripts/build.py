# -*- coding: utf-8 -*-
"""一键构建：Clash 分流 → 广告 rule-provider → Shadowrocket，最后写 upstream.lock。

任一步失败即非零退出；CI 只在 build + tests 全部通过后才提交产物。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_adblock  # noqa: E402
import build_clash  # noqa: E402
import build_shadowrocket  # noqa: E402
import upstream  # noqa: E402

LOCK = upstream.ROOT / "upstream.lock"


def main() -> None:
    clash_sha = build_clash.main()
    build_adblock.main()
    js_sha = build_shadowrocket.main()
    a, j = upstream.AETHERSAILOR, upstream.JOHNSHALL
    LOCK.write_text(
        "# 本次产物所用的上游版本（自动生成）\n"
        f"{a['repo']}@{a['ref']}: {clash_sha}\n"
        f"{j['repo']}@{j['ref']}: {js_sha}\n",
        encoding="utf-8",
    )
    print(f"[build] wrote {LOCK.name}")


if __name__ == "__main__":
    main()
