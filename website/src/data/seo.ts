export type RelatedArticle = {
  href: string;
  title: string;
};

export type ArticleSeo = {
  published: string;
  modified: string;
  section: string;
  related: RelatedArticle[];
};

const article = (published: string, modified: string, section: string, related: RelatedArticle[]): ArticleSeo => ({
  published,
  modified,
  section,
  related
});

export const articleSeoByPath: Record<string, ArticleSeo> = {
  "/articles/action-catalog-audit/": article("2026-08-12", "2026-08-21", "Operations and governance", [
    { href: "/articles/route-static-preflight/", title: "Route static preflight" },
    { href: "/articles/hardened-cli-runtime-config/", title: "Hardened runtime configuration and CLI boundaries" },
    { href: "/articles/runtime-diagnostics/", title: "Runtime diagnostics and troubleshooting" }
  ]),
  "/articles/ai-agent-order/": article("2026-08-12", "2026-08-21", "AI integration", [
    { href: "/articles/ai-agent-solo-budget/", title: "AI agent integration on a solo budget" },
    { href: "/articles/action-catalog-audit/", title: "Action catalog and operation audit" },
    { href: "/articles/robot-ai-approval/", title: "The robot AI approval gate" }
  ]),
  "/articles/ai-agent-solo-budget/": article("2026-08-12", "2026-08-21", "AI integration", [
    { href: "/articles/ai-agent-order/", title: "An LLM order assistant built from Camel routes" },
    { href: "/articles/platform-http-v3-jsonpath/", title: "JSONPath extraction at the HTTP entry" },
    { href: "/articles/robot-ai-approval/", title: "The robot AI approval gate" }
  ]),
  "/articles/cli-schema-validation-routes/": article("2026-08-12", "2026-08-21", "Operations and governance", [
    { href: "/articles/platform-http-v1-ds/", title: "Config-driven DataSonnet transformation" },
    { href: "/articles/route-static-preflight/", title: "Route static preflight" },
    { href: "/articles/hardened-cli-runtime-config/", title: "Hardened runtime configuration and CLI boundaries" }
  ]),
  "/articles/deployment-security/": article("2026-08-12", "2026-08-21", "Operations and governance", [
    { href: "/articles/service-runtime-transitions/", title: "Service start/stop and timeout governance" },
    { href: "/articles/hardened-cli-runtime-config/", title: "Hardened runtime configuration and CLI boundaries" },
    { href: "/articles/runtime-diagnostics/", title: "Runtime diagnostics and troubleshooting" }
  ]),
  "/articles/externaldb-mysql/": article("2026-08-12", "2026-08-21", "Core routes and data access", [
    { href: "/articles/http-listener-undertow/", title: "HTTP listener and Undertow request routing" },
    { href: "/articles/legacy-system-integration/", title: "Modernizing legacy integration" },
    { href: "/articles/platform-http-v1-ds/", title: "Config-driven DataSonnet transformation" }
  ]),
  "/articles/hardened-cli-runtime-config/": article("2026-08-12", "2026-08-21", "Operations and governance", [
    { href: "/articles/cli-schema-validation-routes/", title: "JSON Schema validation routes via CLI" },
    { href: "/articles/deployment-security/", title: "Deployment security with the management API" },
    { href: "/articles/runtime-diagnostics/", title: "Runtime diagnostics and troubleshooting" }
  ]),
  "/articles/http-listener-undertow/": article("2026-08-12", "2026-08-21", "Core routes and data access", [
    { href: "/articles/externaldb-mysql/", title: "External database routes with externaldb" },
    { href: "/articles/platform-http-v3-jsonpath/", title: "JSONPath extraction at the HTTP entry" },
    { href: "/articles/legacy-system-integration/", title: "Modernizing legacy integration" }
  ]),
  "/articles/legacy-system-integration/": article("2026-07-03", "2026-08-21", "Core routes and data access", [
    { href: "/articles/http-listener-undertow/", title: "HTTP listener and Undertow request routing" },
    { href: "/articles/externaldb-mysql/", title: "External database routes with externaldb" },
    { href: "/articles/opcua-vda5050-industrial/", title: "OPC UA and VDA 5050 industrial ingress" }
  ]),
  "/articles/opcua-vda5050-industrial/": article("2026-08-12", "2026-08-21", "Industrial protocols", [
    { href: "/articles/robot-command-dispatcher/", title: "Robot command dispatcher and audit archive" },
    { href: "/articles/externaldb-mysql/", title: "External database routes with externaldb" },
    { href: "/articles/legacy-system-integration/", title: "Modernizing legacy integration" }
  ]),
  "/articles/platform-http-v1-ds/": article("2026-08-12", "2026-08-21", "Data transformation", [
    { href: "/articles/platform-http-v2-dts/", title: "Pluggable DTS via SPI and DataSonnet" },
    { href: "/articles/platform-http-v3-jsonpath/", title: "JSONPath order transformation" },
    { href: "/articles/externaldb-mysql/", title: "External database routes with externaldb" }
  ]),
  "/articles/platform-http-v2-dts/": article("2026-08-12", "2026-08-21", "Data transformation", [
    { href: "/articles/platform-http-v1-ds/", title: "Config-driven DataSonnet transformation" },
    { href: "/articles/platform-http-v3-jsonpath/", title: "JSONPath order transformation" },
    { href: "/articles/cli-schema-validation-routes/", title: "JSON Schema validation routes via CLI" }
  ]),
  "/articles/platform-http-v3-jsonpath/": article("2026-08-12", "2026-08-21", "Data transformation", [
    { href: "/articles/platform-http-v1-ds/", title: "Config-driven DataSonnet transformation" },
    { href: "/articles/platform-http-v2-dts/", title: "Pluggable DTS via SPI and DataSonnet" },
    { href: "/articles/http-listener-undertow/", title: "HTTP listener and Undertow request routing" }
  ]),
  "/articles/robot-ai-approval/": article("2026-07-30", "2026-08-21", "Robotics and AI", [
    { href: "/articles/robot-command-dispatcher/", title: "Robot command dispatcher and audit archive" },
    { href: "/articles/robot-security-policy/", title: "Robot shared safety policy" },
    { href: "/articles/ai-agent-order/", title: "An LLM order assistant built from Camel routes" }
  ]),
  "/articles/robot-command-dispatcher/": article("2026-08-12", "2026-08-21", "Robotics and AI", [
    { href: "/articles/robot-security-policy/", title: "Robot shared safety policy" },
    { href: "/articles/robot-ai-approval/", title: "The robot AI approval gate" },
    { href: "/articles/opcua-vda5050-industrial/", title: "OPC UA and VDA 5050 industrial ingress" }
  ]),
  "/articles/robot-security-policy/": article("2026-08-12", "2026-08-21", "Robotics and AI", [
    { href: "/articles/robot-command-dispatcher/", title: "Robot command dispatcher and audit archive" },
    { href: "/articles/robot-ai-approval/", title: "The robot AI approval gate" },
    { href: "/articles/hardened-cli-runtime-config/", title: "Hardened runtime configuration and CLI boundaries" }
  ]),
  "/articles/route-static-preflight/": article("2026-08-12", "2026-08-21", "Operations and governance", [
    { href: "/articles/cli-schema-validation-routes/", title: "JSON Schema validation routes via CLI" },
    { href: "/articles/runtime-diagnostics/", title: "Runtime diagnostics and troubleshooting" },
    { href: "/articles/hardened-cli-runtime-config/", title: "Hardened runtime configuration and CLI boundaries" }
  ]),
  "/articles/runtime-diagnostics/": article("2026-08-12", "2026-08-21", "Operations and governance", [
    { href: "/articles/deployment-security/", title: "Deployment security with the management API" },
    { href: "/articles/service-runtime-transitions/", title: "Service start/stop and timeout governance" },
    { href: "/articles/action-catalog-audit/", title: "Action catalog and operation audit" }
  ]),
  "/articles/service-runtime-transitions/": article("2026-08-12", "2026-08-21", "Operations and governance", [
    { href: "/articles/deployment-security/", title: "Deployment security with the management API" },
    { href: "/articles/runtime-diagnostics/", title: "Runtime diagnostics and troubleshooting" },
    { href: "/articles/route-static-preflight/", title: "Route static preflight" }
  ]),
  "/articles/temp-form-route-sample/": article("2026-07-17", "2026-08-21", "Core routes and data access", [
    { href: "/articles/http-listener-undertow/", title: "HTTP listener and Undertow request routing" },
    { href: "/articles/legacy-system-integration/", title: "Modernizing legacy integration" },
    { href: "/articles/deployment-security/", title: "Deployment security with the management API" }
  ]),
  "/articles/timer-v1-0-1/": article("2026-08-12", "2026-08-21", "Core routes and data access", [
    { href: "/articles/http-listener-undertow/", title: "HTTP listener and Undertow request routing" },
    { href: "/articles/runtime-diagnostics/", title: "Runtime diagnostics and troubleshooting" },
    { href: "/articles/route-static-preflight/", title: "Route static preflight" }
  ])
};
