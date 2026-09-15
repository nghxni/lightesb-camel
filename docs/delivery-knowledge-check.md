# 交付知识接手与离线检查

新客户接手、升级后首次修改服务，或任务提示缺文件/未知命令时，先确认当前包具备所需知识和工具。后续同一版本只复查本次涉及的能力，无需每个任务重做全部检查。

## 1. 确认当前目录与能力

从包内 [Agent 规则](../AGENTS.md)、[组件索引](README.md) 和对应 Skill 开始。查看当前交付包的 manifest/校验结果；有 CLI 时先运行：

```bash
java -jar lightesb-cli.jar --version
java -jar lightesb-cli.jar --help
```

仅在任务需要对应能力时检查完整命令层级及所需选项，例如：

```bash
java -jar lightesb-cli.jar message schema generate --help
java -jar lightesb-cli.jar ai route validate --help
java -jar lightesb-cli.jar action validate --help
```

这些帮助命令不连接服务端；不要为验证命令存在而执行 create、apply 或 execute。CLI 帮助通过只证明本地命令存在，远程 API 是否可用仍取决于所连接的服务端版本和配置。按 [CLI 参考](cli/01-cli-command-reference.md) 及 [发布验证](release-verification-and-upgrade.md) 核对，不能仅凭相同 Camel 版本推断能力相同。

没有 JAR、命令或选项时，报告“当前包缺少什么、阻塞哪个步骤、需要匹配哪个交付版本”，保留已完成的静态工作。不要从开发机复制工具、猜测替代命令或以跳过校验继续发布；需要的运行或升级动作按已有授权执行。

## 2. 检查知识文件

包根目录运行（需要 Python 3）：

```bash
python3 skills/lightesb-project-troubleshooting/scripts/check-delivery-context.py --root .
```

[检查脚本](../skills/lightesb-project-troubleshooting/scripts/check-delivery-context.py) 只读检查 MANIFEST 中的 docs/skills/example/proto 文件、知识入口、docs/skills Markdown 本地链接和 AGENTS/组件索引中反引号形式的 task-to-skill 路由。缺文件、链接越出包根目录、链接文件漏入清单均失败。不检查网址、标题锚点、任意代码示例或自然语言指令，也不执行文档中的命令；网站和运行产物使用各自发布校验。

通过不代表命令存在、模型能正确执行或服务能加载。现场项目经验位于 `project-experience/lightesb-project-troubleshooting.md`，不进入发布 MANIFEST；此检查不读取、创建或修改它。升级保留与兼容审核按 [排障 Skill](../skills/lightesb-project-troubleshooting/SKILL.md) 执行。

## 3. 按实际场景检查服务文件

复用 [路由静态预检](components/16-route-static-preflight.md) 和 [包内脚本](../skills/lightesb-route-authoring/scripts/route-static-preflight.py)，在真实目标服务目录上选择对应 profile；不因检查自动复制样例到运行目录。

以下五个随包样例用于核对知识、配置和资源是否完整，静态检查不会启动它们：

| 场景 / profile | 参考样例 | 权威说明 |
| --- | --- | --- |
| HTTP / `http` | [DemoHttpSrv](../example/routes/http-undertow/DemoHttpSrv/v1.0.0/) | [HTTP 基础](components/01-http-route-basics.md) |
| Timer / `timer` | [timer v1.0.1](../example/routes/timer/v1.0.1/) | [Timer](components/14-timer-routes.md) |
| 转换 / `transform` | [PlatformHttp v1.0.0](../example/routes/PlatformHttp/v1.0.0/) | [转换](components/04-transform-components.md) |
| Schema / `schema` | [DemoSecuritySrv](../example/routes/security-validation/DemoSecuritySrv/v1.0.0/) | [Schema](components/05-json-schema-validation.md) |
| ExternalDB / `externaldb` | [MysqlRouteSrv](../example/routes/MysqlRouteSrv/v1.0.0/) | [ExternalDB](components/11-externaldb.md) |

例如：

```bash
python3 skills/lightesb-route-authoring/scripts/route-static-preflight.py   --service-dir example/routes/PlatformHttp/v1.0.0 --profile transform
```

`transform-json/DemoTransformSrv` 仅展示可选转换的调用位置，没有启用输入转换；需要完整转换能力时使用上表样例。启用文件型输入/输出转换时，properties 指向的 `.ds`/`.jslt` 必须随服务提供，不能只带 XML。

## 4. 留给下一位使用者的信息

在任务交付中简要记录当前包/CLI 版本（无法确认则注明）、所用文档/Skill、服务名与版本、已检查项、缺失项和下一步。完整 XML、配置和资源留在实际服务目录，避免只保存在会话里。静态通过、实际加载和业务验证分别说明；缺少后两项时给出最小验证入口，不把计划步骤当成已执行结果。
