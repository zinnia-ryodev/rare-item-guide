# レアアイテム検索 (rare-item-guide)

ギルドモノ2 系のレアアイテム／モンスターを検索できる単一ファイルの静的Webアプリ。

## 構成
- `index.html` … 本体（データ埋め込み済みの自己完結型。iOSのホーム画面追加を想定したレイアウト）
- `rare-item-guide-ios.html` … `index.html` と同一（元パッケージのファイル名を保持）
- `guildmono2_rare_items.sqlite3` / `guildmono2_monsters.sqlite3` … 元データ（参照用）

## 公開
GitHub Pages で `index.html` をそのまま配信。
