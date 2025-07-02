# Web Discord Server

## 概要
Discord ボットと aiohttp 製 Web サーバーを組み合わせたファイル共有システムです。ボットが起動すると内部で Web サーバーも自動的に立ち上がり、アップロードされたファイルをブラウザから閲覧・ダウンロードできます。

### 自動タグ付け
Gemini を利用し、アップロードされたファイルからキーワードを抽出してタグ付けします。
テキストや PDF に加え、Word/Excel/PowerPoint などの Office 文書にも対応します。
Gemini が非対応の形式はテキストへ変換してから解析を行います。
`GEMINI_API_KEY` を設定しない場合は自動タグ付けはスキップされます。


## ディレクトリ構成
- `bot/` ... Discord ボット関連コード
- `web/` ... aiohttp 製 Web アプリ
- `tree_export.py` ... フォルダ構成をテキスト出力する補助スクリプト
例: `python tree_export.py web -o structure.txt` とすると構成を `structure.txt` に保存できます。

## 必要な環境
- Python 3.9 以上
- `pip` で以下の主要ライブラリをインストールしてください（例: `pip install discord.py aiohttp aiohttp-session aiolimiter python-dotenv pyotp qrcode pillow google-generativeai`）

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
| `SEND_INTERVAL_SEC` | 同一ファイルを同じ相手へ再送するまでの待ち時間 (秒)。既定値 `60` |
| `DATA_DIR` | アップロードファイルを保存するディレクトリ。既定値 `./data` |
| `STATIC_DIR` | 静的ファイルの格納場所。既定値 `./static` |
| `TEMPLATE_DIR` | HTML テンプレートの場所。既定値 `./templates` |
| `COOKIE_SECRET` | 44 文字の URL-safe Base64。セッション暗号化に使用 (**必須**) |
| `GEMINI_API_KEY` | Gemini API のキー。自動タグ付けに使用 |
| `GDRIVE_CREDENTIALS` | Google Drive OAuth クレデンシャルのパス |
| `GDRIVE_TOKEN` | OAuth 認証で生成されるトークンファイルの保存先。既定値 `token.json` |

`COOKIE_SECRET` は次のコマンドで生成できます。
```bash
python -c "import os,base64;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```
`pdf2image` を利用するため、システムに `poppler` がインストールされている必要があります。

## Google Drive 連携
`GDRIVE_CREDENTIALS` を設定すると、アップロードされたファイルは Google Drive にもコピーされます。
さらに `/import_gdrive` エンドポイントへ Drive のファイル ID を送信することで、Drive 上のファイルをローカルへ取り込めます。
`/gdrive_import` ページではブラウザからファイルIDまたは共有リンクを入力して取り込む簡易フォームを利用できます。
各ユーザーは初回利用時に `/gdrive_auth` を開き、Google アカウントのアクセスを許可してください。

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

## Web サーバー仕様
Web サーバー部分は `aiohttp` を用いた非同期アプリケーションとして実装されています。
主な仕様は以下の通りです。

- 起動ポートは環境変数 `PORT` (既定値 `9040`) で指定します。
- 各リクエストは 50 GiB までのアップロードを受け付けます。
- セッションは `EncryptedCookieStorage` で暗号化され、7 日間有効です。
- `POST` 系リクエストでは CSRF トークンを検証します。
- IP 単位で 60 秒あたり 30 リクエストに制限するレートリミット機能を備えています。
- `/health` エンドポイントではサーバーの状態を JSON で返します。
- `/mobile` ではスマートフォン向けテンプレートを提供します。
- Service Worker を導入し、主要な静的ファイルと `/offline` ページをキャッシュします。
- ナビゲーション失敗時はオフライン用ページ `/offline` を表示します。
- 静的ファイルは `stale-while-revalidate` 戦略で更新され、Push API による通知も利用できます。

## データベース初期化
初回起動時に自動的に SQLite のスキーマが作成されます。既にデータベースが存在する場合はそのまま使用されます。

## テスト
テストは `pytest` で実行できます。
依存パッケージを `pip install -r requirements.txt` でインストールした後、`pytest` を起動してください。
現在テストスクリプトは同梱されていません。

## セキュリティ
本システムでは以下の対策を行っています。

- パスワードは `scrypt` でハッシュ化して保存されます。
- 二要素認証 (TOTP) を任意で有効にできます。
- セッション情報は暗号化した Cookie に保存し、`Secure`、`HttpOnly`、`SameSite=Lax` 属性を付与しています。
- `POST` 系リクエストでは CSRF トークンを検証します。
- ダウンロードリンクには HMAC 署名付きトークンを採用し、有効期限を設定できます。
- `AsyncLimiter` によるレートリミットで DoS やブルートフォース攻撃を抑制します。
- 全ページのレスポンスに Content-Security-Policy ヘッダーを設定し、外部 CDN と自サイトからのリソースのみを許可しています。

## その他ドキュメント
サブディレクトリにも詳細な説明があります。
- `bot/README.md` … ボットコマンドの概要
- `web/README.md` … Web UI の利用方法
- `docs/architecture.mmd` … システム構成図
- `docs/sequence_system.mmd` … 全体のシーケンス図
- `docs/sequence_discord.mmd` … Discord 上のシーケンス図

## ライセンス
このプロジェクトは MIT ライセンスです。
