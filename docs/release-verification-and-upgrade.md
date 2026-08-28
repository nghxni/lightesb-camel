# 发布包验证、升级与回滚

本文只使用交付包内文件和随交付提供的 sidecar 证据，不依赖源码仓库。升级生产前仍需获得明确授权并按现场变更流程执行。

## 1. 收件检查

一个客户交付只对应一个 `deliveryId`。不要混用不同 deliveryId 的归档、manifest、JAR 或证据。

归档外如同时提供以下文件，先在同一目录执行：

```bash
sha256sum -c SHA256SUMS
```

sidecar 通常包含归档、`delivery-attestation.json`、`source-release-manifest.json` 和 `release-manifest.json` 的摘要。摘要失败时停止，不解压、不启动。

## 2. 解压后校验

在新的空目录解压，保留旧版目录不动。进入解压根目录后执行：

```bash
sha256sum -c lightesb-camel-<releaseVersion>.jar.sha256
sha256sum -c lightesb-cli.jar.sha256
```

确认以下文件存在：

- `lightesb-camel-<releaseVersion>.jar`
- `lightesb-cli.jar`
- `release-manifest.json`
- `source-release-manifest.json`
- `lightesb-camel-app/`
- `start.sh` / `start.bat`

`release-manifest.json` 只应描述当前 deliveryId。核对 `customerId`、`serial`、授权起止时间、数据库类型/版本和密钥编号；不应出现公司联系人、电话、打包密码、私钥或其他客户清单。

如果交付方同时提供可信公钥验签工具和公司留存公钥，必须执行离线水印验签，并确认 `customerId`、`serial`、授权期一致且 `signatureValid=true`。不要只依据 JAR 内嵌公钥做正式溯源。

## 3. 隔离启动验证

先在非生产端口和隔离数据目录启动候选。Linux/macOS 启动脚本支持：

```bash
export LIGHTESB_RELEASE_VERSION=<releaseVersion>
export LIGHTESB_CLASSFINAL_PASSWORD='<由交付方安全提供>'
./start.sh
```

密码只通过受控环境注入，不写入 manifest、文档、配置或日志。验证至少包括：

1. 应用正常启动，无授权、水印、fingerprint 或 ClassFinal 错误。
2. 路由加载状态与预期一致。
3. 关键管理命令/接口和一个代表性业务服务 smoke 通过。
4. 新版日志无未预期 ERROR，旧版数据未被候选误写。

## 4. 升级前备份

升级前保存并记录摘要：

- 当前运行包和版本。
- `lightesb-camel-app/` 服务目录及共享配置。
- 外部化配置、启动参数和环境变量清单（不把 secret 写进记录）。
- 数据库类型、当前 schema 版本、完整备份文件及 SHA-256。
- 恢复命令、验证入口和负责人。
- `project-experience/`（如存在）；发布升级不得删除或覆盖项目经验。

数据库升级脚本按版本顺序执行。备份为空、摘要不可复算或恢复入口未演练时，不执行数据库升级。

## 5. 执行升级

1. 完成新版离线校验和隔离启动验证。
2. 停止旧实例或按现场部署机制切走流量。
3. 保留旧版完整目录，新版解压到新目录；不要在旧目录上直接覆盖全部文件。
4. 合并经审核的现场配置和服务目录。发布基线文档/skills 可升级，`project-experience/` 必须保留并在升级后审核兼容性。
5. 按数据库版本记录执行必要升级，成功核验后才更新登记版本。
6. 启动新版，检查路由状态、日志、关键管理入口和业务 smoke。
7. 记录实际启用版本、时间、验证人和证据摘要。

正式服务部署优先使用交付包提供的管理 API 或 CLI；未获授权时不要远程写入、启停或修改生产服务目录。

## 6. 回滚

任一关键校验失败时停止后续升级：

1. 停止或隔离失败候选。
2. 恢复旧版完整目录、配置和服务目录。
3. 数据库发生变更时，从升级前备份恢复并复算摘要。
4. 启动旧版，复查路由、日志、管理入口和代表性业务服务。
5. 记录失败点和回滚结果；不要把部分升级状态登记为成功。

不要删除失败包或修改其 manifest/摘要。修复后应接收新的不可变候选，而不是覆盖原候选文件。
