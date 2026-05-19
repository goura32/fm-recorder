#!/usr/bin/env python3
"""
FM Radio Recorder for JCBA Internet Simul Radio
テスト用 — Oggデータをファイルに保存
"""

import sys
import time
import argparse
import requests
import websocket


def main():
    parser = argparse.ArgumentParser(description="JCBA Internet Simul Radio Recorder Test")
    parser.add_argument("-s", "--station", required=True, default="fmnanami")
    parser.add_argument("-t", "--time", type=int, default=0)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    print(f"[INFO] Station: {args.station}", file=sys.stderr)
    print(f"[INFO] Duration: {args.time if args.time > 0 else 'forever'}s", file=sys.stderr)
    print(f"[INFO] Output: {args.output}", file=sys.stderr)

    # トークン取得
    headers = {
        "Origin": "https://www.jcbasimul.com",
        "Content-Type": "application/json",
    }
    url = (
        f"https://api.radimo.smen.biz/api/v1/select_stream"
        f"?station={args.station}"
        f"&channel=0"
        f"&quality=high"
        f"&burst=5"
    )
    res = requests.post(url, headers=headers, json={"station": args.station}, timeout=10)
    res.raise_for_status()
    data = res.json()
    token = data["token"]
    location = data["location"]
    print(f"[INFO] Token obtained, location: {location}", file=sys.stderr)

    start_time = time.time()
    total_bytes = 0
    page_count = 0
    stop_flag = False
    out_file = open(args.output, "wb")

    def on_open(ws):
        nonlocal stop_flag
        print("[INFO] WSS connected, sending JWT...", file=sys.stderr)
        ws.send(token)

    def on_message(ws, message):
        nonlocal total_bytes, page_count, stop_flag
        page_count += 1
        total_bytes += len(message)
        out_file.write(message)
        elapsed = time.time() - start_time
        if page_count % 20 == 0:
            print(f"[INFO] Pages: {page_count}, Bytes: {total_bytes}, {elapsed:.1f}s", file=sys.stderr)
        if args.time > 0 and elapsed >= args.time:
            print(f"\n[INFO] Duration limit reached ({args.time}s). Stopping...", file=sys.stderr)
            stop_flag = True
            ws.close()

    def on_error(ws, error):
        print(f"[ERROR] {error}", file=sys.stderr)

    def on_close(ws, status, msg):
        print(f"[INFO] WSS closed. {page_count} pages, {total_bytes:,} bytes", file=sys.stderr)

    ws = websocket.WebSocketApp(
        location,
        subprotocols=["listener.fmplapla.com"],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    ws.run_forever()
    out_file.close()

    if page_count == 0:
        print("[ERROR] No data received!", file=sys.stderr)
        sys.exit(1)

    print(f"\n[INFO] ✅ Recorded {page_count} pages, {total_bytes:,} bytes", file=sys.stderr)

    # Oggヘッダー確認
    with open(args.output, "rb") as f:
        header = f.read(20)
    if header[:4] == b"OggS":
        print("[INFO] ✅ Valid Ogg header!", file=sys.stderr)
        serial = int.from_bytes(header[8:12], "little")
        print(f"[INFO] Ogg serial: {serial}", file=sys.stderr)
    else:
        print(f"[WARN] Header hex: {header[:10].hex()}", file=sys.stderr)

    # フレーム数概算
    duration_estimate = page_count * 0.029
    print(f"[INFO] Est. duration: {duration_estimate:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
