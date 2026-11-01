# Plug Native AI Bridge Protocol

**Status:** Phase 1–2 implementation. Discovery endpoints are implemented;
chat and Muk orchestration are not.

## 1. Protocol identity

- Protocol version: `plug-native-v1`
- Transport: HTTP over loopback only
- Default base URL: `http://127.0.0.1:8765`
- Authentication: shared bearer token supplied out-of-band through the
  `PLUG_BRIDGE_TOKEN` environment variable
- No cloud fallback, remote binding, API key provisioning, or automatic
  network discovery

The bridge must bind only to a loopback IP address. It rejects non-loopback
bind addresses.

## 2. Implemented endpoints

Every implemented endpoint requires:

```http
Authorization: Bearer <PLUG_BRIDGE_TOKEN>
```

### `GET /v1/health`

Example response:

```json
{
  "protocol_version": "plug-native-v1",
  "service": "ai-workplace-bridge",
  "status": "ok"
}
```

### `GET /v1/capabilities`

The manifest reports only discovery functionality. In this phase:

- `health`: true
- `capabilities`: true
- `chat`: false
- `planning`: false
- `task_decomposition`: false
- `tool_use`: false
- `streaming`: false
- `persistent_memory`: false

Example:

```json
{
  "protocol_version": "plug-native-v1",
  "service": "ai-workplace-bridge",
  "capabilities": {
    "health": true,
    "capabilities": true,
    "chat": false,
    "planning": false,
    "task_decomposition": false,
    "tool_use": false,
    "streaming": false,
    "persistent_memory": false
  },
  "endpoints": {
    "health": "GET /v1/health",
    "capabilities": "GET /v1/capabilities"
  }
}
```

Unknown paths and unsupported methods return HTTP 404. The server does not
provide a placeholder chat response.

## 3. Reserved chat payload schema (not an active endpoint)

The following shape is defined for future compatibility only. It is not
accepted by an HTTP endpoint in Phase 1–2.

Request:

```json
{
  "protocol_version": "plug-native-v1",
  "request_id": "req-001",
  "session_id": null,
  "message": "Prompt text",
  "context": [],
  "mode": "direct"
}
```

Response:

```json
{
  "protocol_version": "plug-native-v1",
  "request_id": "req-001",
  "status": "completed",
  "answer": "Response text",
  "tasks": [],
  "error": null
}
```

The Python schema validators reject unsupported protocol versions, invalid
request IDs, malformed fields, unknown fields, and mismatched response IDs.
These validators do not imply that a chat backend or endpoint exists.

## 4. Error shape

Implemented HTTP errors use a JSON object:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "valid bearer token required"
  }
}
```

Current error codes include `unauthorized` and `not_found`.

## 5. Running the discovery bridge

From the repository's `desktop/` directory, set a random secret of at least
32 characters in `PLUG_BRIDGE_TOKEN`, then run:

```bash
python -m app.bridge.server
```

Optional settings:

- `PLUG_BRIDGE_HOST`: defaults to `127.0.0.1`; non-loopback addresses are
  rejected.
- `PLUG_BRIDGE_PORT`: defaults to `8765`.

The same token must be configured in a future Plug client. Do not commit the
token or place it in source control. This phase does not yet implement that
client.

## 6. Not implemented

- Muk coordinator runtime
- AI inference backend for this bridge
- `POST /v1/chat`
- Task polling or cancellation
- Streaming
- Persistent sessions or memory
- Plug provider adapter
- Automatic discovery

No Gemini/cloud inference is called by this bridge.
