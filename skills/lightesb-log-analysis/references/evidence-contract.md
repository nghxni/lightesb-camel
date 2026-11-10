# 日志证据工具契约

当前支持inventory/query本地日志采证；用`--help`查看实际参数。无需pip、模型key或运行中的LightESB。仅读取显式根下选定文件，不联网、不执行输入、不写数据库。JSON导入尚未提供。

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
