# AURRA Developer Integration Handout

*Version 1.0.0 · REST API · OAuth 2.0 · Webhooks · SDK · Base URL: `api.aurrahome.com/v1`*

Complete guide to integrating with the AURRA Smart Thermostat API — authentication, telemetry endpoints, predictive maintenance, webhooks, and ready-to-run code samples.

- **Endpoints:** 12
- **Rate limit:** 500 req/min
- **Scopes:** 4

## Integration Overview

The AURRA REST API provides full programmatic access to thermostat control, predictive HVAC diagnostics, energy ecosystem management, and real-time event webhooks. All endpoints use OAuth 2.0 Bearer token authentication and return JSON.

### Base URL

```
https://api.aurrahome.com/v1
```

### API Surface

| Category | Description |
|---|---|
| Thermostat Control | Read status, set temperature, create schedules, toggle Eco Mode. |
| Predictive Maintenance | Submit diagnostics telemetry; receive ML-powered failure predictions. |
| Comfort Optimization | AI-driven temperature adjustment using occupancy and weather signals. |
| Energy Ecosystem | Solar, grid pricing, and EV integration for whole-home load balancing. |
| Alerts & Webhooks | Push alert creation, technician dispatch, real-time event streaming. |
| Voice Integration | Link Alexa, Google Assistant, and HomeKit accounts programmatically. |

### Required OAuth Scopes

| Scope | Access Level | Typical Use |
|---|---|---|
| diagnostics:read | Read | Fetch HVAC telemetry and maintenance predictions |
| alerts:write | Write | Create and dispatch maintenance alerts |
| energy:read | Read | Access solar, grid pricing, and EV data |
| comfort:write | Write | Adjust temperature setpoints and schedules |

> **Note:** Scope strings must be passed during OAuth token generation. Request only the scopes your integration requires — the principle of least privilege applies.

## Authentication

AURRA uses the OAuth 2.0 client credentials flow. All API calls require a Bearer token in the Authorization header. Tokens expire after 3,600 seconds and must be refreshed before expiry.

**POST /auth/token** — Generate an OAuth 2.0 access token

**Request Body**

| Parameter | Type | Required | Description |
|---|---|---|---|
| client_id | string | Required | Application client ID from the AURRA Developer Portal |
| client_secret | string | Required | Application client secret — never expose client-side |
| grant_type | string | Required | Must be the literal value `client_credentials` |

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

**Python — Authentication Helper**

```python
import requests

def get_token(client_id, client_secret):
    resp = requests.post(
        "https://api.aurrahome.com/v1/auth/token",
        json={
            "client_id":     client_id,
            "client_secret": client_secret,
            "grant_type":    "client_credentials"
        }
    )
    return resp.json()["access_token"]

TOKEN   = get_token(CLIENT_ID, CLIENT_SECRET)
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
```

> **Warning:** Never expose your `client_secret` in client-side code or public repositories. Store credentials in environment variables or a secrets management service. Rotate compromised secrets immediately via the developer portal.

## Integration Workflow

A typical AURRA integration follows a five-step lifecycle from authentication to real-time monitoring. Each step maps to one or more API calls.

1. **Authenticate** — `POST /auth/token` → store the Bearer token with its expiry timestamp. *Tokens expire after 3,600 seconds. Implement auto-refresh before expiry to avoid 401 errors mid-session.*
2. **Fetch Device Status** — `GET /thermostat/{device_id}/status` → read current temperature, humidity, and mode. *Poll no more frequently than every 30 seconds to stay within rate limits.*
3. **Configure Comfort** — `POST /thermostat/{device_id}/setpoint` + `/schedule` → set target temperatures and time blocks. *Call `/schedule/sync` after bulk schedule updates to ensure device parity.*
4. **Submit Diagnostics** — `POST /diagnostics/vibration` + `/diagnostics/energy` → stream telemetry for ML analysis. *Recommended cadence: vibration every 60 seconds, energy every 5 minutes.*
5. **Monitor Alerts** — `GET /predictive/hvac/{device_id}/status` → check maintenance predictions and recommended actions. *Use webhooks (`POST /alerts`) for push-based alert delivery at scale — no polling required.*

## Predictive Maintenance API

AURRA's predictive maintenance endpoints are the platform's core differentiator. Submit sensor telemetry and receive ML-powered failure predictions with confidence scores and recommended actions — weeks before a breakdown occurs.

**POST /diagnostics/vibration** — Submit MEMS vibration telemetry

| Parameter | Type | Required | Description / Constraints |
|---|---|---|---|
| device_id | string | Required | Target thermostat device identifier |
| timestamp | string | Required | ISO 8601 UTC timestamp (e.g., 2025-04-22T14:00:00Z) |
| amplitude | float | Required | Peak vibration amplitude in g-force (range: 0.0–10.0) |
| frequency | float | Required | Dominant vibration frequency in Hz |
| duration_ms | integer | Optional | Sample window in milliseconds. Default: 1000 |

**POST /diagnostics/energy** — Submit HVAC runtime telemetry

| Parameter | Type | Required | Description / Constraints |
|---|---|---|---|
| device_id | string | Required | Target device identifier |
| runtime_mins | integer | Required | HVAC runtime in minutes for the reporting period |
| voltage | float | Required | Supply voltage reading in volts |
| current_amps | float | Required | Current draw in amperes |
| period_start | string | Required | ISO 8601 UTC start of reporting period |

**GET /predictive/hvac/{device_id}/status** — Retrieve ML-powered HVAC prediction

**Response Schema**

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

**POST /alerts** — Create and dispatch a maintenance alert

| Parameter | Type | Required | Description |
|---|---|---|---|
| device_id | string | Required | Target device identifier |
| issue | string | Required | Human-readable issue description (max 256 chars) |
| confidence | float | Required | ML confidence score (0.0–1.0). Platform default alert threshold: 0.72 |
| action | string | Required | Recommended remediation step for the homeowner |
| dispatch | boolean | Optional | If true, triggers automated technician dispatch (Enterprise tier only) |

> **Tip:** The confidence threshold of 0.72 is the platform default for alert dispatch. Enterprise integrations may configure custom thresholds via the developer portal.

## Comfort & Energy APIs

**GET /thermostat/{device_id}/status** — Read current temperature, humidity, mode, Eco status

```json
{ "temperature":73, "humidity":42, "mode":"heat", "eco_mode":false, "status":"active" }
```

**POST /thermostat/{device_id}/setpoint** — Set target temperature and HVAC mode

| Parameter | Type | Required | Description |
|---|---|---|---|
| temperature | integer | Required | Target setpoint in °F. Valid range: 40–90 |
| mode | string | Required | `heat \| cool \| auto \| off` |

```python
resp = requests.post(
    f"{BASE}/thermostat/aurra_001/setpoint",
    json={"temperature": 72, "mode": "cool"},
    headers=HEADERS
)
print(resp.json())
```

**POST /thermostat/{device_id}/schedule** — Create or replace a named temperature schedule

```json
{
  "name": "Workday Routine",
  "blocks": [
    { "label":"Morning", "start":"04:00", "end":"08:00",
      "heat":70, "cool":74, "days":["mon","tue","wed","thu","fri"] },
    { "label":"Day",     "start":"08:00", "end":"16:30",
      "heat":65, "cool":78, "days":["mon","tue","wed","thu","fri"] },
    { "label":"Evening", "start":"16:30", "end":"22:00",
      "heat":72, "cool":73, "days":["mon","tue","wed","thu","fri"] },
    { "label":"Night",   "start":"22:00", "end":"04:00",
      "heat":68, "cool":76, "days":["mon","tue","wed","thu","fri"] }
  ]
}
```

**POST /thermostat/{device_id}/eco** — Enable or disable Eco Mode

**POST /climate/optimize** — Trigger AI comfort optimization

## Webhooks & Event Streaming

Register a webhook endpoint to receive real-time push events from AURRA — no polling required. Events are delivered as HTTP POST requests with a JSON payload signed with your webhook secret.

### Supported Event Types

| Event Type | Trigger | Key Payload Fields |
|---|---|---|
| thermostat.temperature_change | Setpoint reached or manually overridden | device_id, old_temp, new_temp, mode |
| predictive.alert_created | ML confidence ≥ threshold → alert fired | device_id, issue, confidence, action |
| predictive.alert_resolved | Technician confirms issue resolved | device_id, alert_id, resolved_at |
| eco.mode_changed | Eco Mode toggled on or off | device_id, enabled, heat_limit, cool_limit |
| schedule.updated | New schedule applied to device | device_id, schedule_name, blocks_count |
| device.offline | Device loses connectivity for >5 minutes | device_id, last_seen, reason |

### Example Webhook Payload

```http
POST https://your-server.com/aurra/webhook
Content-Type: application/json
X-AURRA-Signature: sha256=<hmac_signature>

{
  "event":     "predictive.alert_created",
  "timestamp": "2025-04-22T14:33:10Z",
  "data": {
    "device_id":  "aurra_001",
    "issue":      "Compressor bearing degradation",
    "confidence": 0.87,
    "action":     "Schedule HVAC inspection within 14 days"
  }
}
```

### Signature Verification — Python

```python
import hmac, hashlib

def verify_signature(payload_bytes, header_sig, secret):
    expected = hmac.new(
        secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", header_sig)
```

> **Tip:** Always verify the `X-AURRA-Signature` header before processing webhook payloads. Reject any request where signature verification fails with a 401 response.

## SDK & Code Samples

AURRA provides official SDKs for Python and JavaScript, available via PyPI and npm respectively.

```bash
# Python
pip install aurra-sdk

# JavaScript / Node.js
npm install @aurra/sdk
```

### Python — Full Workflow Example

```python
import requests

BASE = "https://api.aurrahome.com/v1"

# 1. Authenticate
token_resp = requests.post(f"{BASE}/auth/token", json={
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type":    "client_credentials"
})
TOKEN   = token_resp.json()["access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 2. Get current thermostat status
status = requests.get(f"{BASE}/thermostat/aurra_001/status", headers=HEADERS).json()
print(f"Current: {status['temperature']}°F  Mode: {status['mode']}")

# 3. Set temperature
requests.post(f"{BASE}/thermostat/aurra_001/setpoint",
    json={"temperature": 72, "mode": "cool"}, headers=HEADERS)

# 4. Check predictive maintenance status
pred = requests.get(f"{BASE}/predictive/hvac/aurra_001/status", headers=HEADERS).json()
if pred["maintenance_needed"]:
    print(f"ALERT: {pred['prediction']['issue']}")
    print(f"Confidence: {pred['prediction']['confidence']:.0%}")
    print(f"Action: {pred['prediction']['recommended_action']}")
```

### JavaScript — Status & Setpoint

```javascript
const BASE = "https://api.aurrahome.com/v1";

// Fetch current thermostat status
const status = await fetch(`${BASE}/thermostat/aurra_001/status`, {
  headers: { Authorization: `Bearer ${ACCESS_TOKEN}` }
}).then(r => r.json());

console.log(`${status.temperature}°F | ${status.mode} | eco: ${status.eco_mode}`);

// Set temperature to 70°F, heating mode
await fetch(`${BASE}/thermostat/aurra_001/setpoint`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${ACCESS_TOKEN}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ temperature: 70, mode: "heat" })
});
```

## Rate Limits & Error Handling

### Rate Limits

| Tier | Limit | Scope | Response Header |
|---|---|---|---|
| Enterprise | 500 req/min | Per access token | X-RateLimit-Tier: enterprise |
| Standard | 100 req/min | Per access token | X-RateLimit-Tier: standard |
| Diagnostics | 60 req/min | POST /diagnostics/* | X-RateLimit-Endpoint: diag |

### HTTP Status Codes

| Status | Meaning | Common Cause & Resolution |
|---|---|---|
| 200 | OK | Request successful |
| 201 | Created | Resource created (POST alert, schedule) |
| 400 | Bad Request | Missing required field or invalid value — check request body against schema |
| 401 | Unauthorized | Missing, expired, or malformed Bearer token — request a new token |
| 403 | Forbidden | Token lacks required scope — re-authenticate with correct scopes |
| 404 | Not Found | device_id does not exist in your account — verify device ID |
| 429 | Too Many Requests | Rate limit exceeded — back off and retry with exponential delay |
| 500 | Internal Server Error | Unexpected platform error — retry with exponential backoff; contact support |

### Error Response Shape

```json
{
  "error": {
    "code":    "UNAUTHORIZED",
    "message": "Bearer token has expired. Request a new token.",
    "docs":    "https://docs.aurrahome.com/errors/UNAUTHORIZED"
  }
}
```

### Support & Resources

| Resource | Value |
|---|---|
| Developer Portal | docs.aurrahome.com/developers |
| API Status Page | status.aurrahome.com |
| Developer Support | devsupport@aurrahome.com |
| GitHub SDK + Examples | github.com/aurra-technologies/aurra-sdk |
