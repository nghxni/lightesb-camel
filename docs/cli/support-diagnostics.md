# Support Diagnostics

This guide is the external support runbook for LightESB CLI diagnostics. It uses generic placeholders and does not include internal demo service packages.

## Principles

- Start from the symptom, then choose commands.
- Prefer `--output json` for automation, Codex, and remote support.
- Use read-only commands for evidence collection.
- `diagnostics snapshot/warnings` does not reload routes, clean data, change log levels, or read the remote filesystem.
- Redact secrets and customer payloads before sharing output.

## Environment

```bash
lightesb profile current --output json
lightesb profile list --output json
lightesb doctor --server http://localhost:8080 --output json
lightesb diagnostics warnings --server http://localhost:8080 --output json
```

Use this path when CLI cannot connect, returns `401/403`, or diagnostics reports global warnings.

## Service And Route

```bash
lightesb service list --output json
lightesb route status --output json
lightesb route mapping --output json
lightesb route detail --file-key <fileKey> --output json
lightesb route config --file-key <fileKey> --output json
lightesb diagnostics snapshot --service-name <serviceName> --service-version <serviceVersion> --component route-runtime --output json
```

Check `serviceName`, `serviceVersion`, `fileKey`, routeId, CamelContext status, missing placeholders, disabled `server.running`, duplicate routeIds, and route-runtime warnings.

## Logs And Keywords

```bash
lightesb log status --output json
lightesb log health --output json
lightesb log instance list --service-name <serviceName> --service-version <serviceVersion> --output json
lightesb log instance list --service-name <serviceName> --service-version <serviceVersion> --keyword traceId=<traceId> --output json
lightesb keyword list --service-name <serviceName> --service-version <serviceVersion> --output json
lightesb keyword query-instances --service-name <serviceName> --service-version <serviceVersion> --key-name traceId --json-value <traceId> --output json
```

Use logs to correlate `requestId`, `traceId`, `exchangeId`, routeId, service version, HTTP status, and business error codes. Do not share full request or response bodies unless they are sanitized test payloads.

## Common Diagnosis Paths

| Symptom | Commands | Evidence | Next step |
| --- | --- | --- | --- |
| CLI cannot connect | `profile current`, `doctor` | server, exit code, requestId | Fix server/profile/network/backend state |
| Route is not running | `route status`, `route detail`, `diagnostics snapshot --component route-runtime` | fileKey, routeId, CamelContext, warning | Fix XML/config and reload |
| Missing config | `route config`, `route detail` | missing key name only | Restore config and reload the affected route file or service config |
| No instance logs | `log health`, `diagnostics snapshot --component instance-log` | writer/query storage state | Fix log storage or fallback mode |
| Downstream failed | `log instance list --keyword traceId=...` | downstream name, error code, timeout summary | Check downstream network/account/business status |
| Authorization failed | `doctor`, logs by traceId/requestId | HTTP 401/403, requestId | Check gateway and API authorization |
| AI route issue | `ai route cache status`, `diagnostics snapshot --component ai-route-cache`, `diagnostics snapshot --component ai-model-session` | provider/modelRef if observable, duration, failure class | Treat AI output as a candidate; review before apply |
| Robot command issue | `robot doctor --offline`, `robot command validate/status`, `diagnostics snapshot --component robot-command` | robotId, commandId, outbox status | Validate dispatcher/protocol closure separately |

## Recovery

For route XML or service configuration changes:

```bash
lightesb route reload-file --file-path <serverRouteXmlPath> --yes
lightesb route reload-service --service-name <serviceName> --service-version <versionWithoutLeadingV> --yes
lightesb diagnostics warnings --output json
```

Restart the backend only when Java code, dependencies, Spring beans, global configuration, or startup parameters changed, or when hot reload fails and state is inconsistent.

## Evidence Template

```text
Symptom:
Impact:
serviceName/serviceVersion:
fileKey/routeId:
Time:
requestId/traceId/exchangeId:
Key CLI output summary:
Diagnostics warning summary:
Recovery actions tried:
Next ownership:
```

## Redaction

Do not share:

- `password`
- `token`
- `secret`
- `credential`
- `authorization`
- `apiKey`
- `accessKey`
- `secretKey`
- full prompts, model responses, payloads, XML, properties, connection strings, usernames, customer data, or local absolute paths.

You may share service names, versions, routeIds, fileKeys, requestId, traceId, exchangeId, HTTP status, error codes, warning summaries, and sanitized configuration key names.
