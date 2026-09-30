# -*- coding: utf-8 -*-
"""上游 Custom_Clash.ini + custom/clash-overlay.yaml → clash/Custom_Clash.ini

锚点必须在上游恰好出现一次；任何校验失败都会非零退出，CI 不会发布。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import upstream  # noqa: E402

ROOT = upstream.ROOT
OVERLAY = ROOT / "custom" / "clash-overlay.yaml"
OUT = ROOT / "clash" / "Custom_Clash.ini"

GROUP_PREFIX = "custom_proxy_group="
BUILTIN = {"DIRECT", "REJECT", "REJECT-DROP", "PASS"}


class BuildError(Exception):
    pass


def _block(text: str) -> list[str]:
    return [ln.rstrip() for ln in (text or "").strip("\n").splitlines()]


def _find_once(lines: list[str], anchor: str) -> int:
    hits = [i for i, ln in enumerate(lines) if ln.strip() == anchor.strip()]
    if len(hits) != 1:
        raise BuildError(f"anchor must match exactly once, got {len(hits)}: {anchor!r}")
    return hits[0]


def apply_ops(lines: list[str], ops: list[dict]) -> list[str]:
    plan: list[tuple[int, str, list[str]]] = []
    for op in ops:
        kinds = [k for k in ("after", "before", "replace") if k in op]
        if len(kinds) != 1:
            raise BuildError(f"op needs exactly one of after/before/replace: {op}")
        kind = kinds[0]
        plan.append((_find_once(lines, op[kind]), kind, _block(op.get("lines", ""))))
    idx = [p[0] for p in plan]
    if len(set(idx)) != len(idx):
        raise BuildError("two ops target the same upstream line")
    out = list(lines)
    for i, kind, new in sorted(plan, key=lambda p: p[0], reverse=True):
        if kind == "after":
            out[i + 1 : i + 1] = new
        elif kind == "before":
            out[i:i] = new
        else:
            out[i : i + 1] = new
    return out


def replace_groups(lines: list[str], groups: list[str]) -> list[str]:
    pos = [i for i, ln in enumerate(lines) if ln.startswith(GROUP_PREFIX)]
    if not pos:
        raise BuildError("upstream has no custom_proxy_group lines")
    first = pos[0]
    kept = [ln for ln in lines if not ln.startswith(GROUP_PREFIX)]
    return kept[:first] + groups + kept[first:]


def apply_rewrite(text: str, rules: list[dict]) -> str:
    for r in rules or []:
        if "from" in r:
            text = text.replace(r["from"], r["to"])
        else:
            text = re.sub(r["regex"], r["to"], text)
    return text


def group_names(lines: list[str]) -> list[str]:
    return [ln[len(GROUP_PREFIX):].split("`", 1)[0].strip() for ln in lines if ln.startswith(GROUP_PREFIX)]


def validate(text: str, upstream_lines: list[str], ignore: set[str] | None = None) -> list[str]:
    lines = text.splitlines()
    warnings: list[str] = []
    names = group_names(lines)
    defined = set(names)
    if len(defined) != len(names):
        raise BuildError("duplicate custom_proxy_group names")

    rulesets = [ln for ln in lines if ln.startswith("ruleset=")]
    for ln in rulesets:
        grp = ln[len("ruleset="):].split(",", 1)[0].strip()
        if grp not in defined:
            raise BuildError(f"ruleset references undefined group {grp!r}: {ln}")

    for ln in lines:
        if not ln.startswith(GROUP_PREFIX):
            continue
        for part in ln.split("`")[2:]:
            if part.startswith("[]"):
                ref = part[2:].strip()
                if ref not in defined and ref not in BUILTIN:
                    raise BuildError(f"group member references undefined group {ref!r}: {ln[:80]}")

    if "ruleset=🎯 全球直连,[]GEOIP,cn,no-resolve" not in lines:
        raise BuildError("GEOIP,cn must keep no-resolve (DNS leak guard)")
    finals = [i for i, ln in enumerate(rulesets) if ln.endswith(",[]FINAL")]
    if finals != [len(rulesets) - 1]:
        raise BuildError("exactly one FINAL ruleset must be the last ruleset")
    if ".mrs," in text or "cdn.jsdelivr.net/gh/Aethersailor" in text:
        raise BuildError("unrewritten .mrs or cdn.jsdelivr.net URL left in output")

    # 上游新增、我们没有的分组：没有规则引用时只提示
    new_up = [g for g in group_names(upstream_lines) if g not in defined and g not in (ignore or set())]
    if new_up:
        warnings.append(f"upstream groups not in custom/proxy_groups.ini (unused): {new_up}")
    return warnings


def build(upstream_text: str) -> tuple[str, list[str]]:
    cfg = yaml.safe_load(OVERLAY.read_text(encoding="utf-8"))
    up = upstream_text.splitlines()
    start = _find_once(up, "[custom]")
    body = apply_ops(up[start:], cfg.get("ops", []))
    groups = [ln for ln in (ROOT / cfg["proxy_groups"]).read_text(encoding="utf-8").splitlines() if ln.strip()]
    body = replace_groups(body, groups)
    text = "\n".join(_block(cfg.get("header", "")) + [""] + body).rstrip("\n") + "\n"
    text = apply_rewrite(text, cfg.get("rewrite", []))
    return text, validate(text, up, set(cfg.get("ignore_upstream_groups") or []))


def main() -> str:
    ini, sha = upstream.clash_ini()
    try:
        text, warnings = build(ini)
    except BuildError as e:
        raise SystemExit(f"[build_clash] FAILED: {e}")
    for w in warnings:
        print(f"[build_clash] warning: {w}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(text.encode("utf-8"))
    print(f"[build_clash] wrote {OUT.relative_to(ROOT)} ({len(text.splitlines())} lines, upstream {sha[:8]})")
    return sha


if __name__ == "__main__":
    main()
