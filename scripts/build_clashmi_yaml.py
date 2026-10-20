# -*- coding: utf-8 -*-
"""生成 Clash Mi 的 YAML 覆写 overwrite/Clash_Mi_Merge.yaml（Clash Mi 客户端订阅的就是这个地址）。

Clash Mi 的 YAML 覆写语义：字典深合并，列表/标量整体替换；不认识 prepend-rules。
所以这里把完整 rules 写进覆写：先放 custom/Clash_Mi_Merge.src.yaml 的 prepend-rules，
再接上「同一份 clash/Custom_Clash.ini 经 subconverter 展开（expand=true，与真实订阅后端相同）」的全部订阅规则（去掉完全重复项）。
覆写的 rules 会整体替换订阅的 rules，效果等于把那些规则插到订阅规则最前面。

只有 Clash Mi 读这个文件；OpenClash 用 overwrite/LC_AdBlock.conf，Shadowrocket 用 shadowrocket/*.conf。

用法：
  python scripts/build_clashmi_yaml.py --sub expanded_sub.yaml   # e2e/CI：用新展开的订阅规则重建
  python scripts/build_clashmi_yaml.py                           # build.py：只按源文件刷新非 rules 部分，沿用现有订阅规则
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "custom" / "Clash_Mi_Merge.src.yaml"
DST = ROOT / "overwrite" / "Clash_Mi_Merge.yaml"

HEADER = """# Clash Mi 统一覆写（YAML，Mac / Windows 的 Clash Mi 订阅此地址）——自动生成，请勿手改
# 源文件：custom/Clash_Mi_Merge.src.yaml；生成：scripts/build_clashmi_yaml.py（CI 每天重建）
# rules = 源文件 prepend-rules + 同一模板 clash/Custom_Clash.ini 经 subconverter 展开的完整订阅规则。
# Clash Mi 的 YAML 覆写对列表整体替换，所以这里的 rules 会替换订阅 rules，等效于把 prepend-rules 放到最前。
# 注意：find-process-mode 会被 Clash Mi「核心设置 → 进程匹配模式」再覆盖，每台机器需在 App 里设为 always。
# 订阅：{sub_count} 条，前置：{pre_count} 条，合计：{total} 条
"""


def load_src() -> tuple[dict, list[str]]:
    src = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    if "rules" in src:
        raise SystemExit("[clashmi-yaml] custom/Clash_Mi_Merge.src.yaml must not contain rules:")
    pre = list(src.pop("prepend-rules", None) or [])
    if not pre:
        raise SystemExit("[clashmi-yaml] prepend-rules empty in source")
    return src, pre


def merge_rules(pre: list[str], sub_rules: list[str]) -> list[str]:
    seen = set(pre)
    return list(pre) + [r for r in sub_rules if r not in seen]


def render(sub_rules: list[str]) -> str:
    src, pre = load_src()
    rules = merge_rules(pre, sub_rules)
    doc = dict(src)
    doc["rules"] = rules
    body = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=1000)
    return HEADER.format(sub_count=len(sub_rules), pre_count=len(pre), total=len(rules)) + body


def current_sub_rules() -> list[str]:
    """从现有产物里取回订阅规则部分：按文件头记录的「前置：K 条」剥掉开头 K 条。"""
    if not DST.is_file():
        raise SystemExit("[clashmi-yaml] no existing output; run with --sub first")
    text = DST.read_text(encoding="utf-8")
    m = re.search(r"前置：(\d+) 条", text)
    if not m:
        raise SystemExit("[clashmi-yaml] existing output has no header count; run with --sub")
    old = yaml.safe_load(text).get("rules") or []
    return old[int(m.group(1)):]


def refresh() -> None:
    """build.py 调用：按源文件刷新非 rules 部分，沿用现有订阅规则。"""
    sub_rules = current_sub_rules()
    DST.write_text(render(sub_rules), encoding="utf-8")
    print(f"[clashmi-yaml] refreshed {DST.relative_to(ROOT)} (subscription {len(sub_rules)} rules kept)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sub", help="subconverter 展开后的订阅 YAML（expand=true）")
    a = ap.parse_args()
    if a.sub:
        sub = yaml.safe_load(Path(a.sub).read_text(encoding="utf-8"))
        sub_rules = list(sub.get("rules") or [])
        if len(sub_rules) < 500:
            raise SystemExit(f"[clashmi-yaml] expanded subscription has too few rules: {len(sub_rules)}")
    else:
        sub_rules = current_sub_rules()
    DST.write_text(render(sub_rules), encoding="utf-8")
    print(f"[clashmi-yaml] wrote {DST.relative_to(ROOT)} (subscription {len(sub_rules)} rules)")


if __name__ == "__main__":
    main()
