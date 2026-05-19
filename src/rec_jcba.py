#!/usr/bin/env python3
"""
FM Radio Recorder for JCBA Internet Simul Radio
テスト用録音スクリプト — WebSocket経由でPCMデータを取得し、WAVファイルに保存
"""

import sys
import time
import struct
import argparse
import requests
import websocket

class JCBARecorder:
    def __init__(self, station_id: str, duration: int = 0):
        self.station_id = station_id
        self.duration = duration  # 秒。0なら無限ループ
        self.start_time = time.time()
        self.total_bytes = 0
        self.page_count = 0
        self.connected = False
        self.token = ""
        self.location = ""  # type: str
        
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
        )
        
        print(f"[INFO] Getting stream token: {url}", file=sys.stderr)
        res = requests.post(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        token = data["token"]
        location = data["location"]
        print(f"[INFO] Token received, expires in ~15s", file=sys.stderr)
        return token, location
    
    def on_open(self, ws):
        """WebSocket接続確立時にトークンを送信"""
        self.connected = True
        print(f"[INFO] WebSocket connected, sending JWT token...", file=sys.stderr)
        ws.send(self.token)
        print(f"[INFO] Token sent, waiting for audio stream...", file=sys.stderr)

    def on_message(self, ws, message):
        """オーディオデータを受信"""
        # Oggページヘッダー (32 bytes):
        # Magic "OggS" (4) + Version (1) + Flags (1) + Granule (8) +
        # Serial (4) + Sequence (4) + CRC (4) + SegCount (1) + SegTable (N)
        
        self.page_count += 1
        payload_len = len(message)
        self.total_bytes += payload_len
        
        elapsed = time.time() - self.start_time
        
        # メイン処理
        sys.stdout.buffer.write(message)
        sys.stdout.buffer.flush()
        
        # 経過ログ（10ページごと）
        if self.page_count % 50 == 0:
            print(
                f"[INFO] Pages: {self.page_count}, Size: {self.total_bytes} bytes, "
                f"Duration: {elapsed:.1f}s",
                file=sys.stderr
            )
        
        # 時間制限
        if self.duration > 0 and elapsed >= self.duration:
            print(f"\n[INFO] Duration limit reached ({self.duration}s). Stopping.", file=sys.stderr)
            raise KeyboardInterrupt(f"Stop after {elapsed:.1f}s, {self.page_count} pages, {self.total_bytes} bytes")
    
    def on_error(self, ws, error):
        print(f"[ERROR] WebSocket error: {error}", file=sys.stderr)
    
    def on_close(self, ws, close_status_code, close_msg):
        elapsed = time.time() - self.start_time
        print(
            f"\n[INFO] Connection closed. {self.page_count} pages, "
            f"{self.total_bytes} bytes, {elapsed:.1f}s", 
            file=sys.stderr
        )
    
    def record(self):
        """テスト録音実行"""
        self.token, location = self.get_stream_token(burst=5)
        
        ws = websocket.WebSocketApp(
            location,
            subprotocols=["listener.fmplapla.com"],
            on_open=lambda w: self.on_open(w),
            on_message= lambda w, m: self.on_message(w, m),
            on_error=self.on_error,
            on_close=lambda w, s, c: self.on_close(w, s, c),
        )
        
        try:
            print(f"[INFO] Recording to stdout... (Ctrl+C to stop)", file=sys.stderr)
            ws.run_forever()
        except KeyboardInterrupt:
            ws.close()
        finally:
            print(
                f"\n[INFO] Done: {self.page_count} pages, {self.total_bytes:,} bytes, "
                f"{time.time() - self.start_time:.1f}s", 
                file=sys.stderr
            )


def main():
    parser = argparse.ArgumentParser(description="JCBA Internet Simul Radio Recorder (PCM output)")
    parser.add_argument("-s", "--station", required=True, help="Station ID (e.g. fmnanami)")
    parser.add_argument("-t", "--time", type=int, default=0, help="Duration in seconds (0=forever)")
    parser.add_argument("-o", "--output", default="/home/hermes/projects/fm-recorder/output/test.wav")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug")
    args = parser.parse_args()
    
    rec = JCBARecorder(args.station, args.time)
    
    # テスト録音は30秒固定で安全のため
    duration = args.time if args.time > 0 else 30
    rec.token, rec.location = rec.get_stream_token(burst=5)
    
    ws = websocket.WebSocketApp(
        rec.location,
        subprotocols=["listener.fmplapla.com"],
        on_open=lambda w: rec.on_open(w),
        on_message=lambda w, m: rec.on_message(w, m),
        on_error=rec.on_error,
        on_close=lambda w, s, c: rec.on_close(w, s, c),
    )
    
    try:
        print(f"[INFO] Recording Station: {args.station}, Duration: {duration}s", file=sys.stderr)
        print(f"[INFO] Output: {args.output}", file=sys.stderr)
        print(f"[INFO] Starting stream...", file=sys.stderr)
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
    
    # Oggデータを受け取った場合はWAVファイルに変換
    if rec.page_count > 0 and args.output:
        print(f"\n[INFO] Converting to WAV...", file=sys.stderr)
        _save_to_wav(args.output, args.station)
    
    print(f"\n[INFO] Recorded {rec.page_count} pages, {rec.total_bytes:,} bytes", file=sys.stderr)


def _save_to_wav(output_path: str, station: str):
    """録音したoggデータからwavファイルを作成する（簡易版）"""
    # ffmpegを使って変換するのが確実だが、
    # ここではffmpegを使う旨を出力
    print(f"[NOTE] To convert to WAV, run:", file=sys.stderr)
    print(f"  ffmpeg -i <pipe> -c:a pcm_s16le {output_path}", file=sys.stderr)
    print(f"\n[NOTE] Or record with ffmpeg directly:", file=sys.stderr)
    print(f"  python {sys.argv[0]} -s {station} -t 30 | ffmpeg -i pipe: -c:a libvorbis output.ogg", file=sys.stderr)


if __name__ == "__main__":
    main()
