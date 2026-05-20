#!/usr/bin/env python3
"""
opus Ogg/Vorbis analysis for JCBA API high/low comparison.
Parses OpusHead header from OggS frames to extract sample rate, channels, bitrate, etc.
"""
import sys
import time
import requests
import asyncio
import websockets
import struct

def get_stream(station_id, quality="high"):
    params = {"station": station_id, "channel": "0", "quality": quality, "burst": "5"}
    body = {"station": station_id}
    resp = requests.post("https://api.radimo.smen.biz/api/v1/select_stream", params=params, json=body, timeout=10)
    return resp.json()

def parse_opushead(content):
    """Parse OpusHead magic string + OpusHead header fields.
    
    OpusHead header format:
    [0:8]   = "OpusHead" magic string (for OpusTags it's "OpusTags")
    [8]     = version (1)
    [9]     = channel_count
    [10:12] = pre_skip (LE uint16)
    [12:16] = input_sample_rate (LE uint32)
    [16:18] = output_gain (LE int16, two's complement, in q7 format)
    [18]    = channel_mapping_family
    """
    if len(content) < 19 or content[0:8] != b'OpusHead':
        return None
    
    version = content[8]
    channel_count = content[9]
    pre_skip = struct.unpack_from('<H', content, 10)[0]
    input_sample_rate = struct.unpack_from('<I', content, 12)[0]
    output_gain = struct.unpack_from('<h', content, 16)[0]  # signed, q7
    channel_mapping_family = content[18]
    
    # Parse channel mapping (if channel_mapping_family > 0)
    channel_map = None
    if channel_mapping_family > 0:
        if len(content) > 19:
            num_streams = content[19]
            num_coupled = content[20] if len(content) > 20 else 0
            stream_table = content[21:21+num_streams] if len(content) > 21+num_streams else None
            if len(content) > 21+num_streams+num_coupled:
                coupled_table = content[21+num_streams:]
            else:
                coupled_table = []
            channel_map = {
                'num_streams': num_streams,
                'num_coupled': num_coupled,
                'stream_table': list(stream_table) if stream_table else [],
                'coupled_table': list(coupled_table) if len(coupled_table) is not None else [],
            }
    
    return {
        'version': version,
        'channel_count': channel_count,
        'pre_skip': pre_skip,
        'input_sample_rate': input_sample_rate,
        'output_gain': f"{output_gain} (q7)",
        'channel_mapping_family': channel_mapping_family,
        'channel_map': channel_map,
    }

async def capture_and_parse(station_id, quality):
    data = get_stream(station_id, quality)
    if data.get("code") != 200:
        return {"station": station_id, "quality": quality, "error": "API error"}
    
    token = data["token"]
    ws_url = data["location"]
    
    print(f"\n=== {station_id} quality={quality} ===")
    sys.stdout.flush()
    
    ws = await websockets.connect(ws_url, subprotocols=["listener.fmplapla.com"])
    await ws.send(token)
    
    raw_bytes = b""
    start = time.time()
    
    # Capture 3 seconds of audio
    for _ in range(8):
        try:
            chunk = await asyncio.wait_for(ws.recv(), timeout=1)
            if isinstance(chunk, (bytes, bytearray)):
                raw_bytes += bytes(chunk)
        except:
            break
    await ws.close()
    
    elapsed = time.time() - start
    page_count = 0
    opushead = None
    opustags = None
    audio_packet_count = 0
    
    pos = 0
    while pos + 27 <= len(raw_bytes) and page_count < 10:
        if raw_bytes[pos:pos+4] != b'OggS':
            pos += 1
            continue
        
        header_type = raw_bytes[pos + 5]
        num_segments = raw_bytes[pos + 26]
        seg_start = pos + 27
        
        if seg_start + num_segments > len(raw_bytes):
            break
        
        content_len = sum(raw_bytes[seg_start + j] for j in range(num_segments))
        content_start = seg_start + num_segments
        
        if content_start + content_len > len(raw_bytes):
            break
        
        content = raw_bytes[content_start:content_start + content_len]
        pos = content_start + content_len
        
        # Reconstruct first packet (may span multiple segments)
        pkt_start_offset = 0
        pkt_total = content[0:content_len]
        
        if len(pkt_total) > 0 and pkt_total[0] == ord('O') and len(pkt_total) > 8:
            magic = pkt_total[0:8]
            if magic == b'OpusHead':
                opushead = parse_opushead(pkt_total)
                page_count += 1
                print(f"\n  [OpusHead header detected!]")
                if opushead:
                    print(f"    version:             {opushead['version']}")
                    print(f"    channel_count:       {opushead['channel_count']}")
                    print(f"    pre_skip:            {opushead['pre_skip']} frames")
                    print(f"    input_sample_rate:   {opushead['input_sample_rate']} Hz")
                    print(f"    output_gain:         {opushead['output_gain']}")
                    print(f"    channel_mapping:     {opushead['channel_mapping_family']}")
            
            elif magic == b'OpusTags':
                opustags = {"len": len(pkt_total)}
                vendor_idx = 0
                # vendor string
                vendor_len = struct.unpack_from('<I', pkt_total, 8)[0]
                vendor_str = pkt_total[12:12+vendor_len].decode('utf-8', errors='replace')
                
                comment_count_offset = 12 + vendor_len
                comment_count = struct.unpack_from('<I', pkt_total, comment_count_offset)[0]
                
                c_offset = comment_count_offset + 4
                print(f"\n  [OpusTags detected] vendor={vendor_str}, {comment_count} comments")
                for c in range(min(comment_count, 5)):
                    if c_offset + 4 > len(pkt_total):
                        break
                    entry_len = struct.unpack_from('<I', pkt_total, c_offset)[0]
                    c_offset += 4
                    if entry_len > 0:
                        comment_entry = pkt_total[c_offset:c_offset+entry_len].decode('utf-8', errors='replace')
                        print(f"    [{c}]: {comment_entry}")
                    c_offset += entry_len
        
        else:
            # Audio packet (type 0xFC for Opus audio)
            if len(pkt_total) > 0:
                pt = pkt_total[0]
                if pt == 0xFC:  # Opus audio packet type
                    audio_packet_count += 1
        
        page_count += 1
    
    # Calculate actual bitrate
    if page_count > 0:
        actual_kbps = round(len(raw_bytes)*8/elapsed/1000, 1)
    else:
        actual_kbps = 0
    
    print(f"\n  total_bytes:     {len(raw_bytes)}")
    print(f"  capture_time:    {elapsed:.1f}s")
    print(f"  audio_packets:   {audio_packet_count}")
    print(f"  actual_bitrate:  {actual_kbps} kbps")
    print(f"  opushead:        {opushead is not None}")
    print(f"  opustags:        {opustags is not None}")
    
    return {
        "station": station_id,
        "quality": quality,
        "opushead": opushead,
        "opustags": opustags,
        "actual_kbps": actual_kbps,
        "audio_packets": audio_packet_count,
        "total_bytes": len(raw_bytes),
    }

async def main():
    print("=" * 72)
    print("  Opus Codec Analysis for JCBA API (high vs low quality)")
    print("=" * 72)
    sys.stdout.flush()
    
    results = {}
    for s in ["fmhana", "fmshinagawa", "hitsfm"]:
        for q in ["high", "low"]:
            r = await capture_and_parse(s, q)
            results[(s, q)] = r
    
    # Summary table
    print("\n" + "=" * 72)
    print("  SUMMARY: Opus Codec Parameters")
    print("=" * 72)
    print(f"  {'Station':<16} {'Quality':<8} {'SR':<10} {'CH':<6} {'PreSkip':<10} {'ActualBR':<12}")
    print("  " + "-" * 62)
    
    for s in ["fmhana", "fmshinagawa", "hitsfm"]:
        for q in ["high", "low"]:
            r = results[(s, q)]
            oh = r.get('opushead', {})
            if oh:
                print(f"  {s:<16} {q:<8} {oh['input_sample_rate']:<10} {oh['channel_count']:<6} {oh['pre_skip']:<10} {r['actual_kbps']:<12} kbps")
    
    # Comparison table
    print("\n  DIFF (high - low):")
    for s in ["fmhana", "fmshinagawa", "hitsfm"]:
        rh = results[(s, 'high')]
        rl = results[(s, 'low')]
        ho = rh.get('opushead', {})
        lo = rl.get('opushead', {})
        
        sr_d = ho.get('input_sample_rate', 0) - lo.get('input_sample_rate', 0)
        ch_d = ho.get('channel_count', 0) - lo.get('channel_count', 0)
        ps_d = ho.get('pre_skip', 0) - lo.get('pre_skip', 0)
        br_d = rh.get('actual_kbps', 0) - rl.get('actual_kbps', 0)
        pkt_d = rh.get('audio_packets', 0) - rl.get('audio_packets', 0)
        
        print(f"  {s:<16} SR={sr_d:+5d}Hz  CH={ch_d:+3d}  PreSkip={ps_d:+4d}  BR={br_d:+6.1f}kbps  pkts={pkt_d:+4d}")

asyncio.run(main())
