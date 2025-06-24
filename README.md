# Web Discord Server

## 概要
Discord ボットと aiohttp 製 Web サーバーを組み合わせたファイル共有システムです。ボットが起動すると内部で Web サーバーも自動的に立ち上がり、アップロードされたファイルをブラウザから閲覧・ダウンロードできます。

## 必要な環境
- Python 3.9 以上
- `pip` で以下の主要ライブラリをインストールしてください（例: `pip install discord.py aiohttp aiohttp-session aiolimiter python-dotenv pyotp qrcode pillow`）

## 環境変数
`.env` ファイルに下記の変数を設定するか、実行環境で指定します。

| 変数名 | 説明 |
|-------|------|
| `DISCORD_TOKEN` | ボットの Discord トークン (**必須**) |
| `DB_PATH` | SQLite データベースのパス。既定値 `data/web_discord_server.db` |
| `PUBLIC_DOMAIN` | 外部公開ドメイン。ダウンロードリンクや QR コード生成に使用。既定値 `localhost:9040` |
| `PORT` | Web サーバーが待ち受けるポート番号。既定値 `9040` |
| `BOT_OWNER_ID` | ボット製作者の Discord ユーザー ID。登録通知 DM の送信先になります |
| `BOT_GUILD_ID` | コマンド同期を行うギルド ID。開発サーバーを指定する際に使用します |
| `FILE_HMAC_SECRET` | 署名付きリンク生成に用いる Base64 文字列。未指定の場合ランダム値 |
| `UPLOAD_EXPIRES_SEC` | ダウンロード URL の有効期限 (秒)。既定値 `86400` (1 日) |
| `DATA_DIR` | アップロードファイルを保存するディレクトリ。既定値 `./data` |
| `STATIC_DIR` | 静的ファイルの格納場所。既定値 `./static` |
| `TEMPLATE_DIR` | HTML テンプレートの場所。既定値 `./templates` |
| `COOKIE_SECRET` | 44 文字の URL-safe Base64。セッション暗号化に使用 (**必須**) |

## 起動方法
1. 必要な環境変数を設定後、以下のコマンドでボットを起動します。
   ```bash
   python bot/bot.py
   ```
   ボット起動時に Web サーバーも同じプロセス内で開始されます。
2. Web サーバー単体で動作確認したい場合は次のコマンドを実行します。
   ```bash
   python web/app.py
   ```
   `PORT` で指定したポートでリッスンします。

## データベース初期化
初回起動時に自動的に SQLite のスキーマが作成されます。既にデータベースが存在する場合はそのまま使用されます。

## ライセンス
このプロジェクトは MIT ライセンスです。
