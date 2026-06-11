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
extdb.primary.url=${lightesb.mysql.url}
extdb.primary.driver=${lightesb.mysql.driver}
extdb.primary.username=${lightesb.mysql.username}
extdb.primary.password=${lightesb.mysql.password}
extdb.primary.maxPoolSize=10
mysqlroute.target.datasource=primary
```

组件注册成功后，数据源 Bean 名为 `extdb-<id>-datasource`，例如 `extdb-primary-datasource`。路由可通过属性拼接目标数据源：

```xml
<to uri="sql:select 1 as db_ok?dataSource=#bean:extdb-{{mysqlroute.target.datasource}}-datasource&amp;outputType=SelectOne"/>
```

`MysqlRouteSrv/v1.0.0` 使用 `timer://mysql-healthcheck?fixedRate=true&period=60000` 定时执行：

- `select 1 as db_ok` 健康检查。
- 向 `testexdb` 插入测试数据。
- 查询刚插入的数据。
- 删除测试数据。

## 路由建议

- SQL 参数使用 Header 或 Exchange Property 传递，不拼接未校验的外部输入。
- 写操作增加异常分支，避免数据库错误变成不清晰的 500。
- 健康检查路由保持简单，只验证连接和基础查询。
- 演示配置可以使用占位符，真实凭据不要写入交付样例。

## 验证

- 使用演示库执行一条只读查询。
- 准备 `testexdb(ID, name, sex)` 表后复制 `example/routes/MysqlRouteSrv` 到 `lightesb-camel-app/`，观察定时健康检查日志。
- 故意配置错误连接，确认异常日志和响应可定位。
- 检查连接信息只存在于演示配置，不写入真实凭据。
