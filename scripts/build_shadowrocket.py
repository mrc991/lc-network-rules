# -*- coding: utf-8 -*-
"""Johnshall sr_top500_whitelist_ad.conf + clash/Custom_Clash.ini → shadowrocket/Custom_Shadowrocket_whitelist_ad.conf

迁移自 mrc991/ShadowRocket-rules scripts/merge_johnshall.py。
广告段（Reject）在前，LC 分组规则居中，Johnshall 直连/国内段在后，FINAL 走 🐟 漏网之鱼。
DNS 复写为与 Clash Mi 一致的国内 DoH；所有 IP 类规则强制 no-resolve（防 DNS 泄漏）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sr_base as base  # noqa: E402
import upstream  # noqa: E402

ROOT = upstream.ROOT
OUT = ROOT / "shadowrocket" / "Custom_Shadowrocket_whitelist_ad.conf"

DOH_LINE = base.PRIMARY_DNS
FALLBACK_DOH_LINE = base.FALLBACK_DNS
SKIP_APPEND = ", " + base.SKIP_PROXY_EXTRA
IP_RULE_TYPES = ("GEOIP", "IP-CIDR", "IP-CIDR6", "IP-ASN")


def split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"HEADER": []}
    current = "HEADER"
    for line in text.splitlines():
        s = line.strip()
        if len(s) >= 3 and s.startswith("[") and s.endswith("]") and s[1].isalpha():
            current = s
            sections[current] = []
            continue
        sections.setdefault(current, []).append(line)
    return sections


def rewrite_general(lines: list[str]) -> list[str]:
    out: list[str] = []
    replaced_dns = replaced_fallback = False
    for line in lines:
        if re.match(r"^\s*dns-server\s*=", line, re.I):
            out.append(DOH_LINE)
            replaced_dns = True
        elif re.match(r"^\s*fallback-dns-server\s*=", line, re.I):
            out.append(FALLBACK_DOH_LINE)
            replaced_fallback = True
        elif re.match(r"^\s*skip-proxy\s*=", line, re.I):
            if "95516.com" not in line:
                line = line.rstrip() + SKIP_APPEND
            out.append(line)
        else:
            out.append(line)
    if not replaced_dns:
        out.append(DOH_LINE)
    if not replaced_fallback:
        out.append(FALLBACK_DOH_LINE)
    return out


def split_johnshall_rules(rule_lines: list[str]) -> tuple[list[str], list[str]]:
    """广告（Reject）段保持最前；Direct/CN/FINAL 段放到 LC 规则之后。"""
    ads: list[str] = []
    rest: list[str] = []
    seen_direct_block = False
    for line in rule_lines:
        stripped = line.strip()
        if not seen_direct_block and (
            stripped.endswith(",Direct")
            or stripped.endswith(",DIRECT")
            or stripped.startswith("FINAL,")
            or "AppleNews" in stripped
        ):
            seen_direct_block = True
        (rest if seen_direct_block else ads).append(line)
    return ads, rest


def add_no_resolve(line: str) -> str:
    s = line.strip()
    if s and not s.startswith("#") and s.split(",", 1)[0].upper() in IP_RULE_TYPES and "no-resolve" not in s.lower():
        return s + ",no-resolve"
    return line


def remap_upstream_policy(line: str) -> str:
    s = line.strip()
    if not s or s.startswith("#"):
        return line
    if "AppleNews" in s and s.endswith(",PROXY"):
        return s[:-6] + ",🇺🇸 美国节点"
    if s == "FINAL,PROXY":
        return "FINAL,🐟 漏网之鱼"
    if s.endswith(",PROXY"):
        return s[:-6] + ",🐟 漏网之鱼"
    if s.upper() == "GEOIP,CN,DIRECT":
        return "GEOIP,CN,🎯 全球直连,no-resolve"
    return add_no_resolve(line)


def build(text: str) -> list[str]:
    sections = split_sections(text)
    general = rewrite_general(sections.get("[General]", []))
    ads, rest = split_johnshall_rules(sections.get("[Rule]", []))
    ads = [add_no_resolve(x) for x in ads]
    rest_body = [x for x in (remap_upstream_policy(r) for r in rest) if not x.strip().startswith("FINAL,")]

    out: list[str] = [
        "# LC Shadowrocket 配置（自动生成，勿手改）：Johnshall sr_top500_whitelist_ad + LC 分组",
        f"# upstream: https://github.com/{upstream.JOHNSHALL['repo']}/blob/{upstream.JOHNSHALL['ref']}/{upstream.JOHNSHALL['path']}",
        "# 分组与规则来自本仓库 clash/Custom_Clash.ini；DNS 与 Clash Mi 覆写一致（国内 DoH）",
        "# 不含节点。从「配置」页 URL 导入并「使用配置」，不要加到首页订阅。",
        "",
        "[General]",
    ]
    out.extend(general)
    if general and general[-1].strip():
        out.append("")
    out.append("[Proxy Group]")
    out.extend(base.proxy_group_lines())
    out.append("")
    out.append("[Rule]")
    out.extend(base.priority_direct_rules())
    out.append("")
    out.extend(ads)
    if ads and ads[-1].strip():
        out.append("")
    out.append("# ===== LC groups (clash/Custom_Clash.ini) =====")
    out.extend(base.overlay_rule_lines(include_broad_cn=False, include_final=False, include_nonstandard_ports=False))
    out.append("")
    out.append("# ===== johnshall Direct / CN =====")
    out.extend(rest_body)
    out.append("")
    out.extend(base.nonstandard_port_lines())
    out.append("FINAL,🐟 漏网之鱼")
    out.append("")
    for extra in ("[URL Rewrite]", "[MITM]", "[Host]", "[Script]"):
        if extra in sections:
            out.append(extra)
            out.extend(sections[extra])
            if sections[extra] and sections[extra][-1].strip():
                out.append("")
    return out


def main() -> str:
    text, sha = upstream.johnshall()
    out = build(text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes("\n".join(out).encode("utf-8"))
    print(f"[build_shadowrocket] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes, {len(out)} lines, upstream {sha[:8]})")
    return sha


if __name__ == "__main__":
    main()
