#!/usr/bin/env python3
"""JCBA全放送局の受信テストを並列実行"""

import asyncio
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent
OUTPUT_DIR = REPO_DIR / "output"
DATA_DIR = REPO_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)


async def test_single_station(station: dict) -> dict:
    """単一局の受信テスト（10秒）"""
    sid = station["station_id"]
    name = station["station_name"]
    region = station["region"]
    
    ogg_file = OUTPUT_DIR / f"{sid}.ogg"
    
    # test_record.py で10秒録音
    try:
        result = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                sys.executable, str(REPO_DIR / "src/test_record.py"),
                "-s", sid,
                "-t", "10",
                "-o", str(ogg_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(REPO_DIR),
            ),
            timeout=90
        )
    except asyncio.TimeoutError:
        return {
            "station_id": sid,
            "station_name": name,
            "region": region,
            "status": "TIMEOUT",
            "size": 0,
            "valid": False,
        }
    
    stdout, stderr = await result.communicate()
    stdout_str = stdout.decode("utf-8", errors="replace")
    stderr_str = stderr.decode("utf-8", errors="replace")
    
    # サイズチェック
    size = ogg_file.stat().st_size if ogg_file.exists() else 0
    
    # Oggヘッダーチェック
    valid = False
    if ogg_file.exists() and size > 0:
        with open(ogg_file, "rb") as f:
            header = f.read(4)
            valid = header[:4] == b'OggS' or header[:3] == b'Ogg'
    
    return {
        "station_id": sid,
        "station_name": name,
        "region": region,
        "status": "OK" if valid and size > 0 else ("EMPTY" if size == 0 else "ERROR"),
        "size": size,
        "valid": valid,
        "stdout": stdout_str[:200],
    }


async def test_all_stations(stations: list[dict]) -> list[dict]:
    """全駅を並列でテスト（バッチ分割）"""
    # 一度に10局ずつ並列実行
    batch_size = 10
    results = []
    
    for i in range(0, len(stations), batch_size):
        batch = stations[i:i+batch_size]
        tasks = [test_single_station(s) for s in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in batch_results:
            if isinstance(res, Exception):
                results.append({
                    "station_id": res.args[0] if res.args else "UNKNOWN",
                    "status": "ERROR",
                    "size": 0,
                    "valid": False,
                })
            else:
                results.append(res)
        print(f"Progress: done {len(results)}/{len(stations)}")
    
    return results


def save_results(results: list[dict]):
    """結果をCSV/JSONに保存"""
    # CSV結果保存
    csv_path = DATA_DIR / "stations_test_result.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["station_id", "station_name", "region", "prefecture", "test_status", "size_bytes", "valid"])
        for r in results:
            sid = r.get("station_id", "")
            # 元のstations.csvから情報を取得
            with open(DATA_DIR / "stations.csv", "r", encoding="utf-8") as sf:
                reader = csv.DictReader(sf)
                for row in reader:
                    if row["station_id"] == sid:
                        writer.writerow([
                            row["station_id"],
                            row["station_name"],
                            row["region"],
                            row["prefecture"],
                            r.get("status", "UNKNOWN"),
                            r.get("size", 0),
                            r.get("valid", False),
                        ])
                        break
    
    # JSON保存
    json_path = DATA_DIR / "stations_test_result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to {csv_path} and {json_path}")


def print_summary(results: list[dict]):
    """サマリー表示"""
    ok_count = sum(1 for r in results if r.get("status") == "OK")
    empty_count = sum(1 for r in results if r.get("status") == "EMPTY")
    error_count = sum(1 for r in results if r.get("status") == "ERROR" or r.get("status") == "TIMEOUT")
    
    print(f"\n{'='*60}")
    print(f"受信テスト結果サマリー（{len(results)}局）")
    print(f"  ✅ OK: {ok_count} 局（受信成功）")
    print(f"  ⬜ EMPTY: {empty_count} 局（ストリームなし・音源なし）")
    print(f"  ❌ ERROR/TIMEOUT: {error_count} 局")
    print(f"{'='*60}")
    
    # 成功した局のリスト
    ok_stations = [r for r in results if r.get("status") == "OK"]
    print(f"\n✅受信成功局（{len(ok_stations)}局）:")
    for r in ok_stations:
        print(f"  {r['station_id']:<25s} {r['station_name']:<30s} [{r['region']}地区] ({r['size']}B)")
    
    # 失敗した局のリスト
    fail_stations = [r for r in results if r.get("status") != "OK"]
    if fail_stations:
        print(f"\n❌受信失敗局（{len(fail_stations)}局）:")
        for r in fail_stations:
            print(f"  {r['station_id']:<25s} {r['station_name']:<30s} [{r['region']}地区] ({r['status']})")


async def main():
    print(f"JCBA全{142}局受信テスト開始！( ^▽)")
    
    # 局一覧を読み込み
    stations = []
    with open(DATA_DIR / "stations.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stations.append(row)
    
    print(f"対象局: {len(stations)}局\n")
    
    # 並列受信テスト
    results = await test_all_stations(stations)
    
    # 結果保存・表示
    save_results(results)
    print_summary(results)
    
    # 失敗局の詳細表示
    fail_stations = [r for r in results if r.get("status") != "OK"]
    if fail_stations:
        print(f"\n詳細（失敗局のstdout）:")
        for r in fail_stations[:20]:
            print(f"\n--- {r['station_id']} {r['station_name']} ({r['status']}, {r['size']}B) ---")
            if "stdout" in r and r.get("stdout"):
                print(r["stdout"])


if __name__ == "__main__":
    asyncio.run(main())
