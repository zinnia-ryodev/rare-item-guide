# レアアイテム検索 (rare-item-guide)

冒険者ギルド物語2 のレアアイテム／モンスター／おすすめパーティを検索できる、
単一ファイルの静的Webアプリ。GitHub Pages が `index.html` をそのまま配信。

タブ: ダンジョン一覧 / パーティ推奨 / 編成集 / 仕組み / トレハン確認 / モンスター

## 構成

```
index.html            生成物（コミット対象。Pagesが配信。決定的：同じ入力なら同じ出力）
src/
  template.html       ページ外枠＋アプリJS。データは /*@DATA:NAME@*/ マーカー
  content/
    treh_check.json   「トレハン確認」データ … 手管理（wiki由来・要約整形あり）
    guide.json        「仕組み」タブ本文 … 手管理（wikiの平易な書き直し）
data/
  guildmono2_rare_items.sqlite3   正本（アイテム/モンスター/loot/推奨パーティ）
  guildmono2_monsters.sqlite3
  wiki/                            スクレイプ原本（追従の証跡）
    party-formations.html / treasure-hunt.html / drop-item.html
    FETCHED_AT.txt                 取得日時(UTC)
build/
  build.py            index.html を再生成（マーカーを埋める）
  extract_items.py    [生成] sqlite      -> RARE_ITEMS / RARE_MONSTERS / PARTY_RECS
  extract_party.py    [生成] wiki(html)  -> PARTY_BUILDS / PARTY_RECS_PROSE
  check_treh.py       [検査] treh_check.json と treasure-hunt.html の乖離を検知
  check_guide.py      [検査] guide.json と drop-item.html の見出し構造の乖離を検知
  verify.py           [回帰] 生成データの sha256 を build/data.lock と突合
  data.lock           生成データの既知ハッシュ（回帰ガード）
  requirements.txt    beautifulsoup4 / lxml（extract/check 用。ランタイム依存は無し）
build.sh
```

「生成」＝ソースから機械的に再現（バイト一致を保証）。
「検査」＝手管理データ。wiki が変わったら CI で気づけるようアラームだけ出す。

## 更新のしかた

1. データ差し替え
   - アイテム/モンスター: `data/guildmono2_rare_items.sqlite3` を置換
   - wiki由来: `./build.sh --refresh-wiki`（3ページ取り直し＋取得日更新）
2. 再生成＋回帰チェック
   ```
   pip install -r build/requirements.txt      # 初回のみ
   ./build.sh --verify
   ```
   - `DATA REGRESSION` … 生成データがロックとズレた。差分が意図的なら
     `python build/verify.py --update` でロック更新
   - `TREH_CHECK DRIFT` / `GUIDE DRIFT` … wiki側の表・見出しが変わった。
     `src/content/*.json` を見直してから再ビルド
   - `gameVer` は wiki本文の「現在のverX.YZ」を自動検出
3. `git add -A && git commit && git push`
