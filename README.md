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

## 放送局一覧

JCBAインターネットサイマルラジオ参加局 **142局** を収録。他の局も受信可能です。
`station_id` は下表のIDを `-s` オプションに指定します。

### 地域別一覧

#### 北海道地区（8局）

| station_id | 局名 | 所在地 |
|--|--|--|
| fmhana | ＦＭはな | 北海道 |
| moeru | エフエムもえる | 北海道 |
| airtesshi | Ａｉｒてっし | 北海道 |
| radioniseko | ラジオニセコ | 北海道 |
| iruka | FMいるか | 北海道 |
| muroran | FMびゅー | 北海道 |
| fmtomakomai | FMとまこまい | 北海道 |
| fmkuriyama | FMくりやま | 北海道 |

#### 東北地区（14局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| fmazur | FM AZUR | 青森県 |
| applewave | アップルウェーブ | 岩手県 |
| fmgoshogawara | FMごしょがわら | 青森県 |
| fmone | FMONE | 岩手県 |
| fmiwanuma | エフエムいわぬま | 宮城県 |
| hatfm | Ｈ＠！ＦＭ | 福島県 |
| radiomonster | ラジオ モンスター | 福島県 |
| yonezawancvfm | エフエムNCV | 山形県 |
| orandaradio | えふえむい～じゃん | 福島県 |
| harborradio | ハーバーラジオ | 宮城県 |
| ultrafm | ウルトラＦＭ | 福島県 |
| fmpoco | ＦＭポコ | 宮城県 |
| fmkitakata | エフエムきたかた | 岩手県 |
| fmaizu | FM愛'S | 福島県 |

#### 関東地区（34局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| fmdaigo | ＦＭだいご | 茨城県 |
| fmkashima | FMかしま | 茨城県 |
| radiotakasaki | ラジオ高崎 | 群馬県 |
| fmtaro | エフエム太郎 | 群馬県 |
| fmoze | ＦＭ ＯＺＥ | 栃木県 |
| radionanami | ラヂオななみ | 埼玉県 |
| fmchappy | ＦＭチャッピー | 千葉県 |
| miyoshifm | 発するFM | 千葉県 |
| radiokawagoe | ラジオ川越 | 埼玉県 |
| ulalafm | 市川うららFM(I&U-LaLaFM) | 千葉県 |
| kazusafm | かずさFM | 千葉県 |
| radionarita | ラジオ成田 | 千葉県 |
| fmfukuro | ふくろうFM | 埼玉県 |
| skywavefm | SKYWAVE FM | 茨城県 |
| fmedogawa | ＦＭえどがわ | 東京都 |
| musashinofm | むさしのＦＭ | 東京都 |
| fmshinagawa | FMしながわ | 東京都 |
| fmkatsushika | かつしかFM | 東京都 |
| shibuyanoradio | 渋谷のラジオ | 東京都 |
| radiocity | 中央エフエム・RADIO CITY | 東京都 |
| komaraji | コマラジ | 東京都 |
| fmblesohonan | ＦＭブルー湘南 | 神奈川県 |
| kamakurafm | 鎌倉FM | 神奈川県 |
| fmshonan | FM湘南ナパサ | 神奈川県 |
| fmodawara | FMおだわら | 神奈川県 |
| magicwave | FM湘南マジックウェイブ | 神奈川県 |
| fmyamato | FMやまと | 神奈川県 |
| radioshonan | レディオ湘南 | 神奈川県 |
| fmsalus | FMサルース | 東京都 |
| marinefm | マリンFM | 東京都 |
| fmtotsuka | エフエム戸塚 | 神奈川県 |
| chigasakifm | エボラジ | 神奈川県 |

#### 信越地区（19局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| fmkofu | エフエム甲府 | 山梨県 |
| fmfujiyama | FMふじやま | 山梨県 |
| fmfujigoko | エフエム ふじごこ | 山梨県 |
| fmyatsugatake | FM八ヶ岳 | 長野県 |
| radiochat | ラジオチャット・FMにいつ | 新潟県 |
| fmuonuma | FMうおぬま | 新潟県 |
| fmnagaoka | エフエムながおか | 新潟県 |
| fmshibata | エフエムしばた | 新潟県 |
| fmkento | FM KENTO | 新潟県 |
| fmyukiguni | ＦＭゆきぐに | 新潟県 |
| fmjyoetsu | FMじょうえつ | 新潟県 |
| fmpikkara | FMピッカラ | 新潟県 |
| lovefm | ＬＣＶ ＦＭ | 群馬県 |
| fmkaruizawa | FM軽井沢 | 群馬県 |
| azuminofm | エフエムあづみの | 長野県 |
| shiojirifm | 高ボッチ高原FM | 長野県 |
| inadanifm | 伊那谷FM | 長野県 |
| fmpipi | ＦＭＰｉＰｉ | 長野県 |
| fmwatch | ＦＭわっち | 長野県 |

#### 北陸地区（6局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| toyamacityfm | 富山シティエフエム | 富山県 |
| fmtonami | エフエムとなみ | 富山県 |
| radiotakaoka | ラジオたかおか | 富山県 |
| radiokomatsu | ラジオこまつ | 石川県 |
| radionanao | ラジオななお | 石川県 |
| radionazawa | ラジオかなざわ | 石川県 |

#### 東海地区（21局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| hitsfm | Ｈｉｔｓ ＦＭ | 岐阜県 |
| haro | FM Haro! | 愛知県 |
| fnis | FM ISみらいずステーション | 静岡県 |
| fmshimada | g-sky 76.5 | 静岡県 |
| fujiyamagogofm | 富士山ＧＯＧＯＦＭ | 静岡県 |
| voicecue | ボイスキュー | 静岡県 |
| fmshimizu | マリンパル | 静岡県 |
| fmhi | FM-Hi! | 静岡県 |
| radiof | Radio-f | 静岡県 |
| coastfm | COAST-FM 76.7MHz | 静岡県 |
| nagisastation | エフエムなぎさステーション | 静岡県 |
| ciao | Ciao! | 静岡県 |
| fmizunokuni | FMいずのくに | 静岡県 |
| fmyaizu | RADIO LUSH | 静岡県 |
| **fmnanami** | **エフエム ななみ** | **愛知県（ターゲット）** |
| unitednorth | United North | 愛知県 |
| radiosanq | RADIO SANQ | 愛知県 |
| fmichinomiya | i-wave | 三重県 |
| heartfm | HeartFM | 三重県 |
| inabefm | いなべエフエム | 三重県 |
| suzuka | Suzuka Voice FM 78.3MHz | 三重県 |

#### 近畿地区（22局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| fmkusatsu | えふえむ草津 | 滋賀県 |
| fmikaru | ＦＭいかる | 京都府 |
| fmuji | FMうじ | 京都府 |
| fmmaizuru | FMまいづる | 京都府 |
| kyotoribingufm | FM845 | 京都府 |
| fmsenri | FM千里 | 大阪府 |
| umedafm | ウメダFM | 大阪府 |
| minofm | タッキー816みのおエフエム | 大阪府 |
| fmitami | エフエムいたみ | 兵庫県 |
| fmtakarazuka | ハミングFM宝塚 | 兵庫県 |
| sakurafm | さくらFM | 兵庫県 |
| fmmiki | エフエムみっきぃ | 兵庫県 |
| tanba | 805たんば | 兵庫県 |
| fmgenki | FM GENKI | 兵庫県 |
| narafm | なら どっと ＦＭ | 奈良県 |
| fmnishiyamato | エフエムハイホー | 奈良県 |
| fmgojo | ＦＭ五條 | 奈良県 |
| fmmahoroba | FMまほろば | 奈良県 |
| bananafm | バナナエフエム | 和歌山県 |
| fmtanabe | FM TANABE | 和歌山県 |
| fmhashimoto | FMはしもと | 和歌山県 |
| beachstation | FMビーチステーション | 和歌山県 |

#### 中国地区（12局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| radiomomo | レディオ モモ | 山口県 |
| fmkurashiki | FMくらしき | 岡山県 |
| bingo | FMふくやま | 広島県 |
| fmonomichi | FMおのみち | 広島県 |
| fmchupea | FMちゅーピー | 広島県 |
| fmhatsukaichi | FMはつかいち | 広島県 |
| fmhigashihiroshima | FM東広島 | 広島県 |
| fmmihara | FOR LIFE RADIO | 広島県 |
| comeonfm | ＣＯＭＥ ＯＮ ! ＦＭ | 広島県 |
| shunanfm | しゅうなんＦＭ | 山口県 |
| radiobird | RADIO BIRD | 山口県 |
| fmsun | エフエム・サン | 山口県 |

#### 四国地区（4局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| fmradiobaribari | FMラヂオバリバリ | 山口県 |
| fmgaiya | FMがいや | 愛媛県 |
| niihamafm | Hello! NEW 新居浜 FM | 愛媛県 |
| dreamsfm | Dreams FM | 愛媛県 |

#### 九州地区（6局）

| station_id | 局名 | 所在地 |
|-------|------|---------|
| fmyame | FM八女 | 福岡県 |
| fmkaratsu | ＦＭからつ | 佐賀県 |
| fmyatsushiro | Kappa FM | 熊本県 |
| kumamotocityfm | FM791 | 熊本県 |
| yufuin | ゆふいんラヂオ局 | 熊本県 |
| noasfm | NOASFM | 佐賀県 |

### 主な局のstation_id一覧（かんたん）

| 局名 | station_id |
|------|-------|
| エフエム ななみ | **fmnanami** |
| ふくろうFM | fmfukuro |
| FM HARO! | haro |
| リッツFM | hitsfm |
| HeartFM | heartfm |
| ラジオたかおか | radiotakaoka |
| FM SALUS | fmsalus |
| 渋谷のラジオ | shibuyanoradio |
| RADIO CITY | radiocity |
| FM湘南ナパサ | fmshonan |
| FMおだわら | fmodawara |
| FM千里 | fmsenri |
| FOR LIFE RADIO | fmmihara |
| FMふくやま | bingo |

> 💡 **注意**: `station_id` は `-s` オプションとして指定します。
> 例: `python src/test_record.py -s heartfm -t 60 -o output/heartfm.ogg`

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
│   ├── record.sh       # 録音スクリプト
│   └── record_cron.sh  # cron用
├── data/
│   ├── stations.csv    # 全142局CSV
│   ├── stations_by_region.md  # 地域別マーDOWNリスト
│   ├──stations.json    # JSON形式一覧
│   └── stations_raw.csv  # raw list format
├── output/            # 録音ファイル出力先
└── logs/              # ログ
```

## 録音結果

10秒テスト録音成功！ 🎉

| ファイル | サイズ | 内容 |
|--|--|--|
| nanami_raw.ogg | 123K | Ogg/Opus 53ページ（10秒） |
| nanami_converted.wav | 2.9M | Ogg→WAV 変換（PCM 16bit）|
| nanami_test.mp3 | 302K | Ogg→MP3 変換（libmp3lame q4）|

## 注意事項

- JCBAのストリーミングは **WebSocket** ベース。yt-dlpには未対応
- JWTトークンの有効期限は **約15秒**。長時間録音にはリフレッシュ機構が必要
- CDNノード切り替え時にシリアル追跡が必要
- 録音は自身の個人利用に限定し、再配布しないこと
- 海外からのアクセスはブロックされています（2022年6月29日以降）

## アジェンダ（次やること）

- [x] 録音スクリプトの作成、テスト
- [x] 放送局一覧の作成
- [ ] JWTリフレッシュ機構の実装
- [ ] OGG stitching（再接続音の重複削除）
- [ ] cron自動録音スクリプト
- [ ] メタデータ（局名/日時/曲名）の付与
