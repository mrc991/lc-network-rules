# -*- coding: utf-8 -*-
"""产物不变量检查。迁移自 mrc991/ShadowRocket-rules scripts/test_invariants.py，去掉 sing-box，补 Clash ini 与覆写检查。

用法：先跑 build.py，再跑本脚本；任一断言失败即非零退出。
"""
from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import build_clash  # noqa: E402
import build_shadowrocket as merge  # noqa: E402
import sr_base as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INI = ROOT / "clash" / "Custom_Clash.ini"
SR = ROOT / "shadowrocket" / "Custom_Shadowrocket_whitelist_ad.conf"
ADB_DOMAIN = ROOT / "overwrite" / "adblock" / "AdBlock_Domain.yaml"
ADB_IP = ROOT / "overwrite" / "adblock" / "AdBlock_IP.yaml"
REPO_CDN = "https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/"

PROTECTED = [
    "unionpay.com", "95516.com", "cloudpay.com.cn", "qq.com", "weixin.qq.com", "wechat.com",
    "servicewechat.com", "tenpay.com", "alipay.com", "taobao.com", "tmall.com", "jd.com",
    "apple.com", "icloud.com", "github.com", "google.com", "microsoft.com", "jsdelivr.net",
    "tailscale.com", "bigrich.cc", "baidu.com", "aliyun.com", "openai.com", "anthropic.com",
]

FIXTURE_INI = """
[custom]
ruleset=🎥 AppleTV+,[]GEOSITE,apple-tvplus
ruleset=🍎 App Store,[]DOMAIN-SUFFIX,apps.apple.com
ruleset=🍎 App Store,[]DOMAIN-SUFFIX,itunes.apple.com
ruleset=🍎 苹果中国,[]GEOSITE,apple-cn
ruleset=🎯 全球直连,[]DOMAIN-SUFFIX,unionpay.com
ruleset=🎯 全球直连,[]DOMAIN-SUFFIX,95516.com
ruleset=🐟 漏网之鱼,[]FINAL
custom_proxy_group=🎯 全球直连`select`[]DIRECT
custom_proxy_group=🎥 AppleTV+`select`[]🇭🇰 香港节点`[]🎯 全球直连
custom_proxy_group=🍎 App Store`select`[]🇺🇸 美国节点`[]🎯 全球直连
custom_proxy_group=🍎 苹果中国`select`[]🎯 全球直连`[]🚀 手动选择
custom_proxy_group=🇭🇰 香港节点`url-test`(港)`https://cp.cloudflare.com/generate_204`300,,50
custom_proxy_group=🇺🇸 美国节点`url-test`(美)`https://cp.cloudflare.com/generate_204`300,,50
custom_proxy_group=🐟 漏网之鱼`select`[]🚀 手动选择`[]🎯 全球直连
"""


def _fail(msg: str) -> None:
    raise AssertionError(msg)


# ---------- Clash 分流 ----------

def test_overlay_anchor_guard() -> None:
    """锚点不存在或重复时必须失败，不能静默插错位置。"""
    lines = ["[custom]", "a", "b", "b"]
    for bad in ({"after": "zzz", "lines": "x"}, {"after": "b", "lines": "x"}):
        try:
            build_clash.apply_ops(lines, [bad])
        except build_clash.BuildError:
            continue
        _fail(f"apply_ops should reject {bad}")
    out = build_clash.apply_ops(lines, [{"after": "a", "lines": "x\ny"}])
    if out != ["[custom]", "a", "x", "y", "b", "b"]:
        _fail(f"apply_ops after wrong: {out}")


def test_clash_ini() -> None:
    text = INI.read_text(encoding="utf-8")
    lines = text.splitlines()
    must = [
        "ruleset=🎯 全球直连,[]GEOIP,cn,no-resolve",
        "ruleset=🀄️ 优选地址,[]DOMAIN-SUFFIX,tailscale.com",
        "ruleset=🎯 全球直连,[]IP-CIDR,45.62.118.67/32,no-resolve",
        "ruleset=🚀 手动选择,[]DOMAIN-SUFFIX,jsdelivr.net",
        "ruleset=🎯 全球直连,[]GEOSITE,Tencent",
        "ruleset=🍎 App Store,[]DOMAIN-SUFFIX,apps.apple.com",
        "ruleset=🎯 全球直连,[]DOMAIN-SUFFIX,95516.com",
        "ruleset=🎯 全球直连,[]DOMAIN-SUFFIX,synology.com",
        "ruleset=🚀 手动选择,[]DOMAIN-SUFFIX,bigrich.cc",
        "ruleset=🐟 漏网之鱼,[]FINAL",
        "enable_rule_generator=true",
        "overwrite_original_rules=true",
    ]
    for m in must:
        if m not in lines:
            _fail(f"Custom_Clash.ini missing: {m}")
    if "ruleset=🎯 全球直连,[]GEOIP,cn\n" in text + "\n":
        _fail("GEOIP,cn without no-resolve")
    # 顺序：个人前置规则在上游直连表之前；App Store 在苹果中国之前
    def pos(s: str) -> int:  # 只看 ruleset 行，注释里出现同名字符串不算
        return next(i for i, ln in enumerate(lines) if ln.startswith("ruleset=") and s in ln)
    if not pos("DOMAIN-SUFFIX,jsdelivr.net") < pos("Custom_Direct_Domain"):
        _fail("jsdelivr proxy must precede Custom_Direct_Domain")
    if not pos("45.62.118.67/32") < pos("Custom_Port_Direct"):
        _fail("DERP direct must precede non-standard ports")
    if not pos("GEOSITE,Tencent") < pos("category-communication"):
        _fail("Tencent direct must precede category-communication")
    if not pos("apple-tvplus") < pos("🍎 App Store,[]DOMAIN-SUFFIX,apps.apple.com") < pos("apple-cn"):
        _fail("order must be AppleTV+ < App Store < 苹果中国")
    if "🍎 苹果服务" in text or "Ⓜ️ 微软服务" in text:
        _fail("upstream 苹果服务/微软服务 must be replaced")
    # 分组引用校验再跑一遍（与构建期相同逻辑）
    build_clash.validate(text, [])


# ---------- Shadowrocket ----------

def test_dns_helpers() -> None:
    assert "223.5.5.5" in base.PRIMARY_DNS and "1.12.12.12" in base.PRIMARY_DNS
    assert "#proxy" not in base.PRIMARY_DNS and "dns.google" not in base.PRIMARY_DNS
    assert "1.1.1.1" not in base.PRIMARY_DNS + base.FALLBACK_DNS
    assert "8.8.8.8" not in base.FALLBACK_DNS and "223.5.5.5" in base.FALLBACK_DNS


def test_priority_us_appstore_and_unionpay() -> None:
    rules = base.priority_direct_rules()
    text = "\n".join(rules)
    if "95516.com" not in text or "unionpay.com" not in text:
        _fail("priority rules missing UnionPay domains")
    if "PROCESS-NAME,AppStore,🍎 App Store" not in text:
        _fail("AppStore process must go to 🍎 App Store")
    if any("AppStore,🎯 全球直连" in x for x in rules):
        _fail("AppStore must not be DIRECT for US Apple ID")
    if any(x.startswith(("DOMAIN-SUFFIX,apple.com,", "DOMAIN-SUFFIX,itunes.apple.com,")) for x in rules):
        _fail("apple.com / itunes.apple.com must not be prepended")


def test_overlay_order_appletv_then_appstore() -> None:
    rules = base.parse_ini_rules(FIXTURE_INI)
    tv = next(i for i, r in enumerate(rules) if "AppleTV" in r)
    store = next(i for i, r in enumerate(rules) if r.startswith("DOMAIN-SUFFIX,itunes.apple.com,"))
    if not tv < store:
        _fail("AppleTV must precede itunes.apple.com")
    if any("Apple/Apple.list" in r for r in rules):
        _fail("Apple.list (17.0.0.0/8) must not be used")
    groups = base.parse_ini_groups(FIXTURE_INI)
    line = next((g for g in groups if g.startswith("🍎 App Store =")), "")
    if not line.startswith("🍎 App Store = select,🇺🇸 美国节点"):
        _fail(f"App Store group must default to US: {line}")


def test_list_name_mapping() -> None:
    ini = "\n".join(
        f"ruleset=🎯 全球直连,clash-{k}:https://x/rule/{f},28800"
        for k, f in [("domain", "Custom_Direct_Domain.yaml"), ("classic", "Custom_Direct_Classical_IP.yaml"),
                     ("domain", "Steam_CDN_Domain.mrs"), ("classic", "Steam_CDN_Classical_IP.yaml")]
    )
    rules = base.parse_ini_rules(ini)
    urls = [r.split(",")[1].rsplit("/", 1)[-1] for r in rules]
    if urls != ["Custom_Direct.list", "Steam_CDN.list"]:
        _fail(f"list mapping/dedupe wrong: {urls}")


def test_rewrite_general_doh() -> None:
    out = "\n".join(merge.rewrite_general([
        "ipv6 = false",
        "skip-proxy = localhost, captive.apple.com",
        "dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query",
    ]))
    if "https://223.5.5.5/dns-query" not in out or "fallback-dns-server" not in out or "95516.com" not in out:
        _fail("rewrite_general incomplete")
    if any(x in out for x in ("dns.google", "1.1.1.1", "dns.alidns.com", "doh.pub")):
        _fail("rewrite_general still has upstream/overseas DNS")


def test_shadowrocket_conf() -> None:
    text = SR.read_text(encoding="utf-8")
    dns_line = next((ln for ln in text.splitlines() if re.match(r"^\s*dns-server\s*=", ln, re.I)), "")
    if "https://223.5.5.5/dns-query" not in dns_line or "#proxy" in dns_line or "dns.google" in dns_line:
        _fail(f"DNS not aligned with Clash Mi: {dns_line}")
    if "GEOIP,CN,🎯 全球直连,no-resolve" not in text or "ipv6 = false" not in text:
        _fail("GEOIP,CN no-resolve / ipv6=false missing")
    for ln in text.splitlines():
        head = ln.split(",", 1)[0].strip().upper()
        if head in ("GEOIP", "IP-CIDR", "IP-CIDR6", "IP-ASN") and "no-resolve" not in ln.lower():
            _fail(f"IP rule without no-resolve (DNS leak): {ln}")
    for m in ("DOMAIN-SUFFIX,95516.com,🎯 全球直连", "PROCESS-NAME,AppStore,🍎 App Store",
              "🍎 App Store = select,🇺🇸 美国节点", "DOMAIN-SUFFIX,itunes.apple.com,🍎 App Store",
              "DOMAIN-SUFFIX,jsdelivr.net,🚀 手动选择", "DOMAIN-SUFFIX,jsdelivr.com,🚀 手动选择"):
        if m not in text:
            _fail(f"shadowrocket conf missing: {m}")
    for bad in ("PROCESS-NAME,AppStore,🎯 全球直连", "DOMAIN-SUFFIX,apple.com,🍎 苹果中国",
                "Apple/Apple.list,🍎 苹果中国", "DOMAIN-SUFFIX,jsdelivr.net,🎯 全球直连"):
        if bad in text:
            _fail(f"shadowrocket conf must not contain: {bad}")
    if not 0 <= text.find("AppleTV/AppleTV.list") < text.find("DOMAIN-SUFFIX,itunes.apple.com,🍎 App Store"):
        _fail("AppleTV list must appear before itunes.apple.com")
    if not 0 <= text.find("DOMAIN-SUFFIX,jsdelivr.net,🚀 手动选择") < text.find("Custom_Direct.list"):
        _fail("jsdelivr proxy must appear before Custom_Direct.list")
    if "mrc991/Custom_OpenClash_Rules" in text or "mrc991/ShadowRocket-rules" in text:
        _fail("shadowrocket conf still references retired repos")
    if not text.strip().endswith("FINAL,🐟 漏网之鱼") and "\nFINAL,🐟 漏网之鱼\n" not in text:
        _fail("missing FINAL 漏网之鱼")
    # 策略组：规则里用到的分组必须在 [Proxy Group] 定义
    groups = {ln.split(" = ", 1)[0] for ln in text.split("[Proxy Group]", 1)[1].split("[Rule]", 1)[0].splitlines() if " = " in ln}
    rule_part = text.split("[Rule]", 1)[1].split("\n[", 1)[0]
    for ln in rule_part.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        parts = [p.strip() for p in s.split(",")]
        pol = parts[1] if parts[0] == "FINAL" else (parts[2] if len(parts) > 2 else "")
        if pol and pol.upper() not in ("DIRECT", "REJECT", "PROXY", "REJECT-DICT", "REJECT-TINYGIF", "REJECT-ARRAY") \
                and pol not in groups and not pol.startswith("("):
            _fail(f"rule references undefined policy {pol!r}: {s[:100]}")


# ---------- 覆写 ----------

def test_adblock_providers() -> None:
    domains = yaml.safe_load(ADB_DOMAIN.read_text(encoding="utf-8")).get("payload") or []
    cidrs = yaml.safe_load(ADB_IP.read_text(encoding="utf-8")).get("payload") or []
    if len(domains) < 20000 or len(set(domains)) != len(domains):
        _fail(f"AdBlock_Domain.yaml count/dup wrong: {len(domains)}")
    for d in domains:
        if not isinstance(d, str) or "," in d or " " in d or d.startswith("*"):
            _fail(f"AdBlock_Domain.yaml bad entry: {d!r}")
    for c in cidrs:
        ipaddress.ip_network(c, strict=False)
    dset = set(domains)
    hit = [p for p in PROTECTED if p in dset or "+." + p in dset]
    if hit:
        _fail(f"AdBlock would block protected domains: {hit}")


def test_overwrites() -> None:
    mi = yaml.safe_load((ROOT / "overwrite" / "Clash_Mi_Merge.yaml").read_text(encoding="utf-8"))
    if mi["tun"]["strict-route"] is not False or mi["tun"]["stack"] != "system":
        _fail("Clash Mi tun must be strict-route=false, stack=system")
    if mi.get("ipv6") is not False or mi["dns"].get("ipv6") is not False:
        _fail("Clash Mi ipv6 must be false")
    if mi["dns"].get("fallback"):
        _fail("Clash Mi dns.fallback must be empty")
    rules = mi.get("prepend-rules") or []
    for r in ("RULE-SET,lc-adblock-domain,REJECT", "RULE-SET,lc-adblock-ip,REJECT,no-resolve"):
        if r not in rules:
            _fail(f"Clash Mi prepend-rules missing {r}")
    oc_text = (ROOT / "overwrite" / "LC_AdBlock.conf").read_text(encoding="utf-8")
    oc = yaml.safe_load(oc_text.split("[YAML]", 1)[1])
    for doc in (mi, oc):
        for name, prov in doc["rule-providers"].items():
            if not prov["url"].startswith(REPO_CDN + "overwrite/adblock/"):
                _fail(f"{name} url must point to this repo: {prov['url']}")
            local = ROOT / prov["url"][len(REPO_CDN):]
            if not local.is_file():
                _fail(f"{name} url target missing in repo: {local.relative_to(ROOT)}")


def main() -> None:
    for fn in (test_overlay_anchor_guard, test_clash_ini, test_dns_helpers, test_priority_us_appstore_and_unionpay,
               test_overlay_order_appletv_then_appstore, test_list_name_mapping, test_rewrite_general_doh,
               test_shadowrocket_conf, test_adblock_providers, test_overwrites):
        fn()
        print(f"ok  {fn.__name__}")
    print("tests: all passed")


if __name__ == "__main__":
    main()
