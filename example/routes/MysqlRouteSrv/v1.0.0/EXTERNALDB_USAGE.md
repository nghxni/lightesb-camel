# ExternalDB 组件使用说明（一期）

本文档说明 `MysqlRouteSrv/v1.0.0` 中外部数据库组件 `externaldb` 的最小用法。

## 1. 组件启用

在 `common.config.properties` 中启用：

```properties
system.components=externaldb
```

## 2. 配置来源与优先级

- `common.config.properties`：通用默认配置
- `service.config.properties`：服务级覆盖配置
- 优先级：`service.config.properties` 覆盖 `common.config.properties`

## 3. extdb 配置示例

`service.config.properties` 已提供 MySQL 示例：

```properties
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

## 4. Camel Registry 中的 Bean 名

组件注册成功后会向 Camel Registry 绑定：

- `extdb-<id>-datasource`，例如 `extdb-primary-datasource`
- `extdb-default-datasource`（默认数据源别名）
- `extdb.config`（解析后的配置对象）
- `extdb.route.targets`（`*.target.datasource` 映射）

## 5. 路由引用示例

`mysql-healthcheck-route.xml` 使用了路由级覆盖：

```xml
<to uri="sql:select 1 as db_ok?dataSource=#bean:extdb-{{mysqlroute.target.datasource}}-datasource&amp;outputType=SelectOne"/>
```

## 6. 多数据库扩展（示例）

可继续在同一服务中追加多个数据源：

```properties
extdb.ids=primary,archive

extdb.archive.type=postgresql
extdb.archive.url=jdbc:postgresql://127.0.0.1:5432/lightesb
extdb.archive.driver=org.postgresql.Driver
extdb.archive.username=postgres
extdb.archive.password=postgres
extdb.archive.maxPoolSize=10
```

SQLServer/Oracle 可按同样键模型追加：

- `extdb.<id>.type=sqlserver|oracle`
- `extdb.<id>.url`
- `extdb.<id>.driver`
- `extdb.<id>.username`
- `extdb.<id>.password`
- `extdb.<id>.maxPoolSize`

