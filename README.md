# レアアイテム検索 (rare-item-guide)

冒険者ギルド物語2 のレアアイテム／モンスター／おすすめパーティを検索できる、
単一ファイルの静的Webアプリ。GitHub Pages で `index.html` をそのまま配信。

タブ: ダンジョン一覧 / パーティ推奨 / 編成集 / 仕組み / トレハン確認

## リポジトリ構成

```
index.html            生成物（コミット対象。Pagesが配信）
src/
  template.html       ページの外枠＋アプリJS。データは /*@DATA:NAME@*/ マーカー
  content/
    treh_check.json    「トレハン確認」の手入れ済みデータ（wiki由来・要約整形あり）
data/
  guildmono2_rare_items.sqlite3   正本（アイテム/モンスター/loot/推奨パーティ）
  guildmono2_monsters.sqlite3
  wiki/                            スクレイプ原本（追従の証跡）
    party-formations.html
    treasure-hunt.html
    drop-item.html
    FETCHED_AT.txt                 取得日時(UTC)
build/
  build.py           これ1本で index.html を再生成
  extract_items.py   sqlite      -> RARE_ITEMS / RARE_MONSTERS / PARTY_RECS
  extract_party.py   wiki(html)  -> PARTY_BUILDS / PARTY_RECS_PROSE
  extract_treh.py    treh_check.json のドリフト検査（wiki変更の検知）
build.sh
```

## 更新のしかた

1. データを差し替える
   - アイテム/モンスター: `data/guildmono2_rare_items.sqlite3` を新しいものに置換
   - wiki由来（編成集・4章以降の推奨・トレハン確認・仕組み）:
     ```
     ./build.sh --refresh-wiki      # wiki 3ページを data/wiki/ に取り直す
     ```
2. 再生成
   ```
   ./build.sh
   ```
   `index.html` が作り直される。`build/build.py` の `GAME_VER` は wiki のゲームバージョンに合わせて更新。
3. `TREH_CHECK DRIFT` と出たら、wikiの◆効果表が変わっている。
   `src/content/treh_check.json` を見直してから再ビルド。
4. `git add -A && git commit && git push`

依存: Python3 + `beautifulsoup4` / `lxml`（extract 用）。ランタイム依存ライブラリは無し。
