## 2026-11-03（Apple Pay / 钱包 / 银联直连与 Fake-IP 过滤）

- **任务目标**：修复 iPhone 在 Wi-Fi 下 Apple Pay / 钱包支付频繁卡顿超时、必须断开 Wi-Fi 才能成功的问题。
- **分支名**：main
- **修改文件**：
  - custom/clash-overlay.yaml：Custom_Clash.ini 中补充 Apple Pay 核心通信域名强制直连
  - custom/Clash_Mi_Merge.src.yaml：
    - prepend-rules 增加 Apple Pay 与银联域名 DIRECT
    - dns.fake-ip-filter 增加 Apple Pay 与银联核心域名真实 IP 解析
    - sniffer.skip-domain 增加 Apple 支付与推送域名，避免 TLS SNI 目的重写破坏 mTLS
  - scripts/sr_base.py：Shadowrocket skip-proxy 与 priority_direct_rules() 同步补齐 Apple Pay
  - scripts/tests.py：新增 Apple Pay 规则与 Fake-IP / Sniffer 断言
- **验证命令及结果**：python scripts/build.py 生成物同步；python scripts/tests.py 全部 10 项通过。
- **是否已推送远端**：本条随 push 提交。
- **跨仓库联动影响**：工作区 9.tools/GitHub/lc-network-rules/ 与 README.md 同步；家用路由 MT6000 需写入对应 fake-ip-filter 与 openclash_custom_rules.list。

## 2026-10-20（Clash Mi YAML 覆写带完整 rules；修 CI #6）

- 任务目标：Clash Mi 的 YAML 覆写不认识 `prepend-rules`（列表整体替换），前置规则在客户端不生效。改为 CI 生成完整 `rules:`：前置 23 条 + subconverter 展开的完整订阅规则（去重）。同时修 issue #6（jsDelivr 对 CI 偶发 404）。
- 分支名：`main`
- 修改文件：`custom/Clash_Mi_Merge.src.yaml`（由 `overwrite/Clash_Mi_Merge.yaml` 移来，手改源）、`overwrite/Clash_Mi_Merge.yaml`（改为生成物）、`overwrite/Clash_Mi_Merge.js`、`scripts/build_clashmi_yaml.py`（新增）、`scripts/build_clashmi_js.py`、`scripts/build.py`、`scripts/tests.py`、`scripts/check_urls.py`、`scripts/e2e_clash.sh`、`.github/workflows/build.yml`、`README.md`、`log.md`
- 改动内容与原因：e2e 用与线上相同的 subconverter 展开（expand 默认）生成订阅，CLASHMI_WRITE=1 时重建覆写 rules；按 Clash Mi 方式合并后断言：开头为前置规则、总数=前置+订阅去重、无重复、节点与策略组不变、每条规则目标存在、RULE-SET 有 provider、末条 MATCH，再 `mihomo -t`。check_urls：jsDelivr 404 时以 raw.githubusercontent 为准，仅警告（#6 三个地址实测均 200，属 CDN 偶发）。
- 验证命令及结果：本地 build.py / tests.py / check_urls.py（61 条 OK）/ e2e（YAML 与 JS 两条路径 `mihomo -t` 均通过）。用公司 Mac 上真实订阅（1180 条）按 Clash Mi 方式合并：生成规则与真实订阅去重结果完全一致，1203 条、0 重复、0 无效目标，`mihomo -t` 通过。
- 是否已推送远端：本条随 push 提交。
- 跨仓库联动影响：只有 Clash Mi 客户端读取 `overwrite/Clash_Mi_Merge.yaml`（OpenClash 用 LC_AdBlock.conf，Shadowrocket 由 Custom_Clash.ini 生成）。各端需在 App 更新覆写、进程匹配模式设 always、重新连接。

## 2026-10-02（Clash Mi 恢复 AnyDesk 进程直连）

- 任务目标：裸 IP 打洞不吃域名规则。Clash Mi 覆写加回 `PROCESS-NAME,AnyDesk` / `AnyDesk.exe` → DIRECT，并把 `find-process-mode` 设为 `always`。路由 Fake-IP 名单当天已核过，未再改路由。
- 分支名：`main`
- 修改文件：`overwrite/Clash_Mi_Merge.yaml`、`scripts/tests.py`、`README.md`、`log.md`
- 改动内容与原因：域名 DIRECT 留着；进程规则放在域名规则前。README 写明家用 MT6000 不会随订阅/覆写自动更新，Fake-IP 名单要单独推。
- 验证命令及结果：`python3 scripts/tests.py` 全部通过；`git diff --check` 通过。公司 Mac Clash Mi API 仍 401，覆写未在本机应用。
- 是否已推送远端：本条随 push 提交。
- 跨仓库联动影响：无。各端 Clash Mi 需手动更新并重新应用覆写后，进程规则才会生效。

## 2026-10-01（路由 OpenClash AnyDesk）

- 任务目标：家里 GL-MT6000 OpenClash（非 PC Clash Mi）为 AnyDesk 增加仅域名 DIRECT + fake-ip-filter，消除 198.18 Fake-IP。
- 分支名：`main`（直接提交）
- 修改文件：`custom/clash-overlay.yaml`、`overwrite/LC_AnyDesk.conf`（新建）、`overwrite/openclash_fake_filter_anydesk.snippet`（新建）、`README.md`、`log.md`
- 路由实改（BIGRICH-HOME → 192.168.8.1）：
  - 备份后写入 `/etc/openclash/custom/openclash_custom_fake_filter.list` 四条 `+.anydesk*`
  - 写入 `/etc/openclash/custom/openclash_custom_rules.list` 四条 `DOMAIN-SUFFIX → DIRECT`
  - `/etc/init.d/openclash restart`；flush DNS/Fake-IP 缓存
- 验证：运行 `cc.yaml` 含 filter 与规则；`nslookup boot.net.anydesk.com. 192.168.8.1` / `anydesk.com.` 为真实 IP（非 198.18）；`anydesk.com.cn.` → 119.0.68.13。未改公司 Mac。
- 是否已推送远端：本条随 push 提交。

## 2026-10-01

- 任务目标：将 Clash Mi AnyDesk 分流改为只靠域名、零进程匹配，并让 Fake-IP 模式下也能按域名命中。
- 分支名：`fix/anydesk-domain-only`
- 修改文件：`overwrite/Clash_Mi_Merge.yaml`、`README.md`、`log.md`
- 改动内容与原因：删除 AnyDesk 的两条 `PROCESS-NAME` 规则；加入 `anydesk.com`、`net.anydesk.com`、`anydesk.com.cn`、`net.anydesk.com.cn` 的 `DOMAIN-SUFFIX → DIRECT`；将相同后缀加入 `dns.fake-ip-filter`；保留 Synology Drive 等其它进程规则。
- 验证命令及结果：`python3 scripts/tests.py` 全部通过；`git diff --check` 通过；独立 YAML/差异核验确认四个域名规则和四个 Fake-IP 后缀各出现一次，且非 AnyDesk 配置未变化。
- 是否已推送远端：已推送到 `main`，commit `1e4642e767d390591a025c1d9b7251d42d1d50c4`；GitHub Actions Build rules 成功，包含 `mihomo -t` 端到端校验；jsDelivr 缓存已刷新。
- 跨仓库联动影响：无其它仓库改动；使用本仓库远程覆写的各端需刷新并重新应用配置。
- 本机验证限制：读取公司 Mac Mini 的 Clash Mi 沙盒返回 `Operation not permitted`，本地管理 API 返回 `401 Unauthorized`，未绕过权限、未读取凭证；因此尚未刷新本机覆写、检查或修改 `find-process-mode`、取得实际 connections 域名命中证据。GitHub raw 和 testingcf jsDelivr 的静态配置均已验证 `.com.cn` 规则存在；这不代表本机实流已命中。
- 修改期间工具错误：`apply_patch` 不存在，未产生写入，改用精确编辑工具；首次追加 `log.md` 返回 ENOENT（远端无此文件），随后新建日志。未修改任何既有脚本。


## 2026-11-09（香港节点改为 select & 黄果短剧域名走代理）

- **任务目标**：
  1. 将分流规则中的「🇭🇰 香港节点」策略组由 url-test 改为 select。
  2. 修复黄果短剧视频/图片资源无法加载问题：将 drleao.cn 与 hzjvlo.cn 加到分流规则前置（走 🚀 手动选择），规避境内 SNI 阻断与公共 DNS 投毒。
- **分支名**：main
- **修改文件**：
  - custom/proxy_groups.ini：香港节点类型 url-test 改为 select。
  - custom/clash-overlay.yaml：增加 drleao.cn 与 hzjvlo.cn 走 🚀 手动选择。
  - custom/Clash_Mi_Merge.src.yaml：prepend-rules 增加对应规则。
  - 产物重构：clash/Custom_Clash.ini、overwrite/Clash_Mi_Merge.yaml、overwrite/Clash_Mi_Merge.js、shadowrocket/Custom_Shadowrocket_whitelist_ad.conf。
- **验证命令及结果**：python scripts/build.py 成功重构；python scripts/tests.py 全部 10 项测试 passed。
- **是否已推送远端**：是（随本次 commit 推送）。


## 2026-11-17（c.ha.zdz.plus 直连分流与 Fake-IP 过滤）

- **任务目标**：将 `c.ha.zdz.plus` 加入直连规则与 Fake-IP 白名单，避免被代理转发或分配 Fake-IP。
- **分支名**：`feat/direct-c-ha-zdz-plus`
- **修改文件**：
  - `custom/Clash_Mi_Merge.src.yaml`：`prepend-rules` 增加 `DOMAIN,c.ha.zdz.plus,DIRECT`，`dns.fake-ip-filter` 增加 `c.ha.zdz.plus`。
  - `custom/clash-overlay.yaml`：在自定义规则段增加 `ruleset=🎯 全球直连,[]DOMAIN,c.ha.zdz.plus`。
  - `scripts/tests.py`：补充 `c.ha.zdz.plus` 的 Clash ini、Shadowrocket 配置、Clash Mi `prepend-rules` 与 `fake-ip-filter` 断言。
  - 产物重构：`clash/Custom_Clash.ini`、`overwrite/Clash_Mi_Merge.yaml`、`overwrite/Clash_Mi_Merge.js`、`shadowrocket/Custom_Shadowrocket_whitelist_ad.conf`。
- **验证命令及结果**：`python scripts/build.py` 与 `python scripts/tests.py` 全部通过（10 项测试 passed）。
- **是否已推送远端**：是（推送至功能分支 `feat/direct-c-ha-zdz-plus` 并创建 PR，待合入 `main`）。

## 2026-11-17（美国节点改为 select）

- **任务目标**：将分流策略组中的「🇺🇸 美国节点」由 `url-test` 改为 `select`（与「🇭🇰 香港节点」一致）。
- **分支名**：`feat/us-group-select`
- **修改文件**：
  - `custom/proxy_groups.ini`：`🇺🇸 美国节点` 由 `url-test` 改为 `select`，去掉测速 URL 与间隔参数。
  - `scripts/tests.py`：在 Clash ini 与 Shadowrocket 断言中补充 `🇺🇸 美国节点` 必须为 `select` 且不含 `url-test`。
  - 产物重构：`clash/Custom_Clash.ini`、`shadowrocket/Custom_Shadowrocket_whitelist_ad.conf` 等生成产物。
- **验证命令及结果**：`python scripts/build.py` 与 `python scripts/tests.py` 全部通过（10 项测试 passed）。
- **是否已推送远端**：是（推送至功能分支 `feat/us-group-select` 并创建 PR）。

## 2026-11-20（awswaf.com 加入 Crypto 分流）

- **任务目标**：将 `DOMAIN-SUFFIX,awswaf.com,📈 Crypto` 加入 Clash 分流与覆写规则。
- **分支名**：`feat/crypto-awswaf`
- **修改文件**：
  - `custom/clash-overlay.yaml`：在 `ruleset=📈 Crypto,[]GEOSITE,category-cryptocurrency` 后新增 `ruleset=📈 Crypto,[]DOMAIN-SUFFIX,awswaf.com`。
  - `custom/Clash_Mi_Merge.src.yaml`：`prepend-rules`（广告拦截 `RULE-SET` 之前）新增 `DOMAIN-SUFFIX,awswaf.com,📈 Crypto`；不加入 `dns.fake-ip-filter`。
  - `scripts/tests.py`：在 `test_clash_ini`、`test_shadowrocket_conf`、`test_overwrites` 补充 `awswaf.com` → `📈 Crypto` 断言。
  - 产物重构：`clash/Custom_Clash.ini`、`overwrite/Clash_Mi_Merge.yaml`、`overwrite/Clash_Mi_Merge.js`、`shadowrocket/Custom_Shadowrocket_whitelist_ad.conf`。
- **改动内容与原因**：使 `awswaf.com` 及其子域名在 Clash Mi、订阅模板（`Custom_Clash.ini`）与 Shadowrocket 中均命中 `📈 Crypto` 策略组（而非走直连或漏网之鱼）。
- **验证命令及结果**：`python3 scripts/build.py` 成功构建；`python3 scripts/tests.py` 全部 10 项测试通过（`tests: all passed`）；`git diff --check` 无异常；已校验生成物中规则存在性、前置顺序、无重复与未加入 `fake-ip-filter`。
- **是否已推送远端**：随本分支提交推送至 `feat/crypto-awswaf` 并创建 PR。
- **跨仓库联动影响**：无（Shadowrocket 产物已由同仓 `build.py` 同步生成）。
- **可迁移经验**：无


## 2026-11-23（新增自建节点自动测速组 `🏠 自建节点`）

- 任务目标：在 Clash 模板中新增 `🏠 自建节点` 自动测速组（`url-test`），仅包含 BWG 3 个、SJ 3 个、CC 3 个共 9 个自建节点，排在 `🔀 非标端口` 之后、`🇭🇰 香港节点` 之前，供 HomeBistro 日历推送等需绕开机场 22 端口限制的场景全自动选路。
- 分支名：`feat/self-hosted-proxy-group`（快进合入 `main`）。
- 修改文件：`custom/proxy_groups.ini`、`log.md`（追加本节）。
- 改动内容与原因：在 `custom/proxy_groups.ini` 中 `🔀 非标端口` 与 `🇭🇰 香港节点` 之间新增 `custom_proxy_group=🏠 自建节点`（`url-test`，正则 `(bwg|BWG|\brn\b|\bRN\b|gabriel|Gabriel)`，测速地址 `https://cp.cloudflare.com/generate_204`，间隔 300s，容差 50ms）。
- 验证命令及结果：推送至 `origin/main` 触发 `build.yml` 全套校验（`tests.py` + `check_urls.py` + `e2e_clash.sh` + `mihomo -t`）并同步刷新 MT6000 OpenClash 订阅核验 9 个节点全命中且无误命中。
- 是否已推送远端：是（`feat/self-hosted-proxy-group` 与 `main`）。
- 跨仓库联动影响：MT6000 `/etc/openclash/custom/openclash_custom_rules.list` 中 HomeBistro 的 SCP 代理规则目标由单节点 `🇺🇸 US SJ rn HY2` 改为 `🏠 自建节点`。
- 可迁移经验：[Cue: 需要对 SSH/22 端口做自动测速容灾且同时订阅了机场节点] -> [Lesson: 机场共享节点常封禁或限流 22 端口导致全量 `url-test` 选出不可用节点，应单独设立仅匹配自建节点的 `url-test` 组]
