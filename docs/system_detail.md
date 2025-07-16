# Web Dcloud Server 詳細ドキュメント

このドキュメントでは、Discord ボットと aiohttp 製 Web サーバーから構成される Web Dcloud Server の仕組みや利用方法、セキュリティ対策などを総合的に説明します。

## システム概要
Web Dcloud Server は Discord 上でファイル共有を行うボットと、ブラウザからファイルを閲覧・ダウンロードできる Web サーバーを一体化したアプリケーションです。ボットの起動と同時に aiohttp 製 Web サーバーも開始され、アップロードしたファイルをリンク経由で共有できます。Gemini API を利用した自動タグ付け機能や Google Drive との連携のほか、Service Worker を使ったオフライン動作も備えています。

内部では Python の `asyncio` を用いた非同期処理が中心となっており、Discord ボット (`discord.py`) と Web サーバーが同じイベントループ上で動作します。ファイルメタデータは SQLite に保存され、アップロードデータは指定ディレクトリまたは Google Drive へ同期されます。

## Flask製サーバーとの違い
Web Dcloud Server の Web 部は aiohttp を利用した非同期サーバーです。WSGI ベースの Flask と比べ、以下のような特徴があります。

- イベントループで動作するため Discord ボットと同じプロセスで統合しやすく、各処理を await で協調的に実行できます。
- 大量のファイル入出力や Google Drive への同期といった I/O 待ち処理でも他のリクエストをブロックしません。
- WebSocket や Server-Sent Events を利用したリアルタイム通知を実装しやすく、Service Worker との連携が容易です。
- Flask では通常 Gunicorn などの別途 WSGI サーバーが必要ですが、本システムは aiohttp だけで HTTP サーバーとして完結します。


## ディレクトリ構成
- `bot/` … Discord ボットの実装
- `web/` … aiohttp による Web アプリケーション
- `integrations/` … 外部サービス連携モジュール
- `tests/` … pytest 用テストコード
- `docs/` … 本ドキュメントや構成図を格納
- `tree_export.py` … ディレクトリ構成を出力する補助スクリプト

各ディレクトリは以下のような役割を持ちます。

- **bot/**
  - `bot.py` … アプリケーションのエントリーポイント。Web サーバーの起動もここから行われます。
  - `commands.py` … スラッシュコマンドや管理者コマンドの定義。
  - `auto_tag.py` … Gemini API を呼び出し、アップロードファイルへ自動的にタグを付与する処理。
- **web/**
  - `app.py` … aiohttp アプリ本体。ルーティングやミドルウェア、テンプレート設定を担います。
  - `auth.py` … ログイン認証や TOTP、QR コードによるログイン補助ロジック。
  - `gdrive.py` … Google Drive とのファイル同期を管理。
- **integrations/**
  - サードパーティ API とのやり取りをモジュール化したもの。現在は Google Drive 用モジュールが中心です。
- **tests/**
  - Pytest を用いたユニットテスト・統合テストが格納されています。主要コマンドの動作や Web API のレスポンスを検証します。

## 主な機能
### Discord ボット
- サーバー参加時の自動登録と DM 送信
- `/upload` や `/myfiles` などの各種ファイル操作コマンド
- 共有フォルダの作成・管理と Webhook 通知
- Gemini API による自動タグ付け
- ファイル送信時には同一ファイルを同じ相手へ短時間で重複送信しないようインターバルを設けています
- 共有フォルダのメンバー管理や Webhook 再登録など、運用を支援する管理者向けコマンドも複数用意

### Web アプリ
- TOTP による二要素認証対応ログイン
- ドラッグ＆ドロップ可能なアップロードフォーム
- アップロード済みファイルの検索・共有・タグ編集
- 共有フォルダや Google Drive 連携機能
- Service Worker を利用したオフライン対応と Push 通知
- ファイル一覧はページングされ、`FILES_PER_PAGE` で件数を調整可能。初回ページは Service Worker が事前キャッシュ
- QR コードを用いた PC・スマホ間の連携ログイン
- `/health` や `/csrf_token` など API ベースのエンドポイントも備え、PWA からの利用を想定

## 主要な環境変数
| 変数 | 役割 |
| ---- | ---- |
| `DISCORD_TOKEN` | ボット起動に必須の Discord トークン |
| `DB_PATH` | SQLite データベース保存先 |
| `PUBLIC_DOMAIN` | 外部公開用ドメイン名 |
| `PORT` | Web サーバーのリッスンポート |
| `COOKIE_SECRET` | セッション暗号化用の秘密鍵 |
| `GEMINI_API_KEY` | 自動タグ付けに利用する Gemini API キー |
| `GDRIVE_CREDENTIALS` | Google Drive OAuth クレデンシャル |
| `GDRIVE_TOKEN` | 認証後に生成されるトークンの保存先 |
| `BOT_OWNER_ID` | ボット管理者の Discord ユーザー ID |
| `FORCE_HTTPS` | `1` を指定すると HTTP から HTTPS へ自動リダイレクト |
| `FILES_PER_PAGE` | ファイル一覧 API の1ページあたり件数。既定値 `50` |
| `VAPID_PUBLIC_KEY` | Push API 用の VAPID 公開鍵 |

その他の環境変数については `README.md` を参照してください。

## セキュリティ対策
- パスワードを `scrypt` でハッシュ化
- TOTP による二要素認証を任意で利用可能
- CSRF トークンの検証と HMAC 署名付きダウンロードリンク
- レートリミットや Content-Security-Policy ヘッダーの設定
- セッション Cookie には `Secure` `HttpOnly` `SameSite=Lax` を付与
- ファイルアップロード時に `sha256` ハッシュを計算し改ざん検出
- AsyncLimiter による DoS 攻撃対策
- Service Worker 経由のキャッシュには version パラメータを付与し、不正なスクリプト更新を防止

## 動作確認とテスト
Python 3.9 以上と依存パッケージのインストール後、`pytest -q` を実行するとテストが実行されます。本リポジトリでは 70 以上のテストが用意されており、主要機能が自動的に検証されます。

## ワークフロー例
アップロードからダウンロードまでの典型的な流れは以下の通りです。
1. Discord 上で `/upload` コマンドを実行し、対象ファイルを添付して送信。
2. ボットがファイルを保存し、Gemini API によるタグ解析を実施。Google Drive 連携があれば Drive にもコピー。
3. データベースへメタ情報を登録後、ダウンロードリンクをユーザーへ DM で通知。
4. ユーザーがリンクを開くと Web サーバーで認証を行い、署名付き URL からファイルを取得。
5. Web UI 上ではタグ編集や共有期限の延長、QR コード生成などの追加操作が可能です。

## 参考ドキュメント
- `docs/architecture.mmd` … システム全体の構成図
- `docs/sequence_system.mmd` … ボットと Web サーバーを含むシーケンス図
- `docs/sequence_discord.mmd` … Discord 上の操作シーケンス
- `docs/sequence_web.mmd` … Web サーバー内部のシーケンス
- `docs/sequence_pwa.mmd` … PWA でのオフライン動作シーン

以上が Web Dcloud Server の全体像です。詳細な設定やコマンドについては各 README を参照してください。
