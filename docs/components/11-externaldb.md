# ExternalDB 数据访问

## 用途

ExternalDB 用于在路由中访问外部数据库，适合健康检查、查询、写入和同步类场景。

## 配置思路

在服务配置中声明数据源连接信息，并在路由中通过 Camel `sql:` 组件引用注册后的数据源 Bean。优先参考 `example/routes/MysqlRouteSrv/v1.0.0/`。

示例配置：

```properties
system.components=externaldb
extdb.enabled=true
extdb.default=primary
extdb.ids=primary
extdb.primary.type=mysql
extdb.primary.url=PLACEHOLDER_CONFIGURE_IN_SITE
extdb.primary.driver=com.mysql.cj.jdbc.Driver
extdb.primary.username=PLACEHOLDER_CONFIGURE_IN_SITE
extdb.primary.password=PLACEHOLDER_CONFIGURE_IN_SITE
extdb.primary.maxPoolSize=10
mysqlroute.target.datasource=primary
```

`extdb.*` 的连接字段按 properties 字面值读取，不会继续解析 `${lightesb.mysql.*}` 一类 Spring 占位符。部署时通过站点安全配置流程替换 `PLACEHOLDER_CONFIGURE_IN_SITE`；替换完成并验证前保持 `server.running=false`。当前组件没有独立的环境变量密钥解析层。

组件注册成功后，数据源 Bean 名为 `extdb-<id>-datasource`，例如 `extdb-primary-datasource`。路由可通过属性拼接目标数据源：

```xml
<to uri="sql:select 1 as db_ok?dataSource=#bean:extdb-{{mysqlroute.target.datasource}}-datasource&amp;outputType=SelectOne"/>
```

## 连接池生命周期

- 多个服务可以都使用 `primary` 作为本服务内的数据源 id。
- 底层连接池是否共享由连接签名决定，包括 `type/url/driver/username/password/maxPoolSize`。
- 连接签名相同会复用同一个底层池；连接签名不同会创建独立池。
- 路由上下文中绑定的数据源只用于获取连接，不负责关闭底层连接池。
- 不要在路由、脚本或服务卸载动作中手工关闭 `extdb-*` 数据源；连接池由平台统一管理。

`MysqlRouteSrv/v1.0.0` 使用 `timer://mysql-healthcheck?fixedRate=true&period=60000` 定时执行：

- `select 1 as db_ok` 健康检查。
- 向 `testexdb` 插入测试数据。
- 查询刚插入的数据。
- 删除测试数据。

## 路由建议

- SQL 参数使用 Header 或 Exchange Property 传递，不拼接未校验的外部输入。
- MySQL 支持在 prepared statement 中用参数占位符传递 `LIMIT` 值。HTTP Query 参数进入 Camel Header 后通常是字符串；直接写 `limit :#limit` 可能被绑定成 `LIMIT '20'`，MySQL 会报 `PreparedStatementCallback; bad SQL grammar`。先用 Simple 的 `resultType` 把 Header 转成数值类型，再传给 `LIMIT`：

```xml
<setHeader name="queryLimit">
  <simple resultType="java.lang.Integer">${header.limit}</simple>
</setHeader>
<to uri="sql:select * from demo_table order by created_at desc limit :#queryLimit?dataSource=#bean:extdb-{{demo.target.datasource}}-datasource"/>
```

- 若当前 MySQL 版本或查询形态无法使用 `LIMIT` 参数，可退回窗口行号过滤，例如 `row_number() over (...) as rn` 后 `where rn &lt;= least(greatest(cast(:#limit as unsigned), 1), 100)`；该写法依赖 MySQL 8.0 及以上窗口函数能力。
- `outputType=SelectOne` 查询单列时，Camel SQL 可能直接把该列值作为 body 返回；查询多列时通常返回 Map。若 SQL 只返回一列 JSON 字符串，不要写 `${body[RESPONSE_JSON]}`，直接使用 `${body}` 返回或继续处理。
- 写操作增加异常分支，避免数据库错误变成不清晰的 500。
- 健康检查路由保持简单，只验证连接和基础查询。
- 交付样例使用 `PLACEHOLDER_CONFIGURE_IN_SITE`，真实连接信息不要写入版本库。

## 官方参考

- MySQL `SELECT` / `LIMIT`：https://dev.mysql.com/doc/refman/8.4/en/select.html
- MySQL 窗口函数： https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html
- Camel SQL 组件： https://camel.apache.org/components/latest/sql-component.html
- Camel Simple 语言 `resultType`： https://camel.apache.org/components/latest/languages/simple-language.html

## 验证

- 使用演示库执行一条只读查询。
- 准备 `testexdb(ID, name, sex)` 表后复制 `example/routes/MysqlRouteSrv` 到 `lightesb-camel-app/`，观察定时健康检查日志。
- 故意配置错误连接，确认异常日志和响应可定位。
- 若响应出现 `PreparedStatementCallback; bad SQL grammar`，优先查看服务目录 `logs/` 下的完整异常；MySQL 报错位置在 `LIMIT '20'` 一类片段时，检查 Header 是否仍是字符串，按上面的 `resultType` 写法转成整数。
- 若出现 `HikariDataSource ... has been closed`，优先确认运行包版本是否包含连接池统一生命周期管理；已关闭的池需要重启应用恢复。
- 检查占位符已在站点安全配置流程中替换，且真实连接信息未提交到版本库。
