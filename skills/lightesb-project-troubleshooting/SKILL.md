---
name: lightesb-project-troubleshooting
description: 交付仓库内基于证据排查 LightESB 项目问题，使用可升级发布基线和独立项目经验持续沉淀安全、可审核的技术方法。Use when diagnosing route loading, configuration, logs, CLI, management API, external integration, or other delivery-project failures; also use after a verified fix, user correction, field handover, release-context upgrade, experience-distillation request, or periodic skill review.
---

# LightESB 项目问题排查

用“证据 → 判断 → 行动 → 验证”定位交付项目问题，并把经过验证的方法沉淀为可复用经验。本 Skill 只使用交付仓库内可见的规则、文档、配置、样例、日志和运行证据。

## 识别维护模式

开始任务时在交付仓库根目录运行：

```bash
skills/lightesb-project-troubleshooting/scripts/detect-maintenance-mode.sh .
```

脚本只按当前仓库的 `origin` 地址判断，不扫描源码目录、不使用人工标记：源码仓库 `origin` 精确等于 `https://gitee.com/nghxni/lightesb.git` 时是 `local`（本机源码）；外发仓库 `origin` 精确等于 `https://github.com/nghxni/lightesb-camel.git` 时是 `release`（官方发布仓库）；没有 Git、没有 `origin` 或地址不完全相同时才是 `field`（业务现场）。

- `local`/`release` 模式：`SKILL.md`、`references/baseline-experience.md` 和 `references/project-experience-template.md` 由源码交付上下文统一维护；发布仓库只读使用并保持与源码一致。
- `field` 模式：把 `references/baseline-experience.md` 作为可升级、只读的发布基线；后续新增或修订经验只写根目录 `project-experience/lightesb-project-troubleshooting.md`。

现场仓库可以没有 Git、没有 `origin`、指向其他仓库，或保留过期 Git 历史。脚本只输出 `mode` 和 `origin_match`，不会输出可能含凭据的其他远端地址。分支是否最新不参与模式判断，只在本机同步前另行检查。

## 区分经验所有权

- 发布基线属于版本包，可在升级时覆盖；基线内容实质变化时递增其中的“发布基线版本”。
- 项目经验属于当前交付项目，位于受管 `skills/` 目录之外，不进入发布 MANIFEST，升级不得删除、覆盖或隐式创建。
- 项目经验不存在时先按“无项目经验”继续排查。只有准备写入第一条验证经验时，才在 `field` 模式运行 `scripts/init-project-experience.sh`；`local`/`release` 模式不得初始化或修改。
- 项目经验的“已审核发布基线版本”与当前基线不一致时，先检查冲突和过期规则。正式文档、新发布基线和安全边界优先；旧项目经验不能覆盖它们。

## 开始排查

1. 先读根目录 `AGENTS.md` 和 `docs/README.md`，确认目录、授权与验证边界。
2. 按问题领域读取对应 `skills/<name>/SKILL.md` 和组件、CLI 或 API 文档。
3. 读取 `references/baseline-experience.md`；业务现场模式且项目经验文件存在时，再读取根目录项目经验。只采用状态为“有效”、适用条件匹配且已按当前基线审核的记录。
4. 用一句话定义期望结果，区分事实、推断、未知项和暂不处理事项。

需要从源码仓库普通同步文件时，仅允许在源码 `local` 模式执行，并将内容发布到精确 GitHub `release` 仓库。本机源码新增或实质修改可外发经验后，自动完成脱敏和交付视角改写，再进入该增量同步流程；个人画像、内部判断记录、原始对话和其他不可外发信息不参与。先运行 `git status --short --branch` 检查当前分支、精确 `origin`、upstream 和已有改动，再执行 `git fetch --prune` 与 `git pull --ff-only`，确认最新基线后增量同步。验证通过后默认只暂存同步文件，不自动提交或推送，除非用户明确要求。`field` 现场只能使用发布方明确提供的升级流程更新发布基线；升级前后都要证明根目录项目经验内容不变。

## 收集最小证据

按问题选择足以改变结论的证据，不默认启动或重启服务：

- 路由加载：检查服务目录层级、唯一 route XML、两个 properties、资源引用、占位符和 route id。
- 配置问题：检查配置键来源、组件开关、服务名/版本、端口和环境占位值，不输出凭据实值。
- 运行异常：优先检查服务日志、路由状态和只读诊断；未经授权不调用业务接口或远程写操作。
- CLI/API：记录命令、参数、退出码、结构化错误码和脱敏响应，不用成功文案替代真实状态。
- 外部系统：先证明本地配置闭包和协议前置条件，再区分本地问题、网络问题、认证问题和对端问题。

无法复现时，写明已检查证据和缺失证据，不把猜测包装成根因。

## 形成与验证修复

1. 给出最可能根因及支持证据；存在竞争假设时说明如何区分。
2. 选择不破坏 `lightesb-camel-app/{serviceName}/{serviceVersion}` 契约的最小修复。
3. 只修改当前问题需要的文件，保留用户已有改动。
4. 先做静态或只读验证；只有用户明确授权时才启动、重启、调用接口或执行远程写操作。
5. 交付时说明修改文件、已验证内容、未验证运行态和残余风险。

## 沉淀排障经验

在修复被实际证据证明、用户纠正处理方式或用户明确要求沉淀时：

1. 判断结论能否跨服务或跨任务复用；一次性命令、偶发日志和临时路径不沉淀。
2. 本机开发模式不直接修改外部仓库中的经验文件；由源码仓库审核并更新发布基线，可外发内容随后按安全门禁自动改写和增量同步。
3. 业务现场首次写入前运行 `scripts/init-project-experience.sh`；随后按根目录项目经验文件的经验卡格式记录触发信号、证据、根因、最小修复、验证和失效条件。
4. 未经运行证据或用户确认的结论标记为“候选”，不得直接作为后续修复依据。
5. 新证据推翻旧经验时，将旧卡标记为“已替代”并指向新卡，不静默覆盖。
6. 如果结论属于某个组件或 CLI/API 的固定用法，优先更新现场可用文档或专项 Skill；经验库只保留诊断判断。

不要记录：

- 商业、销售、售前和宣传资料
- 视频策划、制作、渲染、发布或相关复盘内容
- 个人画像、内部判断记录、原始对话或隐藏思维链
- 密钥、Token、真实客户数据、私有地址、完整业务报文或未脱敏日志
- 未随交付仓库提供的内部路径、内部流程或内部文档内容

POC、客户交付或业务现场产生的经验，只有在去除客户身份、业务数据、环境地址、凭据和商业背景后，才能作为纯技术排障经验记录。

## 审核经验库

完整审核周期为 30 天或新增/实质修改 10 条记录，以先到者为准。

1. 本机开发模式只审核源码对齐的发布基线，不在外部仓库修改项目经验。
2. 业务现场模式汇总根目录项目经验中的有效、候选和已替代记录；文件不存在时无需初始化。
3. 检查重复、冲突、过期配置、失效链接和缺失证据。
4. 用当前发布基线、交付文档、样例与可用验证重新核对；处理基线版本变化造成的冲突或过期记录。
5. 对候选经验给出来源和影响，待用户确认后再晋升为“有效”。
6. 完整审核后更新项目经验的“已审核发布基线版本”、审核日期，并把记录变更数归零。

不要从经验库推断生产操作授权、对外承诺或安全例外；这些事项每次都需要用户明确授权。

## 经验文件

- `references/baseline-experience.md`：源码维护、升级时允许覆盖的发布经验基线
- `references/project-experience-template.md`：随版本升级、只用于首次初始化的项目经验模板
- `../../project-experience/lightesb-project-troubleshooting.md`：业务现场独立维护、升级永不覆盖的项目经验
