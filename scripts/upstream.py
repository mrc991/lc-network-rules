# -*- coding: utf-8 -*-
"""上游拉取：先把分支解析成 commit sha，再按 sha 取原始文件，保证一次构建内各文件版本一致。

拉取失败直接报错退出，不回退到缓存，避免用旧数据发布。
本地调试可用环境变量指向本地文件：
  LC_UPSTREAM_CLASH_INI   上游 Custom_Clash.ini 路径
  LC_UPSTREAM_JOHNSHALL   上游 sr_top500_whitelist_ad.conf 路径
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AETHERSAILOR = {"repo": "Aethersailor/Custom_OpenClash_Rules", "ref": "main", "path": "cfg/Custom_Clash.ini"}
JOHNSHALL = {"repo": "Johnshall/Shadowrocket-ADBlock-Rules-Forever", "ref": "release", "path": "sr_top500_whitelist_ad.conf"}

UA = "lc-network-rules-builder"


def _get(url: str, *, accept: str | None = None, retries: int = 3) -> bytes:
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    last: Exception | None = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            if not data:
                raise RuntimeError("empty response")
            return data
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise SystemExit(f"fetch failed: {url}: {last}")


def resolve_sha(src: dict) -> str:
    data = json.loads(_get(f"https://api.github.com/repos/{src['repo']}/commits/{src['ref']}", accept="application/vnd.github+json"))
    return data["sha"]


def fetch_text(src: dict, env: str) -> tuple[str, str]:
    """返回 (文本, sha)。本地覆盖时 sha 为 'local'。"""
    local = os.environ.get(env, "").strip()
    if local:
        return Path(local).read_text(encoding="utf-8"), "local"
    sha = resolve_sha(src)
    raw = _get(f"https://raw.githubusercontent.com/{src['repo']}/{sha}/{src['path']}")
    return raw.decode("utf-8"), sha


_cache: dict[str, tuple[str, str]] = {}


def clash_ini() -> tuple[str, str]:
    if "ini" not in _cache:
        _cache["ini"] = fetch_text(AETHERSAILOR, "LC_UPSTREAM_CLASH_INI")
    return _cache["ini"]


def johnshall() -> tuple[str, str]:
    if "js" not in _cache:
        _cache["js"] = fetch_text(JOHNSHALL, "LC_UPSTREAM_JOHNSHALL")
    return _cache["js"]
