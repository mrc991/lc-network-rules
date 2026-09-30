#!/usr/bin/env bash
# 端到端：用假节点 + clash/Custom_Clash.ini 走一遍 subconverter，再叠 Clash Mi 覆写，交给 mihomo -t 校验。
# 用法：SUBCONVERTER=/path/to/subconverter MIHOMO=/path/to/mihomo scripts/e2e_clash.sh
# 依赖：python3（带 pyyaml）、curl。不访问任何真实订阅，节点全部是假数据。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${SUBCONVERTER:?set SUBCONVERTER}"
: "${MIHOMO:?set MIHOMO}"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
SC_PID=""; HTTP_PID=""
cleanup() {
  [ -n "$SC_PID" ] && kill "$SC_PID" 2>/dev/null || true
  [ -n "$HTTP_PID" ] && kill "$HTTP_PID" 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT

# 1) 假订阅：每个地区至少一个节点，保证 url-test 分组非空
cat > "$WORK/nodes.yaml" <<'EOF'
proxies:
  - {name: "🇭🇰 香港 01", type: ss, server: 198.51.100.1, port: 443, cipher: aes-128-gcm, password: x}
  - {name: "🇺🇸 美国 01", type: ss, server: 198.51.100.2, port: 443, cipher: aes-128-gcm, password: x}
  - {name: "🇯🇵 日本 01", type: ss, server: 198.51.100.3, port: 443, cipher: aes-128-gcm, password: x}
  - {name: "🇸🇬 新加坡 01", type: ss, server: 198.51.100.4, port: 443, cipher: aes-128-gcm, password: x}
  - {name: "🇹🇼 台湾 01", type: ss, server: 198.51.100.5, port: 443, cipher: aes-128-gcm, password: x}
  - {name: "🇰🇷 韩国 01", type: ss, server: 198.51.100.6, port: 443, cipher: aes-128-gcm, password: x}
  - {name: "🇬🇧 英国 01", type: ss, server: 198.51.100.7, port: 443, cipher: aes-128-gcm, password: x}
EOF
# E2E_INI 可指定其他模板（用于新旧对比）；E2E_OUT 可保存订阅转换结果
cp "${E2E_INI:-$ROOT/clash/Custom_Clash.ini}" "$WORK/Custom_Clash.ini"

# 2) 本地起 HTTP 提供订阅与模板
HTTP_PORT=18081
(cd "$WORK" && exec "$PY" -m http.server "$HTTP_PORT" --bind 127.0.0.1 >/dev/null 2>&1) & HTTP_PID=$!
for _ in $(seq 1 30); do curl -fs "http://127.0.0.1:$HTTP_PORT/nodes.yaml" >/dev/null 2>&1 && break; sleep 1; done

# 3) 起 subconverter：复制到临时目录，只监听本机；放开 ruleset 数量限制
#    默认 max_allowed_rulesets=64，本模板约 150 条，超限会静默回落到内置模板（生产后端同样需要放开）
cp -R "$(dirname "$SUBCONVERTER")" "$WORK/sc"
"$PY" - "$WORK/sc/pref.toml" <<'EOF'
import re, sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
for k, v in (("listen", '"127.0.0.1"'), ("max_allowed_rulesets", "0"), ("max_allowed_rules", "0")):
    s, n = re.subn(rf"(?m)^{k}\s*=.*$", f"{k} = {v}", s)
    assert n == 1, k
open(p, "w", encoding="utf-8").write(s)
EOF
(cd "$WORK/sc" && exec "./$(basename "$SUBCONVERTER")" >"$WORK/sc.log" 2>&1) & SC_PID=$!
for _ in $(seq 1 30); do curl -fs "http://127.0.0.1:25500/version" >/dev/null 2>&1 && break; sleep 1; done

enc() { "$PY" -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1],safe=""))' "$1"; }
SUB="$(enc "http://127.0.0.1:$HTTP_PORT/nodes.yaml")"
CFG="$(enc "http://127.0.0.1:$HTTP_PORT/Custom_Clash.ini")"
curl -fsS --max-time 300 -o "$WORK/sub.yaml" \
  "http://127.0.0.1:25500/sub?target=clash&url=$SUB&config=$CFG&new_name=true&expand=false"
if grep -q 'exceeded limit' "$WORK/sc.log"; then echo "[e2e] subconverter hit ruleset limit"; exit 1; fi
[ -n "${E2E_OUT:-}" ] && cp "$WORK/sub.yaml" "$E2E_OUT"

# 4) 叠 Clash Mi 覆写（prepend-rules / rule-providers / 顶层键合并），得到最终运行配置
"$PY" - "$WORK/sub.yaml" "$ROOT/overwrite/Clash_Mi_Merge.yaml" "$WORK/final.yaml" <<'EOF'
import sys, yaml
sub = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
mi = yaml.safe_load(open(sys.argv[2], encoding="utf-8"))
groups = {g["name"] for g in sub.get("proxy-groups", [])}
assert len(groups) >= 40, f"too few groups: {len(groups)}"
assert "🍎 App Store" in groups and "🎥 TV Box" in groups, "custom groups missing"
rules = sub.get("rules", [])
assert any(r.startswith("GEOIP,cn,") and r.endswith("no-resolve") for r in rules), "GEOIP,cn no-resolve missing"
for k, v in mi.items():
    if k == "prepend-rules":
        sub["rules"] = list(v) + sub.get("rules", [])
    elif k == "rule-providers":
        sub.setdefault("rule-providers", {}).update(v)
    elif isinstance(v, dict) and isinstance(sub.get(k), dict):
        sub[k].update(v)
    else:
        sub[k] = v
yaml.safe_dump(sub, open(sys.argv[3], "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
print(f"[e2e] groups={len(groups)} rules={len(sub['rules'])} providers={len(sub.get('rule-providers', {}))}")
EOF

# 5) mihomo 校验（会下载 geo 数据与 rule-provider）
"$MIHOMO" -d "$WORK/mihomo" -f "$WORK/final.yaml" -t
echo "[e2e] mihomo -t passed"
