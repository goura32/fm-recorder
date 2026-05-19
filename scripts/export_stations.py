#!/usr/bin/env python3
"""JCBA放送局一覧のCSVを各種フォーマットにエクスポート"""

import csv
import sys
from collections import defaultdict


def load_stations(csv_path: str) -> list[dict]:
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def to_csv_format(stations: list[dict]) -> str:
    lines = ["JCBAインターネットサイマルラジオ 放送局一覧"]
    for s in stations:
        lines.append(f'{s["station_id"]},{s["station_name"]}')
    return "\n".join(lines)


def to_region_list(stations: list[dict]) -> str:
    regions = defaultdict(list)
    for s in stations:
        regions[s["region"]].append(s)
    
    lines = ["JCBAインターネットサイマルラジオ 放送局一覧"]
    lines.append("")
    for region in ["北海道", "東北", "関東", "信越", "北陸", "東海", "近畿", "中国", "四国", "九州", "沖縄"]:
        if region not in regions:
            continue
        s_list = regions[region]
        lines.append(f"【{region}地区】（{len(s_list)}局）")
        for s in s_list:
            lines.append(f'  {s["station_id"]:<25s} {s["station_name"]:<30s} ({s["prefecture"]})')
        lines.append("")
    return "\n".join(lines)


def to_json_format(stations: list[dict]) -> dict:
    result = {}
    for s in stations:
        region = s["region"]
        if region not in result:
            result[region] = []
        result[region].append({
            "station_id": s["station_id"],
            "station_name": s["station_name"],
            "prefecture": s["prefecture"],
        })
    return result


def main():
    stations = load_stations("data/stations.csv")
    print(f"=== 総計 {len(stations)} 局 ===")
    
    # CSV出力
    csv_out = to_csv_format(stations)
    with open("data/stations_raw.csv", "w", encoding="utf-8") as f:
        f.write(csv_out)
    print("\n[OK] data/stations_raw.csv written")
    
    # 地域別リスト出力
    region_out = to_region_list(stations)
    with open("data/stations_by_region.md", "w", encoding="utf-8") as f:
        f.write(region_out)
    print("[OK] data/stations_by_region.md written")
    
    # JSON出力
    json_data = to_json_format(stations)
    import json
    with open("data/stations.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print("[OK] data/stations.json written")
    
    # 地域ブロック表示（一覧として表示）
    print("\n========== 放送局一覧（地域ブロック順）==========")
    print(region_out)


if __name__ == "__main__":
    main()
