#!/usr/bin/env python3
"""
FM Radio Recorder for JCBA Internet Simul Radio
WebSocket→ffmpegパイプでogg録音
"""

import sys
import time
import argparse
import requests
import websocket


class JCBARecorder:
    def __init__(self, station_id: str, duration: int = 0):
        self.station_id = station_id
        self.duration = duration
        self.start_time = time.time()
        self.total_bytes = 0
        self.page_count = 0
        self.connected = False
        self.token = ""
        self.location = ""  # type: str
        self._ws = None  # type: websocket.WebSocketApp | None

    def get_stream_token(self, burst: int = 5) -> tuple[str, str]:
        """ストリーミングのJWTトークンとWSS URLを取得"""
        headers = {
            "Origin": "https://www.jcbasimul.com",
            "Content-Type": "application/json",
        }
        url = (
            f"https://api.radimo.smen.biz/api/v1/select_stream"
            f"?station={self.station_id}"
            f"&channel=0"
            f"&quality=high"
            f"&burst={burst}"
    url = (
        f"https://api.radimo.smen.biz/api/v1/select_stream"
        f"?station={self.station_id}"
        f"&channel=0"
        f"&quality=high"
        f"&burst={burst}"
    )
    print(f"[INFO] Getting stream token...", file=sys.stderr)
    res = requests.post(url, headers=headers, json={"station": self.station_id}, timeout=10)
        res.raise_for_status()
        data = res.json()
        self.token = data["token"]
        self.location = data["location"]
        print(f"[INFO] Token obtained (expires ~15s)", file=sys.stderr)
        return self.token, self.location

    def on_open(self, ws):
        self.connected = True
        print(f"[INFO] WSS connected, sending JWT...", file=sys.stderr)
        ws.send(self.token)
        print(f"[INFO] JWT sent, waiting for audio...", file=sys.stderr)

    def on_message(self, ws, message):
        self.page_count += 1
        self.total_bytes += len(message)
        elapsed = time.time() - self.start_time

        # Ogg出力
        sys.stdout.buffer.write(message)
        sys.stdout.buffer.flush()

        if self.page_count % 30 == 0:
            print(
                f"[INFO] Pages: {self.page_count}, Bytes: {self.total_bytes}, "
                f"Elapsed: {elapsed:.1f}s",
                file=sys.stderr,
            )

        if self.duration > 0 and elapsed >= self.duration:
            print(f"\n[INFO] Duration limit ({self.duration}s) reached. Stopping.", file=sys.stderr)
            ws.close()
            raise KeyboardInterrupt(f"Stop after {elapsed:.1f}s")

    def on_error(self, ws, error):
        print(f"[ERROR] WS error: {error}", file=sys.stderr)

    def on_close(self, ws, close_status_code, close_msg):
        elapsed = time.time() - self.start_time
        print(
            f"\n[INFO] Connection closed. {self.page_count} pages, "
            f"{self.total_bytes:,} bytes, {elapsed:.1f}s",
            file=sys.stderr,
        )

    def record(self, output_ogg: str | None = None):
        self.get_stream_token(burst=5)

        self._ws = websocket.WebSocketApp(
            self.location,
            subprotocols=["listener.fmplapla.com"],
            on_open=lambda w: self.on_open(w),
            on_message=lambda w, m: self.on_message(w, m),
            on_error=self.on_error,
            on_close=lambda w, s, c: self.on_close(w, s, c),
        )

        print(f"[INFO] Station: {self.station_id}, Recording to stdout (Ogg)...\n", file=sys.stderr)

        try:
            self._ws.run_forever()
        except KeyboardInterrupt:
            if self._ws:
                self._ws.close()

        if self.page_count == 0:
            print("[ERROR] No audio data received!", file=sys.stderr)
            return False

        # Oggヘッダー確認
        if output_ogg and self.total_bytes > 100:
            print(f"[INFO] Saving raw Ogg to {output_ogg}...", file=sys.stderr)
            self._save_raw_ogg(output_ogg)
        
        return True

    def _save_raw_ogg(self, path: str):
        """再録音せずにstdoutバッファを保存する方法がないので、ffmpegパイプ前提"""
        pass


def main():
    parser = argparse.ArgumentParser(description="JCBA Internet Simul Radio Recorder")
    parser.add_argument("-s", "--station", required=True, help="Station ID (e.g. fmnanami)")
    parser.add_argument("-t", "--time", type=int, default=0, help="Duration in seconds (0=forever)")
    parser.add_argument("-o", "--output", default=None, help=".ogg output file path")
    args = parser.parse_args()

    rec = JCBARecorder(args.station, args.time)
    success = rec.record(args.output)
    
    if success and rec.page_count > 0:
        print(f"\n[INFO] ✅ Recorded {rec.page_count} pages, {rec.total_bytes:,} bytes in {time.time() - rec.start_time:.1f}s", file=sys.stderr)
    else:
        print("\n[ERROR] Failed to record.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
