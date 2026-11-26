# StreamCache 流缓存（已移除）

`lightesb-streamcache` 组件已从运行包中移除。本页只提供升级迁移说明。

## 升级迁移

1. 检查路由 XML：如仍有 `<to uri="lightesb-streamcache://...">`，删除该端点，否则路由会因找不到组件而加载失败。
2. 检查 `common.config.properties`：从 `system.components` 中删除 `streamcache`。该配置项已不再受理，保留会报"未识别的system.components: streamcache"并导致服务加载失败。
3. 报文留存改用实例日志：在路由中使用 `h2LogCacheProcessor`，请求/响应报文写入实例日志表，见 [H2 缓存与 JsonKeyword](10-h2-jsonkeyword-chain.md)。
4. 现场已有的 `lightesb-StreamCache` 目录仍会被排除在路由文件监听之外，确认无需留存后可手工清理。

`lightesb.cache.*` 中除 `lightesb.cache.base-directory` 外的配置不再生效，可从配置中移除。
