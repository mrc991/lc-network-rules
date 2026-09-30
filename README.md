# lc-network-rules

LC 个人分流规则。上游原版 + 本仓库定制，由 GitHub Actions 每天自动构建。不含节点和密钥。

## 订阅地址

| 用途 | URL |
|------|-----|
| Clash 订阅转换模板（节点分流） | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/clash/Custom_Clash.ini` |
| Clash Mi 统一覆写 | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/Clash_Mi_Merge.yaml` |
| OpenClash 覆写模块 LC_AdBlock | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/overwrite/LC_AdBlock.conf` |
| Shadowrocket 配置（带广告拦截） | `https://testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/shadowrocket/Custom_Shadowrocket_whitelist_ad.conf` |

jsDelivr 有缓存，急用时把 `testingcf.jsdelivr.net/gh/mrc991/lc-network-rules@main/` 换成 `raw.githubusercontent.com/mrc991/lc-network-rules/main/`。

Shadowrocket：在「配置」页用 URL 下载后「使用配置」，不要加到首页订阅。

## 结构

```
custom/                  定制（手改这里）
  clash-overlay.yaml     对上游 Custom_Clash.ini 的插入/替换/URL 改写
  proxy_groups.ini       全部策略组（整体替换上游分组）
overwrite/
  Clash_Mi_Merge.yaml    Clash Mi 覆写（手改）
  LC_AdBlock.conf        OpenClash 覆写模块（手改）
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
3. `check_urls.py`：引用的外部规则列表不得 404
4. `e2e_clash.sh`：假节点 → subconverter → 叠 Clash Mi 覆写 → `mihomo -t`
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
