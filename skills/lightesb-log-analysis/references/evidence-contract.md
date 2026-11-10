# 日志证据工具契约

支持inventory/query本地日志采证与import-json离线导入；用`--help`查看实际参数。无需pip、模型key或运行中的LightESB。仅读取显式根下选定文件，不联网、不执行输入、不写数据库。

## 查询与来源

系统应用日志通常位于安装根logs；服务文件位于lightesb-camel-app/{serviceName}/{serviceVersion}/logs。inventory只读元数据，覆盖这些受管目录，默认不自动扫描未知目录。query用重复`--source`指定相对文件；不接受遍历、符号链接、FIFO/设备。自定义路径使用明确根绑定。

支持项目默认UTF-8的应用/服务pipe布局、服务DEBUG、文本滚动和多行记录。默认读取尾部；`--offset`/`--length`用于显式原文件字节区间，`--expected-identity`可传上次identityBefore JSON以核对同名文件。文件或目录绑定变化时丢弃不稳定正文并报告缺口。非零起点保守丢弃首个物理行并标记TRUNCATED_PREFIX，避免将正文内嵌时间戳误当记录头；后续完整记录仍可解析。

gzip须指定`--gzip`，只从头有界解压；定位单位为decompressed-byte，不支持压缩文件任意续读。重新读取从头解压的字节仍扣预算。

`--level`、`--id`、`--service-name/version`、`--contains`、`--start-time/end-time`只过滤已读取记录，不证明全目录/全历史无命中。`--timezone`显式提供IANA时区；缺少时保留原时间，不能伪造UTC顺序。字面过滤值不原样回显。

可选`--layout-config`读取根内properties白名单。只展开同文件LOG_PATTERN/LOG_DIR/LOG_CHARSET三个常量的简单引用，深度4、替换32次、结果8 KiB；循环、缺失、重复、Lookup和其他语法标unresolved。配置须有有效logger/rootLogger到唯一appender.name的引用及匹配文件路径，未引用或冲突时保留推断布局。配置只说明期望布局，要与实际记录核对，不能自动授权根外文件。

## 输出及引用

stdout单份JSON，schemaVersion=1；状态与退出码：COMPLETE_WITHIN_SCOPE=0、PARTIAL=3、UNAVAILABLE=1、INVALID_INPUT=2。PARTIAL允许零事件；COMPLETE仅表示选定范围处理完，不表示系统健康。stderr不回显原文。

- diagnosisId由调用方给出或本次新建，captureId每次独立。事件完整引用为diagnosisId/captureId/sourceId/evidenceId，合并时保留原编号。
- sources保留相对位置或安全别名、身份观察值、ranges/bytesRead、截断/变化/错误和布局提示；不会输出绝对机器路径。
- events保留可验证的timestamp/normalizedTime、level、logger、serviceName/version、fileKey、routeId/exchangeId、locator和固定signal。message、报文和未知业务正文不输出；不能把suppressed理解为没有日志。
- locator的start/end为半开区间，unit标byte或decompressed-byte。未知全局行号不补造。repeatCount和可选lastLocator/lastTimestamp仅聚合连续同一来源的相同已识别信号，保留状态变化。
- coverage区分recordsRead、layoutParsed、semanticRecognized、unclassified、suppressed及截断；比例分母只可用本次已读记录。缺失身份/时间保留null。
- usage返回inputBytes、decompressedBytes、decompressedBytesExact、outputBytes、elapsedMs。解压异常时保留失败调用预留的最大输出额度（每块最多8192字节），decompressedBytesExact=false表示保守上界；正常返回块按实际字节累计。总处理量为inputBytes+decompressedBytes；gzip两部分都计入。outputBytes包含JSON本身及末尾换行。

服务MDC的联合service-version不得按首个连字符强拆；logger短名可能截断；同名ID跨环境不能自动关联。固定模板描述的是日志报告的事实，不足以证明最终业务结果。

## 预算

| 参数 | 默认 | 硬上限 |
| --- | --- | --- |
| --max-entries | 2000 | 10000 |
| --max-files | 20 | 100 |
| --max-file-bytes | 262144 | 2097152 |
| --max-bytes | 8388608 | 67108864 |
| --max-record-bytes | 16384 | 65536 |
| --max-events | 100 | 500 |
| --max-output-bytes | 131072 | 524288（至少4096） |
| --max-seconds | 10 | 60 |

整次问题预算由Skill累计管理，工具只约束当前调用。Agent须设置进程外层截止时间，不能声称合作式计时能立即中断阻塞IO。新查询不能通过更换diagnosisId重置同一问题预算，恢复时缺失使用量应停止自动续采。

## 导入既有 CLI JSON

```bash
python3 -B skills/lightesb-log-analysis/scripts/log_evidence.py import-json --kind instance-list --root <安全采集目录> --source capture.json
python3 -B skills/lightesb-log-analysis/scripts/log_evidence.py import-json --kind instance-detail --input - < capture.json
```

`--source`与`--input`同义；stdin不需要本地目录后端，调用方负责来源和外层截止时间。文件仍使用相同安全根/类型检查，从头读取；不完整JSON不解析。stdin读满额度时无法确认EOF，保守返回PARTIAL。严格UTF-8、禁止重复键/非有限数，结构深度32、节点20000；未知结构/schema拒绝。不会根据文件名猜类型。

| kind | 记录位置及保留信息 |
| --- | --- |
| log-snapshot | files/i/lines/j；已知布局、服务MDC、文件截断/变化/readError；不造文件字节位置 |
| instance-list | records/i；实例、提供方状态/时间和安全身份，保留分页total/pageNum/pageSize |
| instance-detail | 根记录及itemRecords/i；状态/时间、reqBodyPresent/resBodyPresent，明细parentInstanceUuid来自父记录 |
| diagnostics-snapshot / diagnostics-warnings | components/i；当前状态、固定数值/布尔指标和明确存储枚举；warnings仅计数 |
| route-status / route-detail | 根记录；当前文件/路由数量、ID、运行状态；不输出配置和目录 |
| deploy-status | 根记录；部署身份、状态、进度和时间；不输出部署日志/路径 |

标准success=true响应保留/data指针前缀；裸响应按kind校验。success=false先识别为UNAVAILABLE，保留安全错误码、httpStatus、CLI exitCode；不把失败的data当成功。导入只保留固定字段，不输出自由message、报文、错误详情或未知字段。

可选`--metadata`接收最多4096字节JSON，解析前计入同一输入预算：targetAlias、commandKind、startedAt/completedAt、exitCode和有限filters；输出标caller-supplied，不能当服务端事实。命令类型不匹配拒绝，非零CLI退出码不能推导成功。endpoint由kind固定映射；不接受URL/header/凭据投影。

查询时间、服务端生成时间和导入时间分别保留；缺少时区不建立绝对时间顺序。instance start/end过滤的是记录create_time，sessionId为UUID子串候选，列表联接可有多行同实例；有限分页不是事务快照。存储未提供时不推断MySQL/H2。writer storage的mysql/h2映射MYSQL/H2；查询存储的mysql/h2-fallback映射MYSQL/H2_FALLBACK，其他为UNKNOWN。

先用有界列表定位，必要时读取少量详情。CLI会先缓冲整个HTTP响应，详情可能携带报文；工具的离线字节额度不能限制此前HTTP大小、Java内存或服务端查询。将原始响应保留在受控临时位置，不放进模型上下文或Git。跨次合并仍由Agent保留完整来源引用，工具不将当前诊断或路由状态冒充历史调用事件。

单记录字节预算约束query文本记录及log-snapshot行；其他JSON kind按整份输入字节、结构深度/节点、事件和输出预算处理，不将单记录额度宣称为CLI详情报文大小限制。
