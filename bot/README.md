# Discord Bot

このディレクトリには Web Discord Server のボット側コードが含まれています。
ボットはファイル共有用 Web サーバーを同時に起動し、Discord 上の操作だけで
アップロード・共有・ダウンロードを行えるように設計されています。

## 主な機能
- サーバー参加時に自動登録し、ログイン情報と二要素認証(QRコード)をDMで送信
- `/upload` コマンドによるファイルアップロードと `/myfiles` での一覧表示
- 共有フォルダを作成しメンバーを招待する `/create_shared_folder`
- 各種ファイル操作(削除・タグ付け・共有状態切替・リンク取得)
- 管理者向けコマンド `/sync` `/admin_reset_totp` など
- `help` コマンドで全コマンドの詳細を確認可能

## コマンド一覧
`help` コマンドでは以下のコマンドを選択して詳細説明が表示されます。
- `ping` – レイテンシ確認
- `myfiles` – 自分のファイル一覧をページ表示
- `upload` – ファイルをアップロード
- `delete` / `delete_all` – 指定ファイルまたは全ファイル削除
- `set_tags` – ファイルにタグを設定
- `getfile` – 保存済みファイルを再送信
- `share` / `getlink` – 共有状態切替とダウンロードリンク取得
- `create_shared_folder` – 共有フォルダ作成
- `manage_shared_folder` – 共有フォルダのメンバー管理
- `shared_files` – 参加中フォルダ内のファイル一覧
- `delete_shared_folder` / `remove_shared_folder` – フォルダ削除・退出
- `upload_shared` – 共有フォルダへファイルアップロード
- `shared_delete_all` – 共有フォルダ内の全ファイル削除
- `set_shared_tags` – 共有フォルダ内ファイルのタグ設定
- `cleanup_shared` – 空の共有フォルダを一括削除
- `enable_totp` – 二要素認証を有効化
- `admin_reset_totp` – 管理者によるTOTPリセット

詳細な動作や必要な環境変数については上位ディレクトリの `README.md` を参照してください。
