# LightESB 发布排障经验基线

本文件由源码交付上下文统一维护，随发布版本更新并允许升级覆盖。项目现场不得直接修改。

## 基线元数据

| 项目 | 当前值 |
| --- | --- |
| 经验格式版本 | 1 |
| 发布基线版本 | 5 |
| 最近更新 | 2026-08-26 |

发布基线内容发生实质变化时递增“发布基线版本”。项目经验记录审核通过的基线版本；版本不一致时先做兼容性审核。

## 经验卡格式

```markdown
### E-XXX 简短标题

- 状态：候选 / 有效 / 已替代
- 触发信号：可观察的错误、状态或现象
- 适用范围：服务类型、环境和前置条件
- 证据：交付仓库文件、脱敏日志、命令结果或用户确认
- 根因摘要：证据支持的结论
- 最小修复：限定范围的处理方式
- 验证：证明问题已解决的静态或运行态证据
- 失效条件：不能复用该经验的情况
- 来源日期：YYYY-MM-DD
- 最近验证：YYYY-MM-DD / 尚未验证
```

## 当前经验

### E-001 Action 可查询但受管 route apply 仍提示服务或资源不完整

- 状态：有效
- 触发信号：Action Catalog 中服务为 `AVAILABLE`，但 AI/会话受管 route validate 或 apply 提示服务不存在、固定 Schema 未提供，或把仍被 Action 契约引用的 Schema 列入 `deletedFiles`。
- 适用范围：已从交付目录加载 Action 服务，并使用服务管理受管 route apply 的环境。
- 证据：`action status/get`、`service list/get` 和同一候选的 `ai route validate --output json` 脱敏结果。
- 根因摘要：运行目录/Action Catalog 与服务管理注册是两个边界；固定 Schema 的实际资源闭包同时来自 JSON Schema 校验块和 Action input/output schema route property。
- 最小修复：先注册 provider、非空消息模型和目标服务关系；在非热加载目录执行 `ai route prepare`，只编辑候选并用 `ai route validate` 冻结完整变化集，再申请 fresh session。会话 allowlist 与 apply resources 同时包含 route 实际引用的固定 Schema。
- 验证：`service get` 可查到正确输入/输出消息关系；prepare 候选不在热加载根；validate 不再报缺失且不把仍引用的 Schema 列入 `deletedFiles`；批准后用最新 scope digest 受管 apply，并同时验证 route generation、Catalog revision/source digest 和 session transition。本地直编是另一条流程，不用 apply 追认；已批准会话期间的直接变化仍应 `STALE`。
- 失效条件：错误来自服务名/版本不一致、目录被隔离、allowlist/token/审批状态或其他稳定错误码时，需按对应边界另行排查。
- 来源日期：2026-08-25
- 最近验证：2026-08-25

### E-002 新服务进入会话受管 apply 的完整前置流程

- 状态：有效
- 触发信号：首次为一个已有运行目录的服务申请 Action 审批会话，或需要从零准备可审批的 route 候选。
- 适用范围：使用服务管理注册、Action Catalog、`ai route prepare/validate` 和会话受管 apply 的交付环境。
- 证据：`app/message/service create`、`service list/get`、`ai route prepare/validate`、session get 和 apply 的脱敏 JSON 结果；`docs/action-approval-api.md` 的 CLI 流程。
- 根因摘要：服务管理关系、持久化运行目录、路由加载、Action Catalog 和可审批候选是独立边界；任一单项成功不能代替其他证明。
- 最小修复：按以下顺序完成，不在已批准会话期间补注册或编辑 live 文件：

  ```bash
  lightesb app create --file app.json --yes --output json
  lightesb message create --file request-message.json --yes --output json
  lightesb message create --file response-message.json --yes --output json
  lightesb service create --file service.json --yes --output json
  lightesb service list --service-name <serviceName> --output json
  lightesb service get --id <serviceId> --output json

  mkdir -p build
  lightesb ai route prepare --service-name <serviceName> --service-version <vX.Y.Z> --out build/<candidate-directory> --yes --output json
  lightesb ai route validate --file build/<candidate-directory>/<route.xml> --service-name <serviceName> --service-version <vX.Y.Z> --route-file-name <route.xml> --resource-file common.config.properties --resource-file service.config.properties --output json
  ```

  `service.json` 必须使用前面创建后返回的真实 app/message ID；route 引用 `.ds` 或固定 Schema 时，validate、会话 allowlist 和 apply resources 还必须加入实际引用文件。validate 通过后再申请 fresh session，紧邻 apply 前重新 GET `currentScopeDigest`。
- 验证：服务关系、路由状态和 Catalog 分别可查；候选不在热加载根；validate 返回期望的 `savedFiles/deletedFiles`；apply 后 route generation、Catalog revision/source digest 和 session transition 同时变化。
- 失效条件：只做普通本地开发热加载而不需要审批 lineage 时，直接编辑正式服务目录并在验证后结束，不使用该受管 apply 流程。
- 来源日期：2026-08-25
- 最近验证：2026-08-25

### E-003 数据库版本升级必须先生成可恢复 SQL 备份

- 状态：有效
- 触发信号：准备执行任一正式上线后的 H2/MySQL 版本化升级 SQL。
- 适用范围：使用 `docs/sql/` 中版本化 SQL 升级已有数据库的交付环境；首次自动初始化且没有升级脚本时不执行升级。
- 证据：用户确认的升级与回退要求、升级前数据库类型和当前版本记录、数据库原生工具生成的完整逻辑 SQL 备份、备份 SHA-256、升级日志及结构核对结果。
- 根因摘要：版本化升级会改变已有结构或数据；没有与当前版本绑定且可校验的升级前备份，失败后无法证明能够恢复到原版本，也不能安全继续执行后续版本。
- 最小修复：维护窗口内先停止相关写入，按实际数据库类型生成完整逻辑 SQL 备份，记录客户、数据库类型、当前版本、目标版本、备份时间和 SHA-256，并确认备份可读取；随后只按当前版本到目标版本的顺序执行对应 H2 或 MySQL 脚本。不得跨方言、跳版本或在失败后继续补跑。升级失败时保留错误证据并从该备份恢复，客户登记版本保持原值。
- 验证：升级前备份文件非空、摘要可复算，且具备已验证的恢复入口；升级成功后核对目标表、列、约束、索引和必要数据，再更新客户登记中的数据库版本。恢复演练或失败回退后，结构、关键数据与原版本一致。
- 失效条件：仅创建全新空库且由当前运行时执行首次自动初始化；这时登记初始化基线版本，不执行空 baseline SQL，也不把初始化前的空库备份当作升级回退证据。
- 来源日期：2026-08-26
- 最近验证：尚未验证

### E-004 项目初始化时建立本地 Git 修复留痕

- 状态：有效
- 触发信号：首次接手交付目录，预计需要持续进行本地配置、路由或资源修复。
- 适用范围：允许使用本地版本控制的交付项目；仅保存已脱敏且获准纳入版本控制的项目文件。
- 证据：用户确认项目初始化时应推荐安装 Git、保存本地修复；业务现场的大模型完成一组明确修改后自动提交本次修改。该规则不在本机源码仓库自动执行；源码内容需要同步到官方外发仓库时只暂存同步文件。
- 根因摘要：缺少本地版本基线会使后续修复难以追溯、比较或安全回退。
- 最小修复：项目初始化时推荐安装 Git；确认不会纳入凭据、日志、客户数据或其他敏感文件后，执行 `git init` 并提交脱敏的初始基线。在业务现场仓库中，大模型每完成一组明确修改并通过相应验证后，逐路径检查、暂存并自动提交本次修改，不纳入已有无关改动。本机源码仓库不自动执行该提交规则；源码内容需要同步到官方外发仓库时，同步和静态验证通过后只在外发仓库暂存本次同步文件，不自动提交或推送。
- 验证：`git status` 能识别工作区改动，`git log` 能追溯初始基线和每次本地修复；提交只包含本次修改，敏感文件未被纳入版本控制；外发仓库的 `git diff --cached` 只显示本次同步文件。
- 失效条件：当前为本机源码仓库或官方发布仓库；客户安全策略禁止本地版本控制；或目录包含尚未完成隔离、脱敏和忽略规则配置的敏感数据时。官方发布仓库只适用源码同步后的暂存规则。
- 来源日期：2026-08-26
- 最近验证：尚未验证
