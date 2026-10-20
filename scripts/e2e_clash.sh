#!/usr/bin/env bash
# 端到端：用假节点 + clash/Custom_Clash.ini 走一遍 subconverter，再叠 Clash Mi 覆写（YAML 主用、JS 备用），交给 mihomo -t 校验。
# CLASHMI_WRITE=1：用展开后的订阅规则重建 overwrite/Clash_Mi_Merge.yaml（CI 用）。
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
# 发布包只带 pref.example.toml，pref.toml 首次运行才生成
[ -f "$WORK/sc/pref.toml" ] || cp "$WORK/sc/pref.example.toml" "$WORK/sc/pref.toml"
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
# 3a) expand=false：规则集以 rule-provider 引用（给 JS 覆写校验用，体积小）
curl -fsS --max-time 300 -o "$WORK/sub.yaml" \
  "http://127.0.0.1:25500/sub?target=clash&url=$SUB&config=$CFG&new_name=true&expand=false"
# 3b) 不带 expand 参数（subconverter 默认展开）：与真实订阅后端（CF-Workers-SUB → subconverter）一致，规则逐条内联
curl -fsS --max-time 300 -o "$WORK/sub_expanded.yaml" \
  "http://127.0.0.1:25500/sub?target=clash&url=$SUB&config=$CFG&new_name=true"
if grep -q 'exceeded limit' "$WORK/sc.log"; then echo "[e2e] subconverter hit ruleset limit"; exit 1; fi
[ -n "${E2E_OUT:-}" ] && cp "$WORK/sub_expanded.yaml" "$E2E_OUT"

"$PY" - "$WORK/sub.yaml" "$WORK/sub_expanded.yaml" <<'EOF'
import sys, yaml
for f in sys.argv[1:]:
    sub = yaml.safe_load(open(f, encoding="utf-8"))
    groups = {g["name"] for g in sub.get("proxy-groups", [])}
    assert len(groups) >= 40, f"{f}: too few groups: {len(groups)}"
    assert "🍎 App Store" in groups and "🎥 TV Box" in groups, f"{f}: custom groups missing"
    rules = sub.get("rules", [])
    assert any(r.startswith("GEOIP,cn,") and r.endswith("no-resolve") for r in rules), f"{f}: GEOIP,cn no-resolve missing"
EOF

# 4) Clash Mi YAML 覆写（客户端实际订阅的 overwrite/Clash_Mi_Merge.yaml）
#    CLASHMI_WRITE=1 时先用刚展开的订阅规则重建该文件（CI 用）
if [ "${CLASHMI_WRITE:-0}" = "1" ]; then
  "$PY" "$ROOT/scripts/build_clashmi_yaml.py" --sub "$WORK/sub_expanded.yaml"
fi
#    按 Clash Mi 的 YAML 覆写语义合并（字典深合并，列表/标量整体替换）
"$PY" - "$WORK/sub_expanded.yaml" "$ROOT/overwrite/Clash_Mi_Merge.yaml" "$ROOT/custom/Clash_Mi_Merge.src.yaml" "$WORK/final_yaml.yaml" "${CLASHMI_WRITE:-0}" <<'EOF'
import sys, copy, yaml
sub = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
mi = yaml.safe_load(open(sys.argv[2], encoding="utf-8"))
src = yaml.safe_load(open(sys.argv[3], encoding="utf-8"))
fresh = sys.argv[5] == "1"
pre = src["prepend-rules"]

def merge(dst, patch):
    for k, v in patch.items():
        if isinstance(dst.get(k), dict) and isinstance(v, dict):
            merge(dst[k], v)
        else:
            dst[k] = copy.deepcopy(v)
    return dst

cfg = merge(copy.deepcopy(sub), mi)
rules = cfg["rules"]
assert "prepend-rules" not in mi, "generated overwrite must not carry prepend-rules"
assert rules[:len(pre)] == pre, "Clash Mi YAML overwrite: rules do not start with prepend-rules"
assert len(rules) == len(set(rules)), "duplicate rules in Clash Mi YAML overwrite"
if fresh:
    expect = pre + [r for r in sub["rules"] if r not in set(pre)]
    assert rules == expect, "Clash Mi YAML overwrite rules != prepend + expanded subscription rules"
assert cfg["proxies"] == sub["proxies"], "proxies changed by overwrite"
assert cfg["proxy-groups"] == sub["proxy-groups"], "proxy-groups changed by overwrite"
assert cfg.get("find-process-mode") == "always", "find-process-mode not always"
for name in src["rule-providers"]:
    assert name in cfg.get("rule-providers", {}), f"rule-provider {name} missing"

groups = {g["name"] for g in cfg["proxy-groups"]} | {"DIRECT", "REJECT", "REJECT-DROP", "PASS", "COMPATIBLE"}
providers = set(cfg.get("rule-providers", {}))
def target(rule):
    if rule.split(",", 1)[0] in ("AND", "OR", "NOT"):
        depth = 0
        for i, ch in enumerate(rule):
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0 and ch == ")":
                return rule[i + 2:].split(",")[0]
    parts = rule.split(",")
    return parts[1] if parts[0] == "MATCH" else parts[2]
bad = [r for r in rules if target(r) not in groups]
assert not bad, f"rules target unknown groups: {bad[:5]}"
missing = [r for r in rules if r.startswith("RULE-SET,") and r.split(",")[1] not in providers]
assert not missing, f"RULE-SET without provider: {missing[:5]}"
assert rules[-1].startswith("MATCH,"), "last rule must be MATCH"
yaml.safe_dump(cfg, open(sys.argv[4], "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
print(f"[e2e] yaml-overwrite: subscription={len(sub['rules'])} prepend={len(pre)} total={len(rules)} groups={len(cfg['proxy-groups'])}")
EOF
"$MIHOMO" -d "$WORK/mihomo" -f "$WORK/final_yaml.yaml" -t
echo "[e2e] mihomo -t passed (YAML overwrite, Clash Mi merge semantics)"

# 5) 备用 JS 覆写（overwrite/Clash_Mi_Merge.js），用 node 跑与 Clash Mi 相同的 main() 入口
"$PY" -c 'import sys,json,yaml; json.dump(yaml.safe_load(open(sys.argv[1],encoding="utf-8")),open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False)' "$WORK/sub.yaml" "$WORK/sub.json"
node -e '
const fs = require("fs");
const src = fs.readFileSync(process.argv[1], "utf8");
const main = new Function(src + "\nreturn main;")();
const out = main(JSON.parse(fs.readFileSync(process.argv[2], "utf8")));
fs.writeFileSync(process.argv[3], JSON.stringify(out));
' "$ROOT/overwrite/Clash_Mi_Merge.js" "$WORK/sub.json" "$WORK/final.json"
"$PY" - "$ROOT/custom/Clash_Mi_Merge.src.yaml" "$WORK/final.json" "$WORK/final.yaml" <<'EOF'
import sys, json, yaml
mi = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
cfg = json.load(open(sys.argv[2], encoding="utf-8"))
pre = mi["prepend-rules"]
assert cfg["rules"][:len(pre)] == pre, "JS overwrite did not prepend rules"
assert cfg.get("find-process-mode") == "always", "find-process-mode not always after JS overwrite"
for name in mi["rule-providers"]:
    assert name in cfg.get("rule-providers", {}), f"rule-provider {name} missing after JS overwrite"
assert "prepend-rules" not in cfg, "prepend-rules key leaked into final config"
yaml.safe_dump(cfg, open(sys.argv[3], "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
print(f"[e2e] js-overwrite: rules={len(cfg['rules'])} providers={len(cfg.get('rule-providers', {}))} prepend={len(pre)}")
EOF
"$MIHOMO" -d "$WORK/mihomo" -f "$WORK/final.yaml" -t
echo "[e2e] mihomo -t passed (JS overwrite)"
