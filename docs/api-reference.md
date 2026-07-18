# AURRA API Reference Guide

*Version 1.0.0 · REST · OAuth 2.0 Bearer · Base URL: `api.aurrahome.com/v1`*

Complete endpoint documentation for the AURRA Smart Thermostat API. Every endpoint includes parameter schemas, example requests, response shapes, and Python + JavaScript code samples.

- **Endpoints:** 12
- **Rate limit:** 500 req/min
- **Scopes:** 4
- **Auth type:** JWT

## Authentication

### POST /auth/token

Exchange client credentials for a short-lived RS256-signed Bearer token. Required before any other API call. Tokens expire after 3,600 seconds.

**Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| client_id | string | Required | Application client ID from the AURRA Developer Portal |
| client_secret | string | Required | Application client secret — never expose on client side |
| grant_type | string | Required | Must be the literal value `client_credentials` |

> **Warning:** Never expose `client_secret` in client-side code. Store credentials in environment variables or a secrets management service.

**Request**

```http
POST https://api.aurrahome.com/v1/auth/token
Content-Type: application/json

{
  "client_id":     "acc_a1b2c3d4",
  "client_secret": "sk_live_••••••••••••",
  "grant_type":    "client_credentials"
}
```

**Response — 200 OK**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type":   "Bearer",
  "expires_in":   3600
}
```

**Response — 401 Unauthorized**

```json
{ "error": { "code": "INVALID_CREDENTIALS", "message": "Bad client_id or client_secret" } }
```

**Code — Python**

```python
import requests
r = requests.post("https://api.aurrahome.com/v1/auth/token",
    json={"client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,"grant_type":"client_credentials"})
TOKEN = r.json()["access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
```

**Code — JavaScript**

```javascript
const {access_token} = await fetch("https://api.aurrahome.com/v1/auth/token",{
  method:"POST",headers:{"Content-Type":"application/json"},
  body:JSON.stringify({client_id:CLIENT_ID,client_secret:CLIENT_SECRET,grant_type:"client_credentials"})
}).then(r=>r.json());
```

## Thermostat Control

### GET /thermostat/{device_id}/status

Returns the current operational state of the specified thermostat including live temperature, humidity, active mode, and Eco Mode status.

**Parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| device_id | string (path) | Required | Unique thermostat identifier (e.g., `aurra_001`) |

Response fields: `temperature` (integer °F), `humidity` (integer 0–100%), `mode` (heat\|cool\|auto\|off), `eco_mode` (boolean), `status` (active\|idle\|offline)

**Response — 200 OK**

```json
{ "temperature":73, "humidity":42, "mode":"heat", "eco_mode":false, "status":"active" }
```

**Code — Python**

```python
s = requests.get(f"{BASE}/thermostat/aurra_001/status",headers=HEADERS).json()
print(f"{s['temperature']}°F | {s['mode']} | eco={s['eco_mode']}")
```

**Code — JavaScript**

```javascript
const s = await fetch(`${BASE}/thermostat/aurra_001/status`,
  {headers:{Authorization:`Bearer ${TOKEN}`}}).then(r=>r.json());
console.log(`${s.temperature}°F  ${s.mode}  eco:${s.eco_mode}`);
```

### POST /thermostat/{device_id}/setpoint

Set target temperature and HVAC mode — applied within 30 seconds.

**Parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| temperature | integer | Required | Target setpoint in °F. Valid range: 40–90 |
| mode | string | Required | `heat \| cool \| auto \| off` |

**Request**

```json
{ "temperature": 72, "mode": "cool" }
```

**Response — 200 OK**

```json
{ "success": true, "applied_at": "2025-04-22T15:30:00Z" }
```

**Code — Python**

```python
requests.post(f"{BASE}/thermostat/aurra_001/setpoint",
    json={"temperature":72,"mode":"cool"},headers=HEADERS)
```

### POST /thermostat/{device_id}/schedule

Create or replace a named temperature schedule with time blocks.

**Request Body**

```json
{
  "name": "Workday Routine",
  "blocks": [
    { "label":"Morning","start":"04:00","end":"08:00","heat":70,"cool":74,"days":["mon","tue","wed","thu","fri"] },
    { "label":"Day",    "start":"08:00","end":"16:30","heat":65,"cool":78,"days":["mon","tue","wed","thu","fri"] },
    { "label":"Evening","start":"16:30","end":"22:00","heat":72,"cool":73,"days":["mon","tue","wed","thu","fri"] },
    { "label":"Night",  "start":"22:00","end":"04:00","heat":68,"cool":76,"days":["mon","tue","wed","thu","fri"] }
  ]
}
```

**Schema**

| Field | Type | Required | Description |
|---|---|---|---|
| name | string | Required | Schedule name (max 64 chars) |
| blocks[].label | string | Required | Block label, e.g. Morning, Day, Evening, Night |
| blocks[].start | string HH:MM | Required | Start time in 24-hour format |
| blocks[].end | string HH:MM | Required | End time in 24-hour format |
| blocks[].heat | integer | Required | Heating setpoint in °F |
| blocks[].cool | integer | Required | Cooling setpoint in °F |
| blocks[].days | array | Required | Day codes: mon tue wed thu fri sat sun |

### POST /thermostat/{device_id}/schedule/sync

Force-push stored schedule to device — call after bulk schedule updates.

No request body required. Returns `{ "synced": true, "synced_at": "..." }` on success.

### POST /thermostat/{device_id}/eco

Enable or disable Eco Mode with optional temperature limit overrides.

| Field | Type | Required | Description |
|---|---|---|---|
| enabled | boolean | Required | true to enable, false to disable |
| heat_limit | integer | Optional | Max heating setpoint in Eco Mode. Default: 62°F |
| cool_limit | integer | Optional | Min cooling setpoint in Eco Mode. Default: 78°F |

## Predictive Maintenance

Submit sensor telemetry to the ML pipeline and retrieve failure predictions with confidence scores weeks before a breakdown occurs.

### POST /diagnostics/vibration

Submit MEMS vibration telemetry — recommended cadence: every 60 seconds.

| Field | Type | Required | Description |
|---|---|---|---|
| device_id | string | Required | Target device identifier |
| timestamp | string | Required | ISO 8601 UTC (e.g., 2025-04-22T14:00:00Z) |
| amplitude | float | Required | Peak vibration in g-force (range: 0.0–10.0) |
| frequency | float | Required | Dominant frequency in Hz |
| duration_ms | integer | Optional | Sample window in ms. Default: 1000 |

**Request**

```json
{
  "device_id":   "aurra_001",
  "timestamp":   "2025-04-22T14:33:00Z",
  "amplitude":   0.42,
  "frequency":   58.3,
  "duration_ms": 1000
}
```

Response — 201 Created:

```json
{ "accepted": true, "reading_id": "rdg_x9k2p7" }
```

### POST /diagnostics/energy

Submit HVAC runtime and electrical telemetry — recommended cadence: every 5 minutes.

| Field | Type | Required | Description |
|---|---|---|---|
| device_id | string | Required | Target device identifier |
| runtime_mins | integer | Required | HVAC runtime in minutes for the reporting period |
| voltage | float | Required | Supply voltage in volts |
| current_amps | float | Required | Current draw in amperes |
| period_start | string | Required | ISO 8601 UTC start of reporting period |

### GET /predictive/hvac/{device_id}/status

Retrieve ML-powered HVAC failure prediction, confidence score, and recommended action.

**Response — 200 OK — Issue Detected**

```json
{
  "maintenance_needed": true,
  "prediction": {
    "issue":              "Compressor bearing degradation",
    "confidence":         0.87,
    "recommended_action": "Schedule HVAC inspection within 14 days"
  },
  "last_service": "2024-08-12"
}
```

**Response — 200 OK — No Issues Detected**

```json
{ "maintenance_needed": false, "prediction": null, "last_service": "2025-01-08" }
```

> **Tip:** Poll this endpoint no more than once per minute. For real-time alert delivery without polling, register a webhook for the `predictive.alert_created` event instead.

**Code — Python**

```python
pred = requests.get(f"{BASE}/predictive/hvac/aurra_001/status",headers=HEADERS).json()
if pred["maintenance_needed"]:
    print(f"ALERT: {pred['prediction']['issue']}")
    print(f"Confidence: {pred['prediction']['confidence']:.0%}")
```

### POST /alerts

Create and dispatch a maintenance alert to the homeowner.

| Field | Type | Required | Description |
|---|---|---|---|
| device_id | string | Required | Target device identifier |
| issue | string | Required | Human-readable issue description (max 256 chars) |
| confidence | float | Required | ML confidence score 0.0–1.0. Platform default alert threshold: 0.72 |
| action | string | Required | Recommended remediation step for the homeowner |
| dispatch | boolean | Optional | If true, triggers automated technician dispatch (Enterprise tier only) |
| priority | string | Optional | `low \| medium \| high \| critical`. Default: medium |

## Comfort & Energy

### POST /climate/optimize

Trigger AI comfort optimization using occupancy and weather data.

| Field | Type | Required | Description |
|---|---|---|---|
| device_id | string | Required | Target device identifier |
| mode | string | Optional | `comfort \| efficiency \| balanced`. Default: balanced |
| apply_immediate | boolean | Optional | Apply the optimized schedule immediately without approval |

**Response — 200 OK**

```json
{
  "optimized_schedule": {
    "name": "AI Optimized — 2025-04-22",
    "blocks": [ ... ],
    "projected_savings": "18%"
  },
  "requires_approval": true
}
```

### POST /integration/voice-assistant

Link an Alexa, Google Assistant, or HomeKit account to a device.

| Field | Type | Required | Description |
|---|---|---|---|
| device_id | string | Required | Target device identifier |
| platform | string | Required | `Alexa \| GoogleAssistant \| HomeKit` |
| user_token | string | Required | Platform OAuth user token — distinct from your AURRA client token |

> **Note:** The `user_token` is the homeowner's access token from the voice platform's own OAuth flow — not your AURRA `access_token`.

## Error Reference

All AURRA API errors follow a consistent envelope. The `error.code` field is machine-readable and safe to programmatically handle.

```json
{
  "error": {
    "code":    "RATE_LIMIT_EXCEEDED",
    "message": "You have exceeded 100 requests per minute.",
    "docs":    "https://docs.aurrahome.com/errors/RATE_LIMIT_EXCEEDED",
    "retry_after": 30
  }
}
```

| HTTP | Error Code | Meaning | Resolution |
|---|---|---|---|
| 400 | INVALID_REQUEST | Missing or malformed field | Check request body against schema |
| 400 | INVALID_TEMPERATURE | Setpoint outside 40–90°F range | Adjust temperature value |
| 401 | UNAUTHORIZED | Missing or expired Bearer token | Request a new token via /auth/token |
| 403 | INSUFFICIENT_SCOPE | Token missing required scope | Re-authenticate with correct scopes |
| 404 | DEVICE_NOT_FOUND | device_id not in your account | Verify device ID spelling and ownership |
| 429 | RATE_LIMIT_EXCEEDED | Request rate above tier limit | Back off; check X-RateLimit-* response headers |
| 500 | INTERNAL_ERROR | Unexpected platform error | Retry with exponential backoff; contact support |
| 503 | SERVICE_UNAVAILABLE | Temporary platform maintenance | Monitor status.aurrahome.com |

## Quick Reference — All Endpoints

| Method | Endpoint | Auth | Scope Required |
|---|---|---|---|
| POST | /auth/token | — | — |
| GET | /thermostat/{id}/status | ✓ | — |
| POST | /thermostat/{id}/setpoint | ✓ | comfort:write |
| POST | /thermostat/{id}/schedule | ✓ | comfort:write |
| POST | /thermostat/{id}/schedule/sync | ✓ | comfort:write |
| POST | /thermostat/{id}/eco | ✓ | comfort:write |
| POST | /diagnostics/vibration | ✓ | diagnostics:read |
| POST | /diagnostics/energy | ✓ | diagnostics:read |
| GET | /predictive/hvac/{id}/status | ✓ | diagnostics:read |
| POST | /alerts | ✓ | alerts:write |
| POST | /climate/optimize | ✓ | comfort:write |
| POST | /integration/voice-assistant | ✓ | comfort:write |
