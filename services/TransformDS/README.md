# TransformDS 目录投放规范

## 目录用途

`services/TransformDS` 是 LightESB 数据转换扩展的统一投放目录，用于存放：

- DTS 自定义扩展 `jar`
- 数据转换规则文件（如 `*.ds`）
- 迁移交付包（runtime + 扩展包）
- 发布计划与运维说明文档

## 运行时扫描约定

- 默认扫描开关：`lightesb.transformds.enabled=true`
- 默认扫描目录：`lightesb.transformds.directory=services/TransformDS`
- 默认扫描模式：`lightesb.transformds.scan-pattern=*.jar`
- 以上配置支持外部覆盖（环境变量/外部配置文件）

## 扩展 jar 命名与版本规则

- 推荐命名：`<biz>-dts-impl-<semver>.jar`
- 版本格式：语义化版本 `major.minor.patch`
- 冲突处理建议：
  - 同一 `biz` 出现多个版本时，优先选择高版本
  - 若版本相同，按文件最后修改时间选择最新文件
  - 若仍无法判定，按文件名字典序做稳定选择并记录告警

## 构建输出到投放位置映射

- 构建输出目录：`example/transform-dts-java/target/*.jar`
- 投放目录：`services/TransformDS/`
- 投放动作：复制构建产物到投放目录，保留版本号，不覆盖不同版本文件

## 回滚建议

- 快速回滚：移除或重命名目标扩展 `jar`
- 回退验证：确认系统启动后已切回默认 DTS 实现
- 故障排查：检查启动日志中的 TransformDS 扫描结果与实现选择日志
