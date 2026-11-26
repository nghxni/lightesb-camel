# 部署管理 API

本文档面向第三方运维平台、自动化脚本和交付现场排障，说明部署历史、详情日志和回退接口。

## 接口总览

BasePath：`/api/deployment`

| 能力 | Method | Endpoint | 说明 |
| --- | --- | --- | --- |
| 上传并部署 | POST | `/upload` | 上传服务包并执行部署 |
| 查询状态 | GET | `/status/{deploymentId}` | 查询单次部署状态 |
| 查询历史 | GET | `/history` | 查询部署和回退历史列表 |
| 查询详情 | GET | `/history/detail/{deploymentId}` | 查询部署详情和步骤日志 |
| 部署回退 | POST | `/rollback/{deploymentId}` | 撤销指定部署，恢复到该部署前的备份状态 |
| 仅验证 | POST | `/validate` | 校验服务包，不执行部署 |

部署和仅验证接口都会检查服务目录结构：

- 一个服务包只能包含一个服务目录和一个版本目录（`{serviceName}/{serviceVersion}/...`，或包根下直接是 `{serviceVersion}/...`）；多个服务或多个版本直接验证失败。
- 服务名只能包含字母、数字、下划线、中划线；版本目录必须是 `vX.Y.Z`。
- 版本目录必须包含 `service.config.properties`，并且恰好包含一个 `*.xml` 路由文件；缺少 XML 或存在多个 XML 时返回验证失败，不会复制服务文件或启动路由。

## 上传与解压边界

```bash
curl -X POST "http://localhost:8080/api/deployment/upload" \
  -F "file=@PlatformHttp-v3.0.0.zip" \
  -F "autoStart=true"
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `file` | 是 | `.zip`、`.tar.gz` 或 `.tgz` 服务包 |
| `autoStart` | 否 | 部署后是否启动路由，默认 `true` |
| `targetDirectory` | 否 | 已废弃；非空时返回 `400 TARGET_DIRECTORY_UNSUPPORTED` |

部署目标由 `lightesb.route.directory` 统一决定。服务端使用受控临时文件名，并拒绝
路径穿越、重复文件、TAR 链接/特殊条目，以及超过条目数、单文件、总解压量或
目录深度限制的归档。上传或归档验证失败返回
`400 DEPLOYMENT_VALIDATION_ERROR`。

`POST /api/deployment/upload/batch` 使用相同的 `targetDirectory` 拒绝语义和归档边界。

## 覆盖语义与失败恢复

部署按同名文件覆盖目标版本目录，服务包中没有的现有文件保留。服务包中的路由 XML 与目标目录现有路由 XML 文件名不同时，新 XML 取代旧 XML，旧 XML 及其运行中的路由一并移除。

`autoStart=true` 时，端口占用检查在任何部署写入之前完成：按部署后的有效配置判断（服务包中的 `common.config.properties`/`service.config.properties` 优先，没有则沿用目标目录现有文件）。冲突时部署失败，服务目录和备份目录都不变。

文件写入服务目录后部署失败（例如路由加载或启动校验失败）时，服务端自动恢复部署前目录（有备份时保留服务 `logs/`；首次部署失败时运行日志归档到部署备份目录）：

| 部署前状态 | 失败后处理 |
| --- | --- |
| 目标目录存在且已备份 | 写回部署前备份；`autoStart=true` 时检查端口并重新加载、校验恢复后的路由。目录已恢复但路由未能加载时记为 `DEPLOY_RESTORE_VERIFY_FAILED`，此时不需要再手工回退目录 |
| 首次部署 | 移除本次创建的服务版本目录，运行日志先归档到部署备份目录下的 `{serviceName}-{serviceVersion}-failed-deploy-logs-{deploymentId}`；修正服务包后可直接重新部署同一版本 |
| 目标目录存在但关闭了备份 | 不恢复，目标目录保留本次写入内容 |

部署记录状态仍为 `FAILED`，恢复结果追加在 `errorMessage` 中，详细过程见详情接口 `deployLogs` 的 `DEPLOY_RESTORE`、`DEPLOY_RESTORE_SKIPPED`、`DEPLOY_RESTORE_VERIFY_FAILED` 或 `DEPLOY_RESTORE_FAILED` 步骤。同一服务版本已有其他控制面操作进行时返回冲突，对应部署记录同样为 `FAILED`。

## 部署历史列表

```bash
curl "http://localhost:8080/api/deployment/history?limit=50&serviceName=PlatformHttp&serviceVersion=v3.0.0"
```

Query 参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `limit` | 否 | 返回数量上限，默认 50 |
| `serviceName` | 否 | 按服务名过滤 |
| `serviceVersion` | 否 | 按服务版本过滤 |

响应字段：

| 字段 | 说明 |
| --- | --- |
| `totalCount` | 符合条件的历史总数 |
| `returnedCount` | 当前返回数量 |
| `deployments[].deploymentId` | 部署或回退记录 ID |
| `deployments[].operationType` | `DEPLOY` 或 `ROLLBACK` |
| `deployments[].status` | 部署状态，如 `SUCCESS`、`FAILED`、`ROLLED_BACK`、`ROLLBACK_FAILED` |
| `deployments[].serviceName` | 服务名 |
| `deployments[].serviceVersion` | 服务版本 |
| `deployments[].backupAvailable` | 是否具备回退所需备份目录 |

历史列表只返回概要，不返回完整步骤日志，避免一次拉取大量日志内容。

## 部署历史详情

```bash
curl "http://localhost:8080/api/deployment/history/detail/deploy-550e8400-e29b-41d4-a716-446655440000"
```

详情响应包含 `deployLogs`，用于定位部署或回退过程中的验证、备份、文件覆盖、路由加载等步骤。

## 部署回退

```bash
curl -X POST "http://localhost:8080/api/deployment/rollback/deploy-550e8400-e29b-41d4-a716-446655440000?autoStart=true"
```

回退语义是撤销指定部署，恢复到该部署记录发生前的备份目录状态，不是恢复到该记录部署成功后的文件快照。首次部署或未生成备份目录的记录不能回退。回退替换部署文件但保留服务 `logs/`；路由 XML 文件名与当前目录不同时，被替换路由同时停止。每次部署、回退前生成的备份目录相互独立，连续操作不会写入同一备份。

`autoStart=true` 时，服务端恢复文件后会主动加载恢复目录内的 XML 并校验路由状态，不只依赖文件监听事件。若恢复后的配置包含 `server.running=false`，回退会按停止态成功返回，不要求检测到已启动路由。

自动加载前会根据恢复后的 `HTTP.Listener/server.port/port.level` 检查端口占用。恢复服务或已加载服务任一方使用独立端口模式（`port.level=version`）时，同端口会失败并返回占用服务信息；双方均为共享端口模式时允许复用。

不可回退时返回 `400`，响应包含 `errorCode=ROLLBACK_NOT_AVAILABLE`。常见原因包括首次部署没有备份、备份目录已不存在或备份目录不在配置允许的备份根目录内。

## CLI 对应命令

```bash
lightesb deploy status <deploymentId>
lightesb deploy history --limit 20
lightesb deploy history --service-name PlatformHttp --service-version v3.0.0 --limit 20
```

CLI 的历史列表命令对应 `GET /api/deployment/history`。需要查看完整步骤日志时，可直接调用详情 API。
