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
