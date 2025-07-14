# Web Dcloud Server プレゼン用まとめ

本ドキュメントは、PowerPoint で本システムを紹介する際の要点を箇条書きで整理したものです。

## システム概要
- Discord ボットと aiohttp 製 Web サーバーを統合したファイル共有システム
- ボット起動時に Web サーバーも同時に立ち上がり、ブラウザからアップロード済みファイルを閲覧・ダウンロード可能
- Gemini API による自動タグ付け機能を備え、Office 文書を含むさまざまな形式に対応

## 主な機能
- `/upload` や `/myfiles` などのボットコマンドでファイル操作を実施
- Google Drive 連携によりアップロード内容を Drive にコピー、または Drive からの取り込みが可能
- Web UI ではプレビュー付きダウンロード、タグ検索、共有リンク生成などを提供
- Service Worker によるオフライン対応と Push 通知
- QR コードを使ったモバイルログインや共有フォルダへの Webhook 通知

## セキュリティ対策
- パスワードは scrypt でハッシュ化し、二要素認証 (TOTP) を任意で利用
- HMAC 付きダウンロードリンクに有効期限を設け、CSRF トークン検証を実施
- IP 単位のレートリミットや Content-Security-Policy ヘッダーを設定

## アーキテクチャ
- Bot と Web サーバー、SQLite データベース、ファイルストレージが連携
- 自動タグ付けのため Gemini API を呼び出し、Drive 連携時は OAuth を利用
- サービスワーカーが静的ファイルをキャッシュし、オフライン時は `/offline` ページを表示

## 運用・環境
- Python 3.9 以上で動作し、主要ライブラリは `requirements.txt` で指定
- `.env` ファイルで Discord トークンや各種 API キー、ポート番号などを設定
- Raspberry Pi 5 + SSD 環境で確認済み。リバースプロキシには nginx を使用

## 参考資料
- `docs/architecture.mmd` : システム全体図
- `docs/sequence_system.mmd` : 一連の処理シーケンス
- `docs/sequence_discord.mmd` : Discord 上での流れ
- `docs/sequence_web.mmd` : Web サーバーでのやり取り
- `docs/sequence_pwa.mmd` : PWA の動作シーン

以上をスライドにまとめることで、システムの全体像と特徴を効果的に伝えられます。
