---
name: lightesb-release-verification
description: Verify, upgrade, and roll back a delivered LightESB package using its manifests, checksums, isolated startup, backups, and customer-specific evidence. Use for package receipt checks, pre-upgrade validation, field upgrade planning, or rollback.
---

# LightESB 发布包验证与升级

## 先读

- `docs/release-verification-and-upgrade.md`
- `docs/runtime-configuration-reference.md`
- 涉及 CLI 部署或状态检查时读 `docs/cli/README.md`

## 执行边界

- 一次只处理一个 `deliveryId`；不混用其他客户的 manifest、JAR 或证据。
- 先校验 `SHA256SUMS`、runtime/CLI `.sha256` 和 manifest 客户字段，再解压/启动。
- 候选在新目录、非生产端口和隔离数据下验证；没有明确授权不启停生产、不远程写入、不修改生产服务目录或数据库。
- 打包密码只通过受控环境注入，不写入文档、配置、manifest 或日志。
- 升级前保留旧包、服务目录、配置、数据库备份及摘要；`project-experience/` 不删除、不覆盖。
- 失败立即停止并从旧包/备份回滚；不修改失败候选，等待新的不可变候选。

## 完成标准

- 摘要、水印、客户字段、隔离启动、路由状态和代表性 smoke 均通过。
- 升级/回滚步骤、备份摘要和残余风险已记录。
- 只有用户明确授权后才执行生产变更。
