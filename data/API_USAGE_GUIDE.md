# JCBA Internet Simul Radio - API Usage Guide v3

> For developers who just want to capture radio streams. No theory, no failures, just what works.

---

## ⚠️ Critical: Token Expiry

> **JWT Tokens expire in JUST 15 SECONDS!** Get a new token immediately if you need more time.

---

## TL;DR — Minimum Code to Capture

```python
import requests
import asyncio
import websockets
import json

async def capture(url: str, token: str, duration: int = 10) -> bytes:
    """Capture audio for specified duration. Returns raw Ogg bytes."""
    ws = await websockets.connect(
        url,
        subprotocols=["listener.fmplapla.com"],
        additional_headers={"Authorization": f"Bearer {token}"}
    )
    await ws.send(token)
    
    chunks = []
    end = asyncio.get_event_loop().time() + duration
    while asyncio.get_event_loop().time() < end:
        data = await asyncio.wait_for(ws.recv(), timeout=1)
        if isinstance(data, bytes):
            chunks.append(data)
    
    await ws.close()
    return b"".join(chunks)  # raw Ogg/Vorbis bytes

async def main():
    # Get streaming URL and token
    resp = requests.post(
        "https://api.radimo.smen.biz/api/v1/select_stream",
        params={
            "station": "fmhana",       # Station ID from stations.json
            "channel": "0",            # Always "0" (no multi-channel)
            "quality": "high",         # "high" or "low"
            "burst": "5"               # Initial buffer size (use "5")
        },
        json={"station": "fmhana"}
    )
    
    stream_url = resp.json()["location"]
    token = resp.json()["token"]
    
    # ⚠️ TOKEN EXPIRES IN 15 SECONDS!
    # Get new token immediately for continuous streaming
    audio = await capture(stream_url, token, duration=10)
    print(f"Captured {len(audio)} bytes")
    
    # For longer recordings, get NEW token every 10 seconds
    while recording:
        resp = requests.post(...)  # Repeat API call
        token = resp.json()["token"]
        audio = await capture(stream_url, token, duration=10)
```

---

## Quick Reference

| Item | Value |
|---|---|
 | API endpoint | `POST https://api.radimo.smen.biz/api/v1/select_stream` |
 | Params | `station` (required), `channel="0"`, `quality="high"` or `"low"`, `burst` (int) |
 | Body | `{"station": "<id>"}` |
 | Streaming URL | `data["location"]` (WebSocket) |
 | Token | `data["token"]` (JWT, **valid 15s!**) |
 | Auth | `Bearer {token}` in `additional_headers` |
 | Subproto | `["listener.fmplapla.com"]` (required) |
 | Audio format | Ogg/Vorbis (not WAV!) |
 | CDN nodes | `os13xx` (Osaka) / `ts13xx` (Tokyo) — dynamic |
 | Quality diff | ~2% throughput (not meaningful) |
 | Valid stations | 142 stations in `stations.json` |

---

## Recording Implementation

### Continuous Recording

```python
import requests
import asyncio
import websockets

async def continuous_recording(station: str, filename: str, duration: int):
    """Record radio for specified seconds."""
    resp = requests.post(
        "https://api.radimo.smen.biz/api/v1/select_stream",
        params={"station": station, "channel": "0", "quality": "high", "burst": "5"},
        json={"station": station}
    )
    
    stream_url = resp.json()["location"]
    current_token = resp.json()["token"]
    
    with open(filename, "wb") as f:
        end = asyncio.get_event_loop().time() + duration
        ws = None
        
        try:
            ws = await websockets.connect(
                stream_url,
                subprotocols=["listener.fmplapla.com"],
                additional_headers={"Authorization": f"Bearer {current_token}"}
            )
            await ws.send(current_token)
            
            while asyncio.get_event_loop().time() < end:
                # Get new token every 10 seconds
                if time.time() - start_time > 10:
                    resp = requests.post(
                        "https://api.radimo.smen.biz/api/v1/select_stream",
                        params={"station": station, "channel": "0", "quality": "high", "burst": "5"},
                        json={"station": station}
                    )
                    current_token = resp.json()["token"]
                    await ws.close()
                    ws = await websockets.connect(
                        stream_url,
                        subprotocols=["listener.fmplapla.com"],
                        additional_headers={"Authorization": f"Bearer {current_token}"}
                    )
                    await ws.send(current_token)
                
                data = await ws.recv()
                if isinstance(data, bytes):
                    f.write(data)  # Append to recording file
        finally:
            if ws:
                await ws.close()
```

### Ogg to MP3 Conversion

```python
import subprocess
subprocess.run([
    "ffmpeg", "-y",
    "-i", "recording.ogg",
    "-c:a", "libmp3lame", "-q:a", "2",
    "recording.mp3"
])
```

---

## Important Notes

1. **⚠️ Token expires every 15 seconds** — call API every 10 seconds to get new token
2. **`burst` is just initial buffer** — use `"5"` for most cases
3. **Same token can reconnect** — no need to re-request if connection drops within 15s
4. **OggS frames in response** — handle as binary, not text
5. **No channel support** (`channel="0"` only)
6. **No format selection** — always Ogg/Vorbis
7. **No metadata** — no track info available
8. **No seek/rewind** — real-time only
9. **Connection drops** require re-connection
10. **CDN routing** is dynamic — don't cache URLs

---

## Station List

Get from: `https://github.com/goura32/fm-recorder/blob/main/data/stations.json`

---

## Known Limitations

1. **Tokens expire every 15 seconds** — continuous recording requires frequent API calls
2. Some stations return HTTP 404 (unconfirmed status)
3. No metadata (track info) available
4. No seek/rewind during stream
5. Connection drops require re-connection

---

## Version History

- v1 (2026-05-20): Initial release
- v2 (2026-05-20): Added token lifespan (15s), reconnection test results
- v3 (2026-05-20): Added continuous recording implementation, Ogg to MP3 conversion
