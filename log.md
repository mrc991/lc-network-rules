## 2026-10-01

- 任务目标：将 Clash Mi AnyDesk 分流改为只靠域名、零进程匹配，并让 Fake-IP 模式下也能按域名命中。
- 分支名：`fix/anydesk-domain-only`
- 修改文件：`overwrite/Clash_Mi_Merge.yaml`、`README.md`、`log.md`
- 改动内容与原因：删除 AnyDesk 的两条 `PROCESS-NAME` 规则；加入 `anydesk.com`、`net.anydesk.com`、`anydesk.com.cn`、`net.anydesk.com.cn` 的 `DOMAIN-SUFFIX → DIRECT`；将相同后缀加入 `dns.fake-ip-filter`；保留 Synology Drive 等其它进程规则。
- 验证命令及结果：`python3 scripts/tests.py` 全部通过；`git diff --check` 通过；独立 YAML/差异核验确认四个域名规则和四个 Fake-IP 后缀各出现一次，且非 AnyDesk 配置未变化。
- 是否已推送远端：尚未推送。
- 跨仓库联动影响：无其它仓库改动；推送后使用本仓库远程覆写的各端需刷新并重新应用配置。
- 本机验证限制：读取公司 Mac Mini 的 Clash Mi 沙盒返回 `Operation not permitted`，未绕过权限；尚未刷新本机覆写、检查或修改 `find-process-mode`、取得实际 connections 域名命中证据。上面的域名匹配为静态配置核验，不代表本机实流命中。
- 修改期间工具错误：`apply_patch` 不存在，未产生写入，改用精确编辑工具；首次追加 `log.md` 返回 ENOENT（远端无此文件），随后新建日志。未修改任何既有脚本。
