# -*- coding: utf-8 -*-
"""由 overwrite/Clash_Mi_Merge.yaml 生成 Clash Mi「JS 覆写」overwrite/Clash_Mi_Merge.js。

为什么需要 JS：Clash Mi 的 YAML 覆写只做「字典深合并、列表/标量整体替换」，
不认识 mihomo/Verge 的 prepend-rules（上游 KaringX/clashmi#460 已明确不支持，建议用 JS 覆写）。
所以 YAML 里的 prepend-rules 会被原样写进配置后被内核忽略，广告 REJECT、UDP 443 REJECT、
Synology/AnyDesk PROCESS-NAME 规则都不会生效。

JS 覆写语义与 YAML 覆写保持一致（字典深合并、其他整体替换），另外把 prepend-rules 插到 rules 最前面。
注意：find-process-mode 等「App 核心设置」仍会在 JS 之后再被 App 覆写（原始配置 <- 自定义覆写 <- App 覆写），
需要在每台机器 Clash Mi「核心设置 → 进程匹配模式」选 always。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "overwrite" / "Clash_Mi_Merge.yaml"
DST = ROOT / "overwrite" / "Clash_Mi_Merge.js"

TEMPLATE = """// Clash Mi JS 覆写（自动生成，请勿手改；源文件 overwrite/Clash_Mi_Merge.yaml，生成脚本 scripts/build_clashmi_js.py）
// 用法：Clash Mi「覆写」里新增 URL 覆写，类型选 js，地址填
//   https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/Clash_Mi_Merge.js
// 并在订阅设置里把覆写从 Clash_Mi_Merge.yaml 换成它。YAML 覆写不支持 prepend-rules，所以必须用 JS。
// 语义：与 YAML 覆写一致（字典深合并，列表/标量整体替换），另把 LC_PREPEND_RULES 插到 rules 最前。
var LC_PATCH = __PATCH__;
var LC_PREPEND_RULES = __PREPEND__;

function lcIsMap(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

function lcMerge(dst, src) {
  for (var k in src) {
    if (!Object.prototype.hasOwnProperty.call(src, k)) continue;
    if (lcIsMap(dst[k]) && lcIsMap(src[k])) {
      lcMerge(dst[k], src[k]);
    } else {
      dst[k] = JSON.parse(JSON.stringify(src[k]));
    }
  }
  return dst;
}

function main(config) {
  if (!lcIsMap(config)) config = {};
  lcMerge(config, LC_PATCH);
  var old = Array.isArray(config.rules) ? config.rules : [];
  var seen = {};
  var rules = [];
  var i;
  for (i = 0; i < LC_PREPEND_RULES.length; i++) {
    seen[LC_PREPEND_RULES[i]] = true;
    rules.push(LC_PREPEND_RULES[i]);
  }
  for (i = 0; i < old.length; i++) {
    if (!seen[old[i]]) rules.push(old[i]);
  }
  config.rules = rules;
  return config;
}
"""


def render() -> str:
    data = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    prepend = list(data.pop("prepend-rules", None) or [])
    if not prepend:
        raise SystemExit("[clashmi-js] prepend-rules empty in Clash_Mi_Merge.yaml")
    patch = json.dumps(data, ensure_ascii=False, indent=2)
    pre = json.dumps(prepend, ensure_ascii=False, indent=2)
    return TEMPLATE.replace("__PATCH__", patch).replace("__PREPEND__", pre)


def main() -> None:
    out = render()
    if "--check" in sys.argv:
        if not DST.is_file() or DST.read_text(encoding="utf-8") != out:
            raise SystemExit("[clashmi-js] overwrite/Clash_Mi_Merge.js is stale; run scripts/build_clashmi_js.py")
        print("[clashmi-js] up to date")
        return
    DST.write_text(out, encoding="utf-8")
    print(f"[clashmi-js] wrote {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
