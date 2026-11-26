# 权限校验

## 用途

`permissionCheckProcessor` 用于在路由中按 IP、CIDR、正则和 Token 组合规则做访问校验。

## 使用方式

```xml
<process ref="permissionCheckProcessor"/>
```

建议捕获权限异常并返回 403：

```xml
<doTry>
  <process ref="permissionCheckProcessor"/>
  <doCatch>
    <exception>com.oureman.soa.lightesb.core.processor.PermissionCheckProcessor$PermissionDeniedException</exception>
    <setHeader name="CamelHttpResponseCode"><constant>403</constant></setHeader>
    <setBody><simple>{"error":"PERMISSION_DENIED","message":"${exception.message}"}</simple></setBody>
  </doCatch>
</doTry>
```

## PERMISSION_TYPE

| 值 | 规则 |
| --- | --- |
| `1` | 精确 IP |
| `2` | CIDR |
| `3` | 正则 |
| `4` | Token |
| `5` | IP + Token |
| `6` | CIDR + Token |
| `7` | 正则 + Token |
| `8` | 全部放行 |

类型为空或其他值时拒绝；管理接口保存规则时只接受 `1`~`8`，否则返回 400。

**升级提示：** 旧版本管理接口允许不填类型，这类规则（`PERMISSION_TYPE` 为空）以前按全部放行处理，升级后改为拒绝。升级前可用下面的 SQL 检查并补上类型：

```sql
SELECT APPLICATION_CODE, PERMISSION_TYPE FROM ESBMCP_PERMISSION_TABLE
WHERE PERMISSION_TYPE IS NULL OR PERMISSION_TYPE NOT IN ('1','2','3','4','5','6','7','8');
```


## 输入与输出

输入：

- `client.ip`
- `Token`
- `SenderID`

校验通过后：

- `exchangeProperty.permission.checked=true`
- `exchangeProperty.permission.applicationCode=<applicationCode>`

## 外网经 Nginx 接入

适用于内网调用方直连 ESB 服务端口、外网调用方经 Nginx 转发的部署。内网直连不需要以下配置。

**1. ESB 侧配置**

在 `lightesb-config.properties`（或启动参数 `-D`）中配置 Nginx 的地址，修改后重启生效：

```properties
# 填 Nginx 连接 ESB 时使用的源地址；多台用英文逗号分隔，也可写 IPv4 CIDR
lightesb.security.trusted-proxies=10.0.1.20,10.0.1.21
# Nginx 与 ESB 同机且 upstream 写 127.0.0.1:端口 时（推荐），源地址是 127.0.0.1
# lightesb.security.trusted-proxies=127.0.0.1
# 同机但 upstream 写的是本机网卡 IP 时，源地址是该网卡 IP，应填写网卡 IP 而不是 127.0.0.1
```

启动日志出现 `可信代理地址: exact=[...]` 表示配置已加载；未配置时不输出该行。

**2. Nginx 配置示例**

每个服务监听自己的端口（`common.config.properties` 中的 `server.port`），Nginx 按路径转发到对应端口：

```nginx
upstream esb_temp_approval {
    server 10.0.1.30:19097;   # ESB 主机地址与服务端口；与 ESB 同机时写 127.0.0.1:19097
}

server {
    listen 443 ssl;
    server_name esb.example.com;
    # ssl_certificate / ssl_certificate_key 按现场证书配置

    location /api/temp-approval/ {
        proxy_pass http://esb_temp_approval;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;                      # 必须设置
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

要点：

- 必须设置 `X-Real-IP $remote_addr`：Nginx 用真实客户端地址覆盖客户端自带的同名头，ESB 优先采信该头。不设置时 Nginx 会把客户端自带的 `X-Real-IP` 原样转发，客户端即可指定自己的 IP。`X-Forwarded-For` 仅在请求没有 `X-Real-IP` 时使用，ESB 取其中从右往左第一个不属于可信代理的地址。
- `location` 中只要写了 `proxy_set_header`，就会整体替换 `server`/`http` 层的同类配置；每个写了 `proxy_set_header` 的 `location` 都要完整重复上面几行。
- 只通过 Nginx 暴露业务服务端口，不要对外网开放管理端口（默认 `8080`）：权限、日志等管理接口、控制台页面和 H2 控制台没有鉴权。
- 外网调用方的权限规则按 Nginx 看到的客户端地址配置（精确 IP、CIDR 或正则）。

**3. 配错时的现象与排查**

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 外网请求全部被拒，日志出现"收到来自本机且带 X-Forwarded-For/X-Real-IP 的请求，但本机未配置为可信代理"（每个进程只输出一次） | Nginx 经 `127.0.0.1` 连接 ESB，但未配置可信代理 | 配置 `lightesb.security.trusted-proxies=127.0.0.1` 并重启 |
| 外网请求被拒，权限失败日志中的客户端 IP（`client.ip=` 或 `clientIp=`）是 Nginx 的地址 | 可信代理未包含 Nginx 连接 ESB 时的源地址（同机部署而 upstream 写网卡 IP 时，源地址是网卡 IP） | 把该源地址加入 `lightesb.security.trusted-proxies` |
| 已配置可信代理，权限失败日志中客户端 IP 为 `null` | Nginx 未带 `X-Real-IP`/`X-Forwarded-For`，常见于某个 `location` 自定义了 `proxy_set_header` 而漏掉这几行 | 在该 `location` 中补齐转发头 |
| 启动日志没有"可信代理地址"一行 | 配置未加载 | 检查配置文件路径与键名 `lightesb.security.trusted-proxies` |

## 常见问题

- Token 默认从 Exchange 属性 `Token` 读取，不等同于自动读取 `Authorization` 头。
- 需要 Token 的规则（`4`~`7`）必须配置 token，未配置时拒绝；不需要鉴权的调用方使用 `8` 类规则，或在路由中不调用 `permissionCheckProcessor`。
- `client.ip` 取 TCP 直连地址（依赖服务配置 `HTTP.Listener=true`）；只有直连地址属于 `lightesb.security.trusted-proxies` 时才采信 `X-Real-IP` / `X-Forwarded-For`，内网直连无需配置，外网经 Nginx 接入见上文“外网经 Nginx 接入”。可信代理未带转发头、或本机带转发头却未配置为可信代理时，客户端 IP 视为未知，IP 类规则拒绝。
- 精确 IP 规则按 IP 字段中的地址比较，可用逗号分隔多个地址（字段长度有限，通常最多两个 IPv4）；`localhost`、`::1` 与 `127.0.0.1` 视为同一地址，回环规则只匹配回环客户端。
- 未找到规则会拒绝。
- 规则类型为空或不在 `1`~`8` 内时拒绝访问。

## 离线验证

只验证失败分支时，可以不预置规则，请求会返回局部捕获的 403，错误消息通常为“未找到匹配的权限规则”。验证合法请求通过时，必须先通过管理接口或现场数据预置规则，例如：

```bash
curl -X PUT "http://localhost:8080/api/lightesb/permission/DOC_MOCK" \
  -H "Content-Type: application/json" \
  --data '{"permissionType":"8"}'
```

路由侧需要把调用方标识写入 `exchangeProperty.SenderID=DOC_MOCK`；Token 规则还需要把请求 token 写入 `exchangeProperty.Token`。
