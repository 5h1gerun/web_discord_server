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
| `VAPID_PUBLIC_KEY` | Push API 用の VAPID 公開鍵 (Base64url) |
| `DISCORD_CLIENT_ID` | Discord OAuth2 のクライアント ID |
| `DISCORD_CLIENT_SECRET` | Discord OAuth2 のクライアントシークレット |

`PUBLIC_DOMAIN` は Google OAuth のリダイレクト先だけでなく、Discord OAuth にも使用されます。Google Cloud Console には `https://<PUBLIC_DOMAIN>/gdrive_callback`、Discord には `https://<PUBLIC_DOMAIN>/discord_callback` を登録してください。

`COOKIE_SECRET` は次のコマンドで生成できます。
```bash
python -c "import os,base64;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```
`pdf2image` を利用するため、システムに `poppler` がインストールされている必要があります。

## Google Drive 連携
`GDRIVE_CREDENTIALS` を設定すると、アップロードされたファイルは Google Drive にもコピーされます。
さらに `/import_gdrive` エンドポイントへ Drive のファイル ID を送信することで、Drive 上のファイルをローカルへ取り込めます。
`/gdrive_import` ページでは自身の Drive 上の最近のファイル一覧が表示され、ボタン一つで取り込みできます。ファイル名を入力すると自動的に検索され、一覧が絞り込まれます。入力フォームから直接ファイルIDや共有リンクを指定することも可能です。ダウンロード拒否マークが付いたファイルも自動的に `acknowledgeAbuse` オプションを付与して取得します。
ページ下部には個人フォルダへ戻るリンクも用意しています。初回利用時は `/gdrive_auth` を開き、Google アカウントのアクセスを許可してください。
2025 年 7 月以降は `drive.readonly` スコープも要求するようになったため、以前のトークンでは一覧が空になる場合があります。その際は `/gdrive_auth` を再実行してください。

OAuth 認証時の `state` はセッションに保存され、コールバック後に検証されます。Drive ファイル一覧取得に失敗した際はサーバー側のエラーメッセージが画面に表示されます。
Discord OAuth でログインする際は、過去に一度でも TOTP 認証を成功させたユーザーのみ二要素認証が省略されます。

## Webhook システム
共有フォルダでは、各チャンネルに `WDS Notify` という Webhook を紐付けており、アップロードのたびに自動通知を送信できます。
`/create_shared_folder` でフォルダを作成すると同名の Webhook が生成され、その URL がデータベースに保存されます。
ボットまたは Web からファイルをアップロードすると `notify_shared_upload` が呼び出され、Webhook 経由で「<@ユーザーID> が `<ファイル名>` をアップロードしました」のようにメンション付きで投稿されます。
誤って Webhook を削除した場合などは `/add_shared_webhook` コマンドで再登録が可能です。

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

- **パスワードハッシュに `scrypt` を使用**  
  ユーザーのパスワードはそのまま保存せず、計算量とメモリコストの高い `scrypt` でハッシュ化した値のみを保持します。ブルートフォース攻撃への耐性が高まります。
- **二要素認証 (TOTP) の任意利用**  
  初回設定時に QR コードで秘密鍵を共有し、その後は 6 桁の TOTP コードを入力して本人確認を行います。パスワードが漏洩しても認証コードがなければログインできません。
- **セッション情報は Cookie に保存し安全な属性を付与**  
  セッションは暗号化された Cookie に格納し、`Secure`、`HttpOnly`、`SameSite=Lax` を設定しています。Cookie 盗聴や XSS による被害を抑えます。
- **POST リクエストの CSRF トークン検証**  
  フォーム送信などの `POST` 操作では、セッションに保存した CSRF トークンを照合します。不一致の場合はリクエストを拒否し、外部サイトからの不正操作を防ぎます。
- **HMAC 署名付きダウンロードリンク**  
  ダウンロード URL には署名済みトークンを付与し、有効期限も設けます。サーバー側で署名と期限を検証することで、改ざんや期限切れリンクからのアクセスを防ぎます。
- **ファイルハッシュの保存**  
  アップロードされたファイルは `sha256` ハッシュを計算して記録します。重複検出や改ざん確認に利用されます。
- **`AsyncLimiter` によるレートリミット**  
  IP ごとに一定時間内のリクエスト数を制限し、DoS やブルートフォース攻撃を抑制します。
- **Content-Security-Policy (CSP) ヘッダー**  
  全ページのレスポンスに CSP ヘッダーを付与し、外部リソースの読み込み先を厳格に制御します。必要な CDN の `connect` 許可のみを与え、スクリプトインジェクションのリスクを低減します.
## その他ドキュメント
サブディレクトリにも詳細な説明があります。
- `bot/README.md` … ボットコマンドの概要
- `web/README.md` … Web UI の利用方法
- `docs/architecture.mmd` … システム構成図
- `docs/sequence_system.mmd` … 全体のシーケンス図
- `docs/sequence_discord.mmd` … Discord 上のシーケンス図
- `docs/sequence_web.mmd` … Web サーバ上のシーケンス図

## ライセンス
このプロジェクトは MIT ライセンスです。
