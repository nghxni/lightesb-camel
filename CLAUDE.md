# CLAUDE.md

本文件与 `AGENTS.md` 同源，适用于 Claude 或其他 Agent 在 LightESB-Camel 交付包内工作。

- 先读 `AGENTS.md`，以其中目录边界、阅读顺序和 task -> skill 路由表为准。
- `lightesb-camel-app/` 是正式接口运行目录，只读参考，不新增代理上下文或索引。
- `example/` 是纯演示样例目录，可修改、复制到 `lightesb-camel-app/` 运行，演示完成后删除。
- 任务命中组件领域时，先读对应 `skills/<name>/SKILL.md`，再读 `docs/README.md` 和组件文档。
- 不引用未随包交付的内部架构流程文档，不使用与本交付包无关的外部技能路由。
