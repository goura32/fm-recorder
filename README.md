# FM Radio Recorder — JCBAインターネットサイマルラジオ録音ツール

## 概要

JCBA（日本コミュニティ放送協会）のインターネットサイマルラジオのコミュニティFM放送を録音するためのツールキット。

## 技術調査結果

### ストリーミング方式

- **プロトコル**: WebSocket（Ogg/Opus形式）
- **APIエンドポイント**:
  ```
  POST https://api.radimo.smen.biz/api/v1/select_stream?station={station_id}&channel=0&quality=high&burst={burst}
  Body: {"station": "{station_id}"}
  ```
- **レスポンス**: `{ "code": 200, "token": "JWT", "location": "wss://..." }`
- **WebSocket手順**:
  1. `subprotocols=["listener.fmplapla.com"]` で接続
  2. 最初のメッセージとしてJWTトークン送信
  3. Ogg/Opusバイナリデータを受信（標準出力へパイプ可能）

### 既存リポジトリ

| リポジトリ | 言語 | 特徴 |
|--|--|--|
| [je3kmz/jcba](https://github.com/je3kmz/jcba) | Python | 最も完成度高い。OGG stitching対応 |
| [mikuta0407/jcba-streamer](https://github.com/mikuta0407/jcba-streamer) | Go | 軽量。stdoutストリーミング |
| [NAKADANobuhiro/FMSimulRec](https://github.com/NAKADANobuhiro/FMSimulRec) | Python | 自動録音管理 |

### 依存要件

- `python >= 3.8`
- `pip install requests websocket-client`
- `ffmpeg`（ Ogg→MP3/FLAC変換用）

## 録音の方法

### Pythonスクリプトを使用

```bash
# テスト録音（10秒）
python src/test_record.py -s fmnanami -t 10 -o output/test.ogg

# 録音 → Ogg→MP3変換
ffmpeg -i output/test.ogg -codec:a libmp3lame -q:a 4 output/test.mp3
```

### Goストリーマを使用

```bash
go install github.com/mikuta0407/jcba-streamer@latest
jcba-streamer -s fmnanami -d 3600 | ffmpeg -i pipe: -c:a libvorbis -q:a 4 output.opus
```

## 放送局一覧（全142局）

全142局の一括受信テスト実施。 **135局が正常受信成功**、7局でエンティティなし（配信なし／編成分離）。

### 北海道地区（8局）

| station_id | 局名 | 受信 |
|--|--|--|
| fmhana | ＦＭはな | ✅ |
| moeru | エフエムもえる | ✅ |
| airtesshi | Ａｉｒてっし | ✅ |
| radioniseko | ラジオニセコ | ✅ |
| iruka | FMいるか | ✅ |
| muroran | FMびゅー | ✅ |
| fmtomakomai | FMとまこまい | ✅ |
| fmkuriyama | FMくりやま | ✅ |

### 東北地区（14局）

| station_id | 局名 | 受信 |
|-------|--|--|
| fmazur | FM AZUR | ✅ |
| applewave | アップルウェーブ | ✅ |
| fmgoshogawara | FMごしょがわら | ✅ |
| fmone | FMONE | ✅ |
| fmiwanuma | エフエムいわぬま | ✅ |
| hatfm | Ｈ＠！ＦＭ | ✅ |
| radiomonster | ラジオ モンスター | ✅ |
| yonezawancvfm | エフエムNCV | ✅ |
| orandaradio | えふえむい～じゃん | ✅ |
| harborradio | ハーバーラジオ | ✅ |
| ultrafm | ウルトラＦＭ | ✅ |
| fmpoco | ＦＭポコ | ✅ |
| fmkitakata | エフエムきたかた | ✅ |
| fmaizu | FM愛'S | ✅ |

### 関東地区（34局）

| station_id | 局名 | 受信 |
|-------|--|--|
| fmdaigo | ＦＭだいご | ✅ |
| fmkashima | FMかしま | ✅ |
| radiotakasaki | ラジオ高崎 | ✅ |
| fmtaro | エフエム太郎 | ✅ |
| fmoze | ＦＭ ＯＺＥ | ✅ |
| radionanami | ラヂオななみ | ✅ |
| fmchappy | ＦＭチャッピー | ✅ |
| miyoshifm | 発するFM | ✅ |
| radiokawagoe | ラジオ川越 | ✅ |
| ulalafm | 市川うららFM(I&U-LaLaFM) | ✅ |
| kazusafm | かずさFM | ✅ |
| radionarita | ラジオ成田 | ✅ |
| fmfukuro | ふくろうFM | ✅ |
| skywavefm | SKYWAVE FM | ✅ |
| fmedogawa | ＦＭえどがわ | ✅ |
| musashinofm | むさしのＦＭ | ✅ |
| fmshinagawa | FMしながわ | ✅ |
| fmkatsushika | かつしかFM | ✅ |
| shibuyanoradio | 渋谷のラジオ | ✅ |
| radiocity | 中央エフエム・RADIO CITY | ✅ |
| komaraji | コマラジ | ✅ |
| fmblesohonan | ＦＭブルー湘南 | ⬜ |
| kamakurafm | 鎌倉FM | ✅ |
| fmshonan | FM湘南ナパサ | ✅ |
| fmodawara | FMおだわら | ✅ |
| magicwave | FM湘南マジックウェイブ | ✅ |
| fmyamato | FMやまと | ✅ |
| radioshonan | レディオ湘南 | ✅ |
| fmsalus | FMサルース | ✅ |
| marinefm | マリンFM | ✅ |
| fmtotsuka | エフエム戸塚 | ✅ |
| chigasakifm | エボラジ | ✅ |

### 信越地区（19局）

| station_id | 局名 | 受信 |
|-------|--|--|
| fmkofu | エフエム甲府 | ✅ |
| fmfujiyama | FMふじやま | ✅ |
| fmfujigoko | エフエム ふじごこ | ✅ |
| fmyatsugatake | FM八ヶ岳 | ✅ |
| radiochat | ラジオチャット・FMにいつ | ✅ |
| fmuonuma | FMうおぬま | ✅ |
| fmnagaoka | エフエムながおか | ✅ |
| fmshibata | エフエムしばた | ✅ |
| fmkento | FM KENTO | ✅ |
| fmyukiguni | ＦＭゆきぐに | ✅ |
| fmjyoetsu | FMじょうえつ | ✅ |
| fmpikkara | FMピッカラ | ✅ |
| lovefm | ＬＣＶ ＦＭ | ✅ |
| fmkaruizawa | FM軽井沢 | ✅ |
| azuminofm | エフエムあづみの | ⬜ |
| shiojirifm | 高ボッチ高原FM | ✅ |
| inadanifm | 伊那谷FM | ✅ |
| fmpipi | ＦＭＰｉＰｉ | ✅ |
| fmwatch | ＦＭわっち | ✅ |

### 北陸地区（6局）

| station_id | 局名 | 受信 |
|-------|--|--|
| toyamacityfm | 富山シティエフエム | ✅ |
| fmtonami | エフエムとなみ | ✅ |
| radiotakaoka | ラジオたかおか | ✅ |
| radiokomatsu | ラジオこまつ | ✅ |
| radionanao | ラジオななお | ✅ |
| radionazawa | ラジオかなざわ | ⬜ |

### 東海地区（21局）

| station_id | 局名 | 受信 |
|-------|--|--|
| hitsfm | Ｈｉｔｓ ＦＭ | ✅ |
| haro | FM Haro! | ✅ |
| fnis | FM ISみらいずステーション | ⬜ |
| fmshimada | g-sky 76.5 | ✅ |
| fujiyamagogofm | 富士山ＧＯＧＯＦＭ | ✅ |
| voicecue | ボイスキュー | ✅ |
| fmshimizu | マリンパル | ⬜ |
| fmhi | FM-Hi! | ⬜ |
| radiof | Radio-f | ✅ |
| coastfm | COAST-FM 76.7MHz | ✅ |
| nagisastation | エフエムなぎさステーション | ✅ |
| ciao | Ciao! | ✅ |
| fmizunokuni | FMいずのくに | ✅ |
| fmyaizu | RADIO LUSH | ✅ |
| **fmnanami** | **エフエム ななみ** | **✅** |
| unitednorth | United North | ✅ |
| radiosanq | RADIO SANQ | ✅ |
| fmichinomiya | i-wave | ✅ |
| heartfm | HeartFM | ✅ |
| inabefm | いなべエフエム | ✅ |
| suzuka | Suzuka Voice FM 78.3MHz | ✅ |

### 近畿地区（22局）

| station_id | 局名 | 受信 |
|-------|--|--|
| fmkusatsu | えふえむ草津 | ✅ |
| fmikaru | ＦＭいかる | ✅ |
| fmuji | FMうじ | ✅ |
| fmmaizuru | FMまいづる | ✅ |
| kyotoribingufm | FM845 | ✅ |
| fmsenri | FM千里 | ✅ |
| umedafm | ウメダFM | ✅ |
| minofm | タッキー816みのおエフエム | ✅ |
| fmitami | エフエムいたみ | ✅ |
| fmtakarazuka | ハミングFM宝塚 | ✅ |
| sakurafm | さくらFM | ✅ |
| fmmiki | エフエムみっきぃ | ✅ |
| tanba | 805たんば | ✅ |
| fmgenki | FM GENKI | ✅ |
| narafm | なら どっと ＦＭ | ✅ |
| fmnishiyamato | エフエムハイホー | ⬜ |
| fmgojo | ＦＭ五條 | ✅ |
| fmmahoroba | FMまほろば | ✅ |
| bananafm | バナナエフエム | ✅ |
| fmtanabe | FM TANABE | ✅ |
| fmhashimoto | FMはしもと | ✅ |
| beachstation | FMビーチステーション | ✅ |

### 中国地区（12局）

| station_id | 局名 | 受信 |
|-------|--|--|
| radiomomo | レディオ モモ | ✅ |
| fmkurashiki | FMくらしき | ✅ |
| bingo | FMふくやま | ✅ |
| fmonomichi | FMおのみち | ✅ |
| fmchupea | FMちゅーピー | ✅ |
| fmhatsukaichi | FMはつかいち | ✅ |
| fmhigashihiroshima | FM東広島 | ✅ |
| fmmihara | FOR LIFE RADIO | ✅ |
| comeonfm | ＣＯＭＥ ＯＮ ! ＦＭ | ✅ |
| shunanfm | しゅうなんＦＭ | ✅ |
| radiobird | RADIO BIRD | ✅ |
| fmsun | エフエム・サン | ✅ |

### 四国地区（4局）

| station_id | 局名 | 受信 |
|-------|--|--|
| fmradiobaribari | FMラヂオバリバリ | ✅ |
| fmgaiya | FMがいや | ✅ |
| niihamafm | Hello! NEW 新居浜 FM | ✅ |
| dreamsfm | Dreams FM | ✅ |

### 九州地区（6局）

| station_id | 局名 | 受信 |
|-------|--|--|
| fmyame | FM八女 | ✅ |
| fmkaratsu | ＦＭからつ | ✅ |
| fmyatsushiro | Kappa FM | ✅ |
| kumamotocityfm | FM791 | ✅ |
| yufuin | ゆふいんラヂオ局 | ✅ |
| noasfm | NOASFM | ✅ |

### 主な局のstation_id一覧（かんたん）

| 局名 | station_id |
|--|--|
| エフエム ななみ | **fmnanami** |
| ふくろうFM | fmfukuro |
| FM HARO! | haro |
| HeartFM（愛知） | heartfm ✅ |
| リッツFM | hitsfm |
| ラジオたかおか | radiotakaoka |
| FM SALUS | fmsalus |
| 渋谷のラジオ | shibuyanoradio |
| RADIO CITY | radiocity |
| FM湘南ナパサ | fmshonan |
| FMおだわら | fmodawara |
| FM千里 | fmsenri |
| FOR LIFE RADIO | fmmihara |
| FMふくやま | bingo |

### エンティティなし（受信不可）の局（7局）

以下の7局は、受信テストで `EMPTY`（サイズ: 0B）となった。現在の時間帯で **編成分離**（非編成）か、radiko配信から外れている可能性がある。

| station_id | 局名 | 所在地 |
|-------|--|--|--|
| fmblesohonan | ＦＭブルー湘南 | 神奈川県 |
| azuminofm | エフエムあづみの | 長野県 |
| fnis | FM ISみらいずステーション | 静岡県 |
| fmshimizu | マリンパル | 静岡県 |
| fmhi | FM-Hi! | 静岡県 |
| radionazawa | ラジオかなざわ | 石川県 |
| fmnishiyamato | エフエムハイホー | 奈良県 |

> 💡 **注意**: 局名が異なるIDの局がある（例：FM HARO! → `haro`）。一覧は `data/stations.csv` を参照。

## ディレクトリ構成

```
fm-recorder/
├── README.md          # このファイル
├── requirements.txt   # Python依存
├── src/
│   ├── test_record.py  # テスト録音スクリプト（OGG保存）
│   └── record.py       # メイン録音スクリプト（ストリーム出力）
├── scripts/
│   ├── export_stations.py  # 局一覧エクスポート
│   ├── test_all_stations.py  # 全142局受信テスト
├── data/
│   ├── stations.csv    # 全142局CSV
│   ├── stations_by_region.md
│   ├── stations.json
│   └── stations_raw.csv
├── output/            # 録音ファイル出力先
└── logs/
```

## 録音結果

10秒テスト録音成功！ 🎉

| ファイル | サイズ | 内容 |
|--|--|--|
| heartfm.ogg | 126K | Ogg/Opus 53ページ（10秒） |
| heartfm.wav | 2.9M | Ogg→WAV 変換（PCM 16bit）|
| nanami_raw.ogg | 126K | Ogg/Opus 53ページ（10秒） |
| nanami_converted.wav | 2.9M | Ogg→WAV 変換 |

## 受信テスト結果サマリー

| 項目 | 結果 |
|------|------|
| **総局数** | 142局 |
| **✅ 受信成功** | 135局（95.1%） |
| **⬜ 受信不可** | 7局（編成分離／配信なし） |
| **テスト日** | 2026-05-19 |
| **テスト方法** | `test_record.py -s {id} -t 10`（10秒バッチ並列テスト） |

## 注意事項

- JCBAのストリーミングは **WebSocket** ベース。yt-dlpには未対応
- JWTトークンの有効期限は **約15秒**。長時間録音にはリフレッシュ機構が必要
- CDNノード切り替え時にシリアル追跡が必要
- 録音は自身の個人利用に限定し、再配布しないこと
- 海外からのアクセスはブロックされています（2022年6月29日以降）

## アジェンダ（次やること）

- [x] 録音スクリプトの作成、テスト
- [x] 放送局一覧の作成
- [x] 142局の一括受信テスト
- [ ] JWTリフレッシュ機構の実装
- [ ] OGG stitching（再接続音の重複削除）
- [ ] cron自動録音スクリプト
- [ ] メタデータ（局名/日時/曲名）の付与
