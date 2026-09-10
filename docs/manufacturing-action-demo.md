# 业务 Action 与 Codex CLI 演示

使用现有 CLI 查询三个业务 Action：订单发货检查、ERP/WMS 出库流水对账、回款异常。所有数据均为合成数据；快照固定为 `2026-09-08T00:00:00Z`，不代表实时系统、客户签收或任意历史状态。无需 MCP 或 Ash。

## 样例服务

| 业务服务 | Action | 依赖的模拟服务 | 默认端口 |
| --- | --- | --- | --- |
| `OrderDeliveryCheckSrv/v1.0.0` | `check-order-delivery` | `MockErpSrv`、`MockWmsSrv` | 18703 |
| `InventoryReconcileSrv/v1.0.0` | `reconcile-erp-wms` | `MockErpSrv`、`MockWmsSrv` | 18704 |
| `ReceivableExceptionSrv/v1.0.0` | `check-receivable-exceptions` | `MockErpSrv`、`MockTreasurySrv`、`MockContractSrv` | 18707 |

目录位于 `example/routes/`，配套 mock 端口依次为 18701、18702、18705、18706。所有服务默认 `server.running=false`，HTTP 只绑定 loopback。获得本地演示运行授权后，将完整服务版本目录复制到独立测试实例的 `lightesb-camel-app/`，显式启用相应服务。不要覆盖已有客户服务或配置。

业务 HTTP 入口固定返回 `403 ACTION_API_REQUIRED`；请通过受控 Action CLI 执行。Mock HTTP 仅供本地合成数据演示，不能用作生产接口。

## 准备与执行

按 [安全执行说明](action-execution-api.md) 显式开启八个 Action 开关。操作端准备精确 allowlist、查询 profile、短期运行 token 和可信审批会话：

- 查询 profile 只需 `catalog-read`；执行使用独立运行 token，不用查询 bearer 代替。
- 三个业务路由都有 HTTP 下游，read 声明也不能省略审批。每个服务版本分别申请会话，固定输入策略与摘要，通过 [可信审批接口](action-approval-api.md) 批准；`allowedFileNames=[]` 表示不允许修改路由。
- 操作端提供已批准 sessionId、固定 input-policy 文件以及环境中的运行 token；不向 Codex 提供管理或签名凭据。不让 Agent 修改策略、扩大查询范围或绕过失效批准。
- 审批回调时间使用当前 UTC，最多毫秒精度；token/session TTL 使用真实时钟，与模拟快照时间无关。

```bash
lightesb action search --query 交付 --output json
lightesb action get --action-id check-order-delivery --service-version v1.0.0 --output json
```

`get` 返回 Schema 文件名与 SHA-256，不返回正文。将样例自带的 `request-schema.json`、`response-schema.json` 原字节复制给 Agent，先核对在线摘要，不一致时停止。Agent 使用资料不应包括 mock 路由、测试数据、答案或服务端凭据。

输入文件示例：

```json
{"orderId":"<由用户提供的订单号>","asOf":"2026-09-08T00:00:00Z"}
```

```bash
lightesb action execute \
  --action-id check-order-delivery --service-version v1.0.0 \
  --input-file request.json --input-policy-file input-policy.json \
  --session-id '<approved-session-id>' --yes --output json
```

订单使用 `orderId`；对账使用 `documentId` 和 `warehouseId`；回款使用 `customerId`，均需带固定 `asOf`。所有参数以各自 Schema 为准。

## 结果边界

- 订单：按返回状态解释正常、部分发货、逾期或冲突。`READY` 不代表客户签收。无效、缺失、歧义或过期数据返回 `UNKNOWN`。
- 对账：按出库单、仓库、行号、SKU 关联，不拿出库量与库存余额相减；重复记录不自动合并，不跨单位计算。是否存在差异必须以实际调用结果为准。
- 回款：金额为整数分，示例币种 CNY/USD；不跨币种相加，不自动分配未认领到账，不催收或付款。当前结清不证明历史是否准时到账，不能凭客户ID猜测回款情况。
- HTTP 失败返回 `UPSTREAM_UNAVAILABLE`，数据/计算处理失败返回 `DATA_OR_PROCESSING_ERROR`。不能据此编造缺货、拒付等原因。

只根据 `data.output` 和 `evidence` 解释结果；授权和执行审计 ID 用于追踪调用。权限失败、摘要不一致或会话失效应停止，由操作端按原授权范围重新准备。

先验证一个场景的正常、缺参和权限失败，再测试三场景与多轮追问。缺少订单号等必要参数应补问；缺失/过期资料不能解释为业务正常。分别记录业务正确性、服务端权限和测试环境的隔离程度，本演示不等于生产安全认证或现场验收。
