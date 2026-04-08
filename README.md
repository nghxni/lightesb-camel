# 轻量Camel接口管理

使用 Apache Camel 构建的轻量 ESB 接口管理与监控平台，支持 AI Agent 模式，可直接复用存量系统 API。

核心能力：
- HTTP 接口暴露与服务编排（Undertow、Route Loader 生命周期）
- 统一日志、动态日志调级与链路观测（CamelServiceLog、指标采集）
- 数据转换与校验（ConditionalTransform、JsonTransform、JSON Schema）
- 安全与权限（IP/CIDR/Token 校验、核心安全包约束）
- 数据访问与缓存（ExternalDB、多数据源、H2 缓存与关键字检索）
- 异常兜底与全局处理链
- AI 扩展能力（LangChain4j + Camel、AI Chat 框架）
- 第三方 DTS SPI 扩展接入与最小模板落地



# lightesb-camel
A lightweight ESB interface management and monitoring platform built on Apache Camel. It supports AI Agent mode and can directly reuse APIs from legacy systems.

Key capabilities :
- HTTP exposure and service orchestration (Undertow, route loader lifecycle)
- Unified logging, dynamic log level control, and observability (CamelServiceLog, metrics collector)
- Data transform and validation (ConditionalTransform, JsonTransform, JSON Schema)
- Security and access control (IP/CIDR/Token checks, core secure package rules)
- Data access and cache flow (ExternalDB, multi-datasource, H2 cache + keyword search)
- Global exception fallback chain
- AI integration (LangChain4j + Camel, AI chat framework)
- Third-party DTS SPI extension and minimal template

