# ExternalDB Component Usage Guide (Phase 1)

This document describes the minimum usage of the external database component `externaldb` in `MysqlRouteSrv/v1.0.0`.

## 1. Enable the Component

Enable it in `common.config.properties`:

```properties
system.components=externaldb
```

## 2. Configuration Sources and Priority

- `common.config.properties`: common default configuration
- `service.config.properties`: service-level override configuration
- Priority: `service.config.properties` overrides `common.config.properties`

## 3. extdb Configuration Example

`service.config.properties` already provides a MySQL example:

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

## 4. Bean Names in Camel Registry

After successful component registration, the following beans are bound to the Camel Registry:

- `extdb-<id>-datasource`, for example `extdb-primary-datasource`
- `extdb-default-datasource` (default datasource alias)
- `extdb.config` (parsed configuration object)
- `extdb.route.targets` (`*.target.datasource` mapping)

## 5. Route Reference Example

`mysql-healthcheck-route.xml` uses a route-level override:

```xml
<to uri="sql:select 1 as db_ok?dataSource=#bean:extdb-{{mysqlroute.target.datasource}}-datasource&amp;outputType=SelectOne"/>
```

## 6. Multi-Database Extension (Example)

You can continue adding multiple data sources in the same service:

```properties
extdb.ids=primary,archive

extdb.archive.type=postgresql
extdb.archive.url=jdbc:postgresql://127.0.0.1:5432/lightesb
extdb.archive.driver=org.postgresql.Driver
extdb.archive.username=postgres
extdb.archive.password=postgres
extdb.archive.maxPoolSize=10
```

SQLServer/Oracle can be added using the same key model:

- `extdb.<id>.type=sqlserver|oracle`
- `extdb.<id>.url`
- `extdb.<id>.driver`
- `extdb.<id>.username`
- `extdb.<id>.password`
- `extdb.<id>.maxPoolSize`

