---
name: lightesb-temp-form
description: 交付包内创建临时表单/审批/收集类网页服务（路由自吐 HTML 页面）、mock 数据演示、用完销毁路由时使用。
---

# LightESB 临时表单服务

先读：

- `docs/components/01-http-route-basics.md`
- `docs/components/03-charset-processing.md`
- `docs/runtime-route-loading.md`
- 样例 `example/routes/TempApprovalMockSrv/v1.0.0/`（复制到 `lightesb-camel-app/` 后运行，见 `example/README.md`）

规则：

- 最小创建集 = 路由 XML + `common.config.properties` + `service.config.properties` 三个文件；`log4j2.properties` 运行时自动生成，不要手工创建；Schema、samples 等只在实际使用时才添加。
- 表单页（GET）：`setBody` + `<constant><![CDATA[...]]></constant>` 内联完整 HTML，显式 `Content-Type: text/html;charset=UTF-8`；不要用 `jsonResponseProcessor`/`responseCharsetProcessor` 收尾，HTML 中不出现本地绝对路径。
- 页面样式：默认沿用 `example/routes/TempApprovalMockSrv/v1.0.0/` 样例的样式体系（CSS 变量 token、卡片 + 编号步骤布局、状态徽章语义色 `PENDING` 琥珀/`APPROVED` 绿/`REJECTED` 红、结果卡按 `success` 显示绿/红左边框、`prefers-color-scheme` 暗色自适应）；完整实现以样例为准，不复制到本文档。
- 不引 UI 框架和 CDN 资源，交互用原生 fetch + 少量 vanilla JS，保证内网/离线可用；品牌色与风格只是默认值，用户指定风格时以用户要求为准。
- 提交/审批（POST JSON）：`requestCharsetProcessor` 入口 → `jsonpath suppressExceptions="true"` 提取字段 → simple 空值判断兜底 400 → 拼装 mock 响应 → `jsonResponseProcessor` 出口。
- 查看（GET）：query 参数经 header 读取，返回固定 mock 数据；页面和响应文案明确标注 mock、无持久化。
- 端口：独立空闲 `server.port` + `port.level=version`，`system.components=undertowhttp,servicelog`，`server.running=true` 默认启动。
- 销毁：删除路由 XML 即自动卸载并释放端口；软摘除用 `POST /api/routes/unload?filePath=...`；文件放回后热加载恢复。
- `<simple>` 体内不混用 `{{占位符}}` 与字面 `}}`（报 `Missing {{ from the text`），占位符先经 `<constant>` 存入 exchangeProperty 再引用；simple 不支持 `? :` 三元，条件取值用 `<choice>` + `<constant>`。

验收：

- `curl http://127.0.0.1:<port>/api/<path>/form` 返回 200 且 `Content-Type: text/html`。
- 提交返回 200 + 生成的单号；缺字段返回 400。
- 管理面 `GET /api/routes/status` 能查到新增 routeId；删除 XML 后路由消失、端口释放。
