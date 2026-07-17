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

部署和仅验证接口都会检查服务目录结构。每个 `serviceName + serviceVersion` 目录必须包含 `service.config.properties`，并且恰好包含一个 `*.xml` 路由文件；缺少 XML 或存在多个 XML 时返回验证失败，不会复制服务文件或启动路由。

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

回退语义是撤销指定部署，恢复到该部署记录发生前的备份目录状态，不是恢复到该记录部署成功后的文件快照。首次部署或未生成备份目录的记录不能回退。

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
