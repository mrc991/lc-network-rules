# lc-network-rules

LC 个人分流规则。上游原版 + 本仓库定制，由 GitHub Actions 每天自动构建。不含节点和密钥。

## 订阅地址

| 用途 | URL |
|------|-----|
| Clash 订阅转换模板（节点分流） | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/clash/Custom_Clash.ini` |
| Clash Mi 覆写（YAML，客户端用这个，含完整 rules） | `https://raw.githubusercontent.com/mrc991/lc-network-rules/main/overwrite/Clash_Mi_Merge.yaml` |
| Clash Mi JS 覆写（备用，一般不用） | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/Clash_Mi_Merge.js` |
| OpenClash 覆写模块 LC_AdBlock | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/LC_AdBlock.conf` |
| OpenClash 覆写模块 LC_AnyDesk | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/LC_AnyDesk.conf` |
| Shadowrocket 配置（带广告拦截） | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/shadowrocket/Custom_Shadowrocket_whitelist_ad.conf` |

jsDelivr 有缓存，急用时把 `testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/` 换成 `raw.githubusercontent.com/mrc991/lc-network-rules/main/`。

Shadowrocket：在「配置」页用 URL 下载后「使用配置」，不要加到首页订阅。

## 结构

```
custom/                  定制（手改这里）
  Clash_Mi_Merge.src.yaml  Clash Mi 覆写源文件（prepend-rules + DNS/TUN 等）
  clash-overlay.yaml     对上游 Custom_Clash.ini 的插入/替换/URL 改写
  proxy_groups.ini       全部策略组（整体替换上游分组）
overwrite/
  Clash_Mi_Merge.yaml    Clash Mi 覆写（生成：前置规则 + 展开后的完整订阅规则，scripts/build_clashmi_yaml.py）
  Clash_Mi_Merge.js      Clash Mi 备用 JS 覆写（生成，scripts/build_clashmi_js.py）
  LC_AdBlock.conf        OpenClash 覆写模块（手改）
  LC_AnyDesk.conf        OpenClash AnyDesk 域名直连覆写（手改）
  openclash_fake_filter_anydesk.snippet  路由 fake-ip-filter 片段（手改）
  adblock/               广告 rule-provider（生成）
clash/                   Custom_Clash.ini（生成）
shadowrocket/            Shadowrocket 配置（生成）
upstream.lock            本次产物使用的上游 commit（生成）
scripts/                 构建与测试
```

生成物不要手改，下次构建会被覆盖。

## 上游

- [Aethersailor/Custom_OpenClash_Rules](https://github.com/Aethersailor/Custom_OpenClash_Rules) `main`：`cfg/Custom_Clash.ini` 及其引用的规则列表
- [Johnshall/Shadowrocket-ADBlock-Rules-Forever](https://github.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever) `release`：`sr_top500_whitelist_ad.conf`（广告拦截 + 国内白名单）
- Shadowrocket 端 GEOSITE 映射到 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)

## 自动化

`.github/workflows/build.yml`：每天北京时间 04:00、手动触发、改动 `custom/`/覆写/脚本时运行。

1. 按 commit sha 拉取上游，套用 `custom/`，生成三类产物
2. `tests.py`：分流不变量（`GEOIP,cn,no-resolve`、个人规则顺序、DNS 防泄漏、App Store/云闪付等）
3. `check_urls.py`：引用的外部规则列表不得 404（jsDelivr 偶发 404 时以 raw.githubusercontent 为准，仅警告）
4. `e2e_clash.sh`：假节点 → subconverter（与线上相同的展开方式）→ 重建 `overwrite/Clash_Mi_Merge.yaml` 的 rules（前置规则 + 订阅规则去重）→ 按 Clash Mi 方式合并（字典深合并、列表整体替换）→ 校验规则开头/总数/无重复/策略组与节点不变/每条规则目标存在 → `mihomo -t`；再用 node 跑备用 JS 覆写 → `mihomo -t`
5. 全部通过且产物有变化才提交并刷新 jsDelivr；任一步失败不提交，自动开 issue

`clash-overlay.yaml` 的每个锚点必须在上游恰好出现一次。上游改动导致锚点失效时构建失败，线上保持上一版，按 issue 修 overlay 即可。

## 本地构建

```bash
pip install pyyaml
python scripts/build.py && python scripts/tests.py
```

`LC_UPSTREAM_CLASH_INI` / `LC_UPSTREAM_JOHNSHALL` 可指向本地文件，离线调试。

## 注意

- 订阅转换后端需放开 `max_allowed_rulesets`（本模板约 150 条，subconverter 默认 64，超限会静默回落到内置模板）。
- 防 DNS 泄漏：国内 IP 兜底必须 `GEOIP,cn,no-resolve`；Shadowrocket 所有 IP 规则强制 `no-resolve`。
- `jsdelivr.net/com` 必须在上游直连表之前走 `🚀 手动选择`（国内直连被 RST）。
- 美区 App Store 走 `🍎 App Store`（默认美国节点），排在 AppleTV+ 之后、苹果中国之前。
- Clash Mi 的 YAML 覆写只做字典深合并、列表整体替换，不认识 `prepend-rules`（KaringX/clashmi#460）。所以 `overwrite/Clash_Mi_Merge.yaml` 由 CI 生成完整 `rules:`：先放 `custom/Clash_Mi_Merge.src.yaml` 的前置规则，再接 subconverter 展开的完整订阅规则（去掉完全重复项），整体替换订阅的 rules。改规则请改 `custom/Clash_Mi_Merge.src.yaml` 或 `custom/` 下的模板，CI 每天重建。注意：订阅模板改了而覆写还没重建时，客户端用的是覆写里的旧订阅规则（最多差一天，或手动触发 CI）。
- `find-process-mode` 会被 App「核心设置 → 进程匹配模式」覆盖（原始配置 <- 自定义覆写 <- App 覆写），每台机器需在 App 里设为 always。

### Clash Mi 客户端操作（公司 Mac / BIGRICH-OFFICE / BIGRICH-HOME 各做一次）

1. 「覆写」页：找到远程覆写 `.../overwrite/Clash_Mi_Merge.yaml`（地址用 raw.githubusercontent，见上表），点「更新」（不更新也会每 24 小时自动更新）。
2. 「设置 → 核心设置 → 进程匹配模式」设为 `always`。
3. 首页「重新连接」（会重建 TUN，断网几秒）。
4. 检查：连接/规则里能看到 `RULE-SET,lc-adblock-domain,REJECT` 等前置规则排在最前；`AnyDesk` 进程命中 `ProcessName` → `DIRECT`。

回滚：GitHub 上 revert 本次提交（或把覆写换回旧版本），在 App 里更新覆写；进程匹配模式改回 `off`；再「重新连接」。临时救急可在 App 里取消该订阅的覆写后重新连接。
- AnyDesk（Clash Mi）：在 `custom/Clash_Mi_Merge.src.yaml`：`PROCESS-NAME,AnyDesk` / `AnyDesk.exe` 与四个 `DOMAIN-SUFFIX` 都走 `DIRECT`，并写入 `dns.fake-ip-filter`。`find-process-mode` 为 `always`，否则进程规则不生效。域名规则盖不住打洞用的裸 IP。
- **常设：**改 GitHub 订阅或 Clash Mi 覆写时，家用路由 MT6000 上的 OpenClash **不会**自动跟着生效。必须把同一意图推到路由，尤其是 `openclash_custom_fake_filter.list` 和 AnyDesk 的 DIRECT 规则。更新订阅 ≠ 更新 Fake-IP 名单。
- AnyDesk（家里路由 OpenClash / GL-MT6000）：规则走 `overwrite/LC_AnyDesk.conf`（+rules DIRECT）或 `custom/clash-overlay.yaml` → Custom_Clash.ini；**Fake-IP 必须**写入路由 `openclash_custom_fake_filter.list`（见 `overwrite/openclash_fake_filter_anydesk.snippet`），否则中继仍会解析成 198.18.x。验证：`boot.net.anydesk.com` / `anydesk.com` 不得为 198.18；连接出口应为 DIRECT。
- Clash Mi 更新远程覆写并重新应用配置后，检查实际生效规则和连接：AnyDesk 应命中 `DomainSuffix`，出口为 `DIRECT`。
- HomeBistro（家里访问 / 局域网识别）：`custom/Clash_Mi_Merge.src.yaml` 前置 `DOMAIN,homebistro.bigrich.cc,DIRECT`，让 Cloudflare 看到家庭公网出口；应用侧靠 `/api/net/beacon` + `/api/net/hint` 判断「是否在家」并自动跳到局域网地址。家里路由 MT6000 的 `openclash_custom_rules.list` 有同一条（2026-10-24 加）。代理出口 IP（45.62.118.67 / 192.210.136.225）在应用侧被排除，避免在外网被误判。
