# AVEVA Plant SCADA OPC UA / MQTT 接入

本文说明交付包中如何通过 LightESB 接入 AVEVA Plant SCADA 的标准接口。首版使用 `industrial` 轻封装：路由仍使用 Camel 原生 `milo-client:` 和 `paho-mqtt5:`，校验、脱敏、标准 JSON 和错误映射由 `industrial` processor 完成。

## 启用方式

服务配置中启用：

```properties
HTTP.Listener=true
server.running=false
server.port=19110
port.level=version
system.components=undertowhttp,industrial

industrial.source=aveva-plant-scada
industrial.target.http.uri=http://127.0.0.1:18080/api/scada/telemetry
industrial.target.http.connectTimeout=5000
industrial.target.http.socketTimeout=30000
industrial.log.max.body.length=1000
```

`server.running=false` 是安全默认值。现场配置真实连接后再改为 `true`。

## OPC UA

配置：

```properties
service.name=AvevaOpcUaSrv
service.version=v1.0.0
service.type=SCADA
service.impl=OPCUA

industrial.opcua.endpoint.uri=tcp://127.0.0.1:4840
industrial.opcua.client.id=lightesb-aveva-opcua
industrial.opcua.read.node=ns=2;s=Plant.Area.Line1.Pump101.Speed
industrial.opcua.write.node=ns=2;s=Plant.Area.Line1.Pump101.SetPoint
industrial.opcua.username=PLACEHOLDER_CONFIGURE_IN_SITE
industrial.opcua.password=PLACEHOLDER_CONFIGURE_IN_SITE
industrial.opcua.security=PLACEHOLDER_CONFIGURE_IN_SITE
```

遥测路由：

```xml
<route id="aveva-opcua-read-telemetry" routeConfigurationId="globalError">
  <from uri="milo-client:{{industrial.opcua.endpoint.uri}}?node={{industrial.opcua.read.node}}&amp;clientId={{industrial.opcua.client.id}}-reader"/>
  <process ref="opcUaTelemetryNormalizeProcessor"/>
  <toD uri="{{industrial.target.http.uri}}?httpMethod=POST&amp;bridgeEndpoint=true&amp;connectTimeout={{industrial.target.http.connectTimeout}}&amp;socketTimeout={{industrial.target.http.socketTimeout}}"/>
</route>
```

写控制 API：

- `POST /api/aveva/opcua/write`
- 请求体：`{"value":55.5}`
- 只允许写 `industrial.opcua.write.node`，请求体不能包含 `node` 或 `topic`。

## MQTT 5

配置：

```properties
service.name=AvevaMqttSrv
service.version=v1.0.0
service.type=SCADA
service.impl=MQTT5

industrial.mqtt.broker.url=tcp://127.0.0.1:1883
industrial.mqtt.client.id=lightesb-aveva-mqtt
industrial.mqtt.telemetry.topic=aveva/plant/telemetry/line1
industrial.mqtt.command.topic=aveva/plant/command
industrial.mqtt.qos=1
industrial.mqtt.command.retained=false
industrial.mqtt.username=PLACEHOLDER_CONFIGURE_IN_SITE
industrial.mqtt.password=PLACEHOLDER_CONFIGURE_IN_SITE
industrial.mqtt.tls=PLACEHOLDER_CONFIGURE_IN_SITE
```

遥测路由：

```xml
<route id="aveva-mqtt-telemetry-consumer" routeConfigurationId="globalError">
  <from uri="paho-mqtt5:{{industrial.mqtt.telemetry.topic}}?brokerUrl={{industrial.mqtt.broker.url}}&amp;clientId={{industrial.mqtt.client.id}}-telemetry&amp;qos={{industrial.mqtt.qos}}&amp;userName={{industrial.mqtt.username}}&amp;password={{industrial.mqtt.password}}"/>
  <process ref="mqttTelemetryNormalizeProcessor"/>
  <toD uri="{{industrial.target.http.uri}}?httpMethod=POST&amp;bridgeEndpoint=true&amp;connectTimeout={{industrial.target.http.connectTimeout}}&amp;socketTimeout={{industrial.target.http.socketTimeout}}"/>
</route>
```

命令发布 API：

- `POST /api/aveva/mqtt/command`
- 请求体：`{"command":"start","deviceId":"Pump101"}`
- 只允许发布到 `industrial.mqtt.command.topic`，请求体不能包含 `topic` 或 `node`。

## 验证

1. 配置真实 OPC UA Server 或 MQTT 5 Broker。
2. 配置现场凭据、证书和安全策略。
3. 改 `server.running=true`。
4. 启动服务并确认路由为 `STARTED`。
5. 验证遥测下游收到标准 JSON。
6. 调用写控制 API，确认固定 node/topic 被写入或发布。

## 排障

- 找不到 processor：检查 `system.components` 是否包含 `industrial`。
- 路由启动失败：检查 Server/Broker 地址和凭据。
- MQTT 通配 topic：按 Camel URI 规则处理 `#` 等特殊字符。
- 写控制被拒绝：请求体不能动态指定 `node` 或 `topic`。
