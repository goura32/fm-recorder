#!/usr/bin/env python3
"""
JCBA Simul Radio API - Comprehensive Test Suite
Tests 1: Token lifespan, Test 2: Audio format analysis, Test 3: Reconnection
"""
import requests
import asyncio
import time
import websockets
import json
import base64
import struct
import wave
import numpy as np

def get_stream(station_id, quality="high", burst="5"):
    params = {"station": station_id, "channel": "0", "quality": quality, "burst": str(burst)}
    body = {"station": station_id}
    resp = requests.post("https://api.radimo.smen.biz/api/v1/select_stream", params=params, json=body, timeout=10)
    return resp.json()

def decode_jwt_payload(token):
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        raw = base64.urlsafe_b64decode(parts[1] + "==")
        return json.loads(raw)
    except:
        return None

# ============================================================
# TEST 1: Token lifespan
# ============================================================
async def test_token_lifespan(station_id, quality="high"):
    data = get_stream(station_id, quality)
    if data.get("code") != 200:
        return {"station": station_id, "quality": quality, "error": "API error"}
    
    token = data["token"]
    ws_url = data["location"]
    payload = decode_jwt_payload(token)
    
    print(f"\n=== {station_id} quality={quality} ===")
    print(f"  JWT iat={payload['iat']} exp={payload['exp']} (t={time.strftime('%H:%M:%S', time.gmtime(payload['exp']))} UTC)")
    print(f"  Full exp={time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(payload['exp']))}")
    remaining = payload['exp'] - int(time.time())
    print(f"  Remaining: {remaining}s ({remaining/60:.1f}min)")
    
    async def measure():
        ws = None
        try:
            t0 = time.time()
            ws = await asyncio.wait_for(
                websockets.connect(ws_url, subprotocols=["listener.fmplapla.com"],
                                  additional_headers={"Authorization": f"Bearer {token}"}),
                timeout=15)
            await ws.send(token)
            
            chunks = 0
            total_bytes = 0
            errors = []
            end = t0 + 30
            
            while time.time() < end:
                try:
                    chunk = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    if isinstance(chunk, str):
                        try:
                            msg = json.loads(chunk)
                            if msg.get("type") == "status":
                                errors.append(msg.get("message", ""))
                        except:
                            pass
                        continue
                    sz = len(chunk)
                    chunks += 1
                    total_bytes += sz
                except asyncio.TimeoutError:
                    break
                except websockets.exceptions.ConnectionClosed as e:
                    errors.append(f"Closed: code={e.code} reason={e.reason}")
                    break
                except Exception as e:
                    errors.append(str(e)[:100])
                    break
            
            elapsed = time.time() - t0
            await ws.close()
            return {"received": 1 if chunks > 0 else 0, "chunks": chunks, "total_bytes": total_bytes,
                    "bytes_per_s": round(total_bytes / elapsed, 0) if elapsed > 0 else 0,
                    "duration": round(elapsed, 1), "errors": errors}
        except Exception as e:
            if ws: await ws.close()
            return {"received": 0, "error": str(e)[:200]}
    
    result = await measure()
    print(f"  Duration: {result['duration']}s | Chunks: {result['chunks']} | Bytes: {result['total_bytes']}")
    if result.get("errors"):
        for e in result["errors"]:
            print(f"    ERROR: {e}")
    
    return {
        "station": station_id, "quality": quality,
        "iat": payload["iat"], "exp": payload["exp"],
        "remaining_at_request": remaining,
        "lifespan": result
    }

# ============================================================
# TEST 2: Audio format analysis (OGG/Vorbis header parsing)
# ============================================================
async def test_audio_format(station_id, quality="high"):
    data = get_stream(station_id, quality)
    if data.get("code") != 200:
        return {"station": station_id, "quality": quality, "error": "API error"}
    
    token = data["token"]
    ws_url = data["location"]
    
    print(f"\n=== {station_id} quality={quality} ===")
    
    async def capture_audio():
        ws = None
        try:
            t0 = time.time()
            ws = await asyncio.wait_for(
                websockets.connect(ws_url, subprotocols=["listener.fmplapla.com"],
                                  additional_headers={"Authorization": f"Bearer {token}"}),
                timeout=15)
            await ws.send(token)
            
            # Capture first 10 chunks of binary data
            ogg_headers = []
            ogg_continuations = []
            total_bytes = 0
            captured = 0
            end = t0 + 5
            
            while time.time() < end and captured < 20:
                try:
                    chunk = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    if isinstance(chunk, str):
                        continue
                    sz = len(chunk)
                    total_bytes += sz
                    captured += 1
                    
                    # Check if this is an OggS header
                    if chunk[:4] == b"OggS":
                        ogg_headers.append({"size": sz, "position": captured,
                                          "version": chunk[4], "type": chunk[5],
                                          "burst": chunk[6], "serial": chunk[7:11].hex(),
                                          "segment_table_len": chunk[26]})
                    else:
                        ogg_continuations.append({"size": sz, "position": captured})
                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    break
            
            await ws.close()
            elapsed = time.time() - t0
            return {"total_bytes": total_bytes, "duration": elapsed,
                    "chunks": captured, "headers": ogg_headers,
                    "continuations": ogg_continuations,
                    "bytes_per_s": round(total_bytes / elapsed, 0) if elapsed > 0 else 0}
        except Exception as e:
            if ws: await ws.close()
            return {"total_bytes": 0, "error": str(e)[:200]}
    
    result = await capture_audio()
    if not result.get("headers"):
        print(f"  No OggS headers found (error: {result.get('error')})")
        if "error" not in result:
            return {"station": station_id, "quality": quality, "result": result, "error": "No Ogg headers"}
    
    # Deep dive into first Ogg header
    h = result["headers"][0]
    print(f"  Headers found: {len(result['headers'])}")
    print(f"  Total: {result['total_bytes']} bytes in {result['duration']}s ({result['bytes_per_s']} B/s)")
    print(f"  Chunk format: {result['chunks']} chunks")
    if h:
        print(f"  Header bytes: {h['size']} | version={h['version']} | type={h['type']} | serial={h['serial']}")
    
    return {"station": station_id, "quality": quality, "result": result, "ogg_headers": result.get("headers", [])}

# ============================================================
# TEST 3: Reconnection test
# ============================================================
async def test_reconnection(station_id, quality="high"):
    data = get_stream(station_id, quality)
    if data.get("code") != 200:
        return {"station": station_id, "quality": quality, "error": "API error"}
    
    token = data["token"]
    ws_url = data["location"]
    
    print(f"\n=== {station_id} quality={quality} ===")
    
    # First session
    ws1 = await websockets.connect(ws_url, subprotocols=["listener.fmplapla.com"],
                                   additional_headers={"Authorization": f"Bearer {token}"})
    await ws1.send(token)
    
    # Receive for 3 seconds
    t0 = time.time()
    session1_chunks = 0
    session1_bytes = 0
    while time.time() - t0 < 3:
        try:
            chunk = await asyncio.wait_for(ws1.recv(), timeout=0.5)
            if isinstance(chunk, str):
                continue
            session1_bytes += len(chunk)
            session1_chunks += 1
        except asyncio.TimeoutError:
            break
    
    session1_duration = time.time() - t0
    print(f"  Session 1: {session1_chunks} chunks, {session1_bytes} bytes, {session1_duration:.1f}s")
    await ws1.close()
    
    # Wait 3 seconds, then reconnect with SAME token
    print("  Reconnecting with SAME token...")
    await asyncio.sleep(3)
    
    ws2 = await websockets.connect(ws_url, subprotocols=["listener.fmplapla.com"],
                                   additional_headers={"Authorization": f"Bearer {token}"})
    await ws2.send(token)
    
    session2_chunks = 0
    session2_bytes = 0
    session2_duration = time.time()
    while time.time() - session2_duration < 3:
        try:
            chunk = await asyncio.wait_for(ws2.recv(), timeout=0.5)
            if isinstance(chunk, str):
                continue
            session2_bytes += len(chunk)
            session2_chunks += 1
        except asyncio.TimeoutError:
            break
    
    session2_duration = time.time() - session2_duration
    print(f"  Session 2 (reconnect): {session2_chunks} chunks, {session2_bytes} bytes, {session2_duration:.1f}s")
    
    # Check if token is still valid from first get_stream call
    # by re-connecting again
    print("  Reconnecting again with SAME token...")
    await asyncio.sleep(3)
    
    try:
        ws3 = await websockets.connect(ws_url, subprotocols=["listener.fmplapla.com"],
                                       additional_headers={"Authorization": f"Bearer {token}"})
        await ws3.send(token)
        session3_chunks = 0
        session3_bytes = 0
        session3_duration = time.time()
        while time.time() - session3_duration < 3:
            try:
                chunk = await asyncio.wait_for(ws3.recv(), timeout=0.5)
                if isinstance(chunk, str):
                    continue
                session3_bytes += len(chunk)
                session3_chunks += 1
            except asyncio.TimeoutError:
                break
        session3_duration = time.time() - session3_duration
        print(f"  Session 3 (reconnect #2): {session3_chunks} chunks, {session3_bytes} bytes, {session3_duration:.1f}s")
        await ws3.close()
        token_valid_after_3_reconnects = True
    except Exception as e:
        print(f"  Session 3 FAILED: {e}")
        token_valid_after_3_reconnects = False
    
    await ws2.close()
    
    return {
        "station": station_id, "quality": quality,
        "session1_bytes": session1_bytes, "session2_bytes": session2_bytes, "session3_bytes": session3_bytes,
        "token_valid_after_3_reconnects": token_valid_after_3_reconnects
    }

# ============================================================
# Run all tests
# ============================================================
async def main():
    stations = ["fmhana", "fmshinagawa", "hitsfm"]
    
    # Test 1: Token lifespan
    print("=" * 60)
    print("  TEST 1: Token Lifespan")
    print("=" * 60)
    lifespan_results = []
    for s in ["high", "low"]:
        for station in stations:
            r = await test_token_lifespan(station, s)
            lifespan_results.append(r)
    await asyncio.sleep(1)  # Brief pause between tests
    
    # Test 2: Audio format
    print("\n" + "=" * 60)
    print("  TEST 2: Audio Format Analysis")
    print("=" * 60)
    format_results = []
    for s in ["high", "low"]:
        for station in stations:
            r = await test_audio_format(station, s)
            format_results.append(r)
    await asyncio.sleep(1)
    
    # Test 3: Reconnection
    print("\n" + "=" * 60)
    print("  TEST 3: Reconnection Test")
    print("=" * 60)
    reconnect_results = []
    for s in ["high", "low"]:
        for station in stations:
            r = await test_reconnection(station, s)
            reconnect_results.append(r)
    
    # Summary
    print("\n\n" + "=" * 60)
    print("  FINAL SUMMARY")
    print("=" * 60)
    print(f"\n--- Token Lifespan ---")
    for r in lifespan_results:
        if "error" not in r:
            print(f"  {r['station']:20s} quality={r['quality']:4s} exp={time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(r['exp']))}")
            print(f"    received={r['lifespan'].get('received', 'N/A')} | duration={r['lifespan'].get('duration', 'N/A')}s | errors={r['lifespan'].get('errors', [])}")
    
    print(f"\n--- Reconnection ---")
    for r in reconnect_results:
        req_remaining = r['remaining_at_request'] if 'remaining_at_request' in r else 'N/A'
        print(f"  {r['station']:20s} quality={r['quality']:4s} | s1={r['session1_bytes']:6d}B s2={r['session2_bytes']:6d}B s3={r['session3_bytes']:6d}B | valid={r['token_valid_after_3_reconnects']}")

asyncio.run(main())
