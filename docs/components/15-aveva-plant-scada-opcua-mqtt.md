# AVEVA Plant SCADA OPC UA / MQTT / Modbus TCP 接入

本文说明交付包中如何通过 LightESB 接入 AVEVA Plant SCADA 的标准接口，并提供默认关闭的 Modbus TCP（PLC4X）只读模板。首版使用 `industrial` 轻封装：路由仍使用 Camel 原生 `milo-client:`、`paho-mqtt5:` 和 `plc4x:`，校验、脱敏、标准 JSON 和错误映射由 `industrial` processor 完成。

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
<route id="aveva-opcua-read-telemetry">
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
<route id="aveva-mqtt-telemetry-consumer">
  <from uri="paho-mqtt5:{{industrial.mqtt.telemetry.topic}}?brokerUrl={{industrial.mqtt.broker.url}}&amp;clientId={{industrial.mqtt.client.id}}-telemetry&amp;qos={{industrial.mqtt.qos}}&amp;userName={{industrial.mqtt.username}}&amp;password={{industrial.mqtt.password}}"/>
  <process ref="mqttTelemetryNormalizeProcessor"/>
  <toD uri="{{industrial.target.http.uri}}?httpMethod=POST&amp;bridgeEndpoint=true&amp;connectTimeout={{industrial.target.http.connectTimeout}}&amp;socketTimeout={{industrial.target.http.socketTimeout}}"/>
</route>
```

命令发布 API：

- `POST /api/aveva/mqtt/command`
- 请求体：`{"command":"start","deviceId":"Pump101"}`
- 只允许发布到 `industrial.mqtt.command.topic`，请求体不能包含 `topic` 或 `node`。

## Modbus TCP（PLC4X）只读模板

Camel 4.18 的 Modbus 路由使用 `plc4x:` consumer 和 PLC4X Modbus driver；`connection` 是完整的 PLC4X connection string，读取 tag 保持为配置值，不从消息体接收寄存器或 unit id。

```properties
HTTP.Listener=false
server.running=false
system.components=industrial

industrial.modbus.connection=PLACEHOLDER_CONFIGURE_IN_SITE
industrial.modbus.read.tag=PLACEHOLDER_CONFIGURE_IN_SITE
industrial.modbus.polling.ms=1000
```

```xml
<route id="modbus-read-route">
  <from uri="plc4x:{{industrial.modbus.connection}}?tag.holdingRegister={{industrial.modbus.read.tag}}&amp;period={{industrial.modbus.polling.ms}}"/>
  <to uri="servicelog:info?message=Modbus%20holding%20register%20read"/>
</route>
```

仅在现场确认 connection、只读 tag、unit id、地址偏移和数据类型后再改 `server.running=true`。该模板不包含写寄存器能力；本地 simulator 验证不构成 PLC、字节序、异常码或现场安全互锁的互操作结论。

## 验证

路由加载会自动应用全局错误处理；业务路由 XML 不需要手工声明 `routeConfigurationId="globalError"`。

无真实 Server/Broker 时先做离线 mock：

1. 使用 HTTP-only mock 入口构造 OPC UA write 请求，不连接 `milo-client:`。
2. 请求体只传 `value`，期望返回固定 `industrial.opcua.write.node` 摘要和 `externalWriteInvoked=false`。
3. 请求体带 `node` 或 `topic` 时，期望返回 `422`，错误码为动态目标拒绝。

示例：

```bash
curl -X POST "http://localhost:19189/api/doc-mock/aveva/opcua/write" \
  -H "Content-Type: application/json" \
  -d '{"value":55.5}'
```

动态 node 拒绝：

```bash
curl -X POST "http://localhost:19189/api/doc-mock/aveva/opcua/write" \
  -H "Content-Type: application/json" \
  -d '{"value":55.5,"node":"ns=9;s=Override"}'
```

真实联调时：

1. 配置真实 OPC UA Server 或 MQTT 5 Broker。
2. 配置现场凭据、证书和安全策略。
3. 改 `server.running=true`。
4. 启动服务并确认路由为 `STARTED`。
5. 验证遥测下游收到标准 JSON。
6. 调用写控制 API，确认固定 node/topic 被写入或发布。

离线 mock 只证明路由结构、固定目标边界和错误响应，不证明现场 OPC UA Server、MQTT Broker、证书或点位权限已完成互操作。

已获本地运行授权时，可用仅绑定回环地址的 Apache Milo OPC UA Mock 验证 `milo-client:` 的只读订阅和数值遥测标准化。处理器会将 OPC UA `DataValue` 的值转换为标准 JSON `value` 字段；该验证不覆盖现场 Server、认证、证书、复杂数据类型或业务点位语义。

## 排障

- 找不到 processor：检查 `system.components` 是否包含 `industrial`。
- 路由启动失败：检查 Server/Broker 地址和凭据。
- MQTT 通配 topic：按 Camel URI 规则处理 `#` 等特殊字符。
- 写控制被拒绝：请求体不能动态指定 `node` 或 `topic`。
