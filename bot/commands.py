"""bot/commands.py – スラッシュコマンド定義（日本語）

| コマンド        | 説明                                                         |
|-----------------|----------------------------------------------------------------|
| /ping           | レイテンシを確認                                              |
| /myfiles        | ページ送りでファイルカタログを表示                            |
| /upload         | Nitro プラン別上限でファイルをアップロード                   |
| /delete         | 自分のファイルを削除                                          |
| /getfile        | ファイルをDiscordに送信 (上限超過時はリンクで返却)              |
| /share          | ファイルの共有状態を切り替え (ファイル所有者のみ)              |
| /getlink        | ファイルのダウンロードリンクを取得 (共有中 or 所有者)           |
| /get_login      | Bot 製作者 (BOT_OWNER_ID) が自分のログイン情報を DM 取得       |
| /sync           | コマンドツリーを同期（オーナー専用）                          |
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional
from .help import setup_help

import discord
from discord import app_commands
from discord import Embed, Member
from discord.app_commands import describe

import io                # 画像バッファ用
import qrcode            # QR 生成
import pyotp             # TOTP ライブラリ  ←★ここを追加★

import base64


# 環境変数
FILE_HMAC_SECRET = base64.urlsafe_b64decode(
    os.getenv("FILE_HMAC_SECRET", "").encode() or os.urandom(32)
)
URL_EXPIRES_SEC = int(os.getenv("UPLOAD_EXPIRES_SEC", 86400))  # 24h
DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

def make_otp_link(uri: str) -> str:
    token = base64.urlsafe_b64encode(uri.encode()).decode()
    return f"https://{os.getenv('PUBLIC_DOMAIN','localhost:9040')}/otp/{token}"


# Discord 添付アップロード制限 (Nitroプラン別)
SIZE_LIMIT = {2: 500 << 20, 1: 100 << 20, 0: 25 << 20}

# ダウンロードリンク署名

def _sign(fid: str, exp: int) -> str:
    msg = f"{fid}:{exp}".encode()
    sig = hmac.new(FILE_HMAC_SECRET, msg, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(msg + b":" + sig).decode()


def _crop(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit-1] + "…"

# カタログ表示用 View
class CatalogView(discord.ui.View):
    MAX_NAME = 256
    MAX_VAL  = 1024

    def _embed(self) -> discord.Embed:
        now  = int(datetime.now(timezone.utc).timestamp())
        emb  = discord.Embed(title=f"あなたのファイル – {self.page+1}/{self.maxp+1}")

        for r in self.rows[self.page*self.per:(self.page+1)*self.per]:
            url   = f"https://{os.getenv('PUBLIC_DOMAIN','localhost:9040')}/download/{_sign(r['id'], now+URL_EXPIRES_SEC)}"

            name  = _crop(r["original_name"], self.MAX_NAME)
            value = _crop(f"ID:`{r['id']}` · {r['size']/1024:.1f} KB\n[DL]({url})", self.MAX_VAL)
            emb.add_field(name=name, value=value, inline=False)

        return emb
    def __init__(self, rows: List[Dict[str, object]], uid: int, per: int = 10):
        super().__init__(timeout=180)
        self.rows, self.uid, self.per = rows, uid, per
        self.page, self.maxp = 0, max(0, (len(rows) - 1) // per)
        self.msg: Optional[discord.Message] = None
        self._update_btn()

    def _update_btn(self):
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= self.maxp

    async def _refresh(self, it: discord.Interaction):
        self._update_btn()
        if self.msg:
            await self.msg.edit(embed=self._embed(), view=self)
        else:
            self.msg = await it.followup.send(embed=self._embed(), view=self, ephemeral=True)

    @discord.ui.button(label="◀ 前へ", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, it: discord.Interaction, _):
        if it.user.id == self.uid:
            self.page -= 1
            await it.response.defer()
            await self._refresh(it)

    @discord.ui.button(label="次へ ▶", style=discord.ButtonStyle.primary)
    async def next_btn(self, it: discord.Interaction, _):
        if it.user.id == self.uid:
            self.page += 1
            await it.response.defer()
            await self._refresh(it)

# 共有フォルダ用ビューとコントロール
class ManageFolderView(discord.ui.View):
    def __init__(self, bot, folder_id: str, channel: discord.TextChannel, members: List[discord.Member], non_members: List[discord.Member]):
        super().__init__(timeout=300)
        self.bot = bot
        self.folder_id = folder_id
        self.channel = channel
        self.members = members
        self.non_members = non_members
        # 非メンバー追加セレクト
        if self.non_members:
            self.add_item(MemberAddSelect(self))
        # メンバー削除ボタン
        for m in self.members:
            self.add_item(MemberRemoveButton(self, m))

# ---- ① Select ----
class MemberAddSelect(discord.ui.Select):
    def __init__(self, parent: 'ManageFolderView'):   # 型ヒントを parent に変更
        self.parent = parent                          # ← 別名で保持
        options = [
            discord.SelectOption(label=m.display_name, value=str(m.id))
            for m in parent.non_members[:25]
        ]
        super().__init__(placeholder="メンバーを追加", options=options,
                         min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        uid = int(self.values[0])
        member = interaction.guild.get_member(uid)
        if member:
            await self.parent.channel.set_permissions(
                member, read_messages=True, send_messages=True)

            await self.parent.bot.db.execute(
                "INSERT OR IGNORE INTO shared_folder_members (folder_id, discord_user_id) "
                "VALUES (?, ?)",
                self.parent.folder_id, member.id
            )
            await self.parent.bot.db.commit()
            await interaction.response.send_message(
                f"✅ {member.display_name} を追加しました。", ephemeral=True)


# ---- ② Button ----
class MemberRemoveButton(discord.ui.Button):
    def __init__(self, parent: 'ManageFolderView', member: discord.Member):
        super().__init__(label=f"🗑 {member.display_name}",
                         style=discord.ButtonStyle.danger)
        self.parent = parent
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        await self.parent.channel.set_permissions(self.member, overwrite=None)
        await self.parent.bot.db.execute(
            "DELETE FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            self.parent.folder_id, self.member.id
        )
        await self.parent.bot.db.commit()
        await interaction.response.send_message(
            f"🗑 {self.member.display_name} を削除しました。", ephemeral=True)

class DeleteSharedFolderView(discord.ui.View):
    def __init__(self, bot, user: discord.User, folders: list[dict]):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user

        # セレクトを動的に生成してから、callback を紐付け
        options = [discord.SelectOption(label=f["name"], value=str(f["id"])) for f in folders]
        select = discord.ui.Select(
            placeholder="削除したい共有フォルダを選択してください",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="delete_shared_folder_select"
        )
        select.callback = self.select_folder
        self.add_item(select)

    async def select_folder(self, interaction: discord.Interaction):
        # interaction.data["values"] に選択された値のリストが入っている
        folder_id = int(interaction.data["values"][0])
        db = self.bot.db

        # 共有フォルダ情報取得
        rec = await db.get_shared_folder(folder_id)
        if not rec:
            return await interaction.response.send_message("❌ フォルダ情報が見つかりません。", ephemeral=True)

        channel = interaction.guild.get_channel(rec["channel_id"])
        perm = channel.permissions_for(interaction.user) if channel else None
        is_owner = bool(perm and perm.manage_channels)

        if is_owner:
            # オーナー：チャンネル削除＋DB完全削除
            if channel:
                await channel.delete(reason=f"Shared folder deletion by {interaction.user}")
            await db.delete_shared_folder(folder_id)
            await interaction.response.send_message(f"✅ 共有フォルダ `{rec['name']}` を完全に削除しました。", ephemeral=True)
        else:
            # メンバー：参加解除のみ
            member = interaction.guild.get_member(interaction.user.id)
            if channel and member:
                await channel.set_permissions(member, overwrite=None)
            await db.delete_shared_folder_member(folder_id, interaction.user.id)
            await interaction.response.send_message(f"🗑️ `{rec['name']}` からの参加を解除しました。", ephemeral=True)

# コマンド登録
def setup_commands(bot: discord.Client):
    tree, owner_id = bot.tree, getattr(bot, "owner_id", None)

    @tree.command(name="ping", description="レイテンシを確認します。")
    async def _ping(i: discord.Interaction):
        await i.response.send_message(f"Pong! `{int(bot.latency*1000)} ms`", ephemeral=True)

    @tree.command(name="myfiles", description="ファイルカタログを表示します。")
    async def _myfiles(i: discord.Interaction):
        await i.response.defer(thinking=True, ephemeral=True)

        # DBインスタンスを bot から取得
        db = bot.db

        if db.conn is None:
            await i.followup.send("データベース接続がありません。少々お待ちください。", ephemeral=True)
            return

        pk = await db.get_user_pk(i.user.id)
        if pk is None:
            await i.followup.send("ユーザー登録が見つかりません。", ephemeral=True)
            return
        rows = await db.list_files(pk)
        if not rows:
            await i.followup.send("ファイルがありません。", ephemeral=True)
            return
        view = CatalogView(rows, i.user.id)
        await view._refresh(i)

    @tree.command(name="upload", description="添付ファイルをアップロードします。")
    async def _upload(i: discord.Interaction, file: discord.Attachment):
        db = i.client.db
        limit = SIZE_LIMIT.get(int(getattr(i.user, "premium_type", 0)), 25 << 20)
        if file.size > limit:
            await i.response.send_message(f"❌ 上限 {limit>>20} MiB を超えています。", ephemeral=True)
            return
        pk = await db.get_user_pk(i.user.id)
        if pk is None:
            await i.response.send_message("ユーザー登録が見つかりません。", ephemeral=True)
            return
        await i.response.defer(thinking=True, ephemeral=True)
        data = await file.read()
        fid = str(uuid.uuid4())
        path = DATA_DIR / fid
        path.write_bytes(data)
        from .auto_tag import generate_tags
        tags = generate_tags(path)
        await db.add_file(fid, pk, file.filename, str(path), len(data), hashlib.sha256(data).hexdigest(), tags)
        now = int(datetime.now(timezone.utc).timestamp())
        url = f"https://{os.getenv('PUBLIC_DOMAIN','localhost:9040')}/download/{_sign(fid, now+URL_EXPIRES_SEC)}"
        emb = discord.Embed(title="✅ アップロード完了", description=f"[DL]({url})", colour=0x2ecc71)
        emb.add_field(name="サイズ", value=f"{len(data)/1024/1024:.1f} MiB", inline=True)
        await i.followup.send(embed=emb, ephemeral=True)
        if owner_id and (owner := bot.get_user(owner_id)):
            try:
                await owner.send(f"📥 **{i.user}** が `{file.filename}` をアップロードしました。")
            except discord.Forbidden:
                pass

    @tree.command(name="delete", description="自分のファイルを削除します。")
    async def _delete(i: discord.Interaction, file_id: str):
        db = i.client.db
        await i.response.defer(ephemeral=True)
        rec = await db.get_file(file_id)
        pk = await db.get_user_pk(i.user.id)
        if not rec or rec["user_id"] != pk:
            await i.followup.send("❌ 見つからないか権限なし。", ephemeral=True)
            return
        Path(rec["path"]).unlink(missing_ok=True)
        await db.delete_file(file_id)
        await i.followup.send("🗑️ 削除しました。", ephemeral=True)

    @tree.command(name="delete_all", description="自分の全ファイルを削除します。")
    async def _delete_all(i: discord.Interaction):
        db = i.client.db
        await i.response.defer(thinking=True, ephemeral=True)
        pk = await db.get_user_pk(i.user.id)
        if pk is None:
            await i.followup.send("ユーザー登録が見つかりません。", ephemeral=True)
            return
        rows = await db.fetchall("SELECT path FROM files WHERE user_id=?", pk)
        for r in rows:
            Path(r["path"]).unlink(missing_ok=True)
        await db.delete_all_files(pk)
        await i.followup.send(f"🗑️ {len(rows)} 件のファイルを削除しました。", ephemeral=True)

    @tree.command(name="set_tags", description="ファイルにタグを設定します。")
    async def _set_tags(i: discord.Interaction, file_id: str, tags: str):
        db = i.client.db
        await i.response.defer(ephemeral=True)
        rec = await db.get_file(file_id)
        pk = await db.get_user_pk(i.user.id)
        if not rec or rec["user_id"] != pk:
            await i.followup.send("❌ 見つからないか権限なし。", ephemeral=True)
            return
        await db.update_tags(file_id, tags)
        await i.followup.send("✅ タグを更新しました。", ephemeral=True)

    @tree.command(name="shared_delete_all", description="共有フォルダ内の全ファイルを削除します。")
    async def _shared_delete_all(i: discord.Interaction, channel: discord.TextChannel):
        db = i.client.db
        await i.response.defer(ephemeral=True)
        rec = await db.get_shared_folder_by_channel(channel.id)
        if not rec:
            return await i.followup.send("❌ このチャンネルは共有フォルダではありません。", ephemeral=True)
        perm = channel.permissions_for(i.user)
        if not (perm.view_channel and perm.send_messages):
            return await i.followup.send("❌ あなたはこの共有フォルダに参加していません。", ephemeral=True)
        await db.delete_all_shared_files(rec["id"])
        await i.followup.send("🗑️ フォルダ内のファイルを削除しました。", ephemeral=True)

    @tree.command(name="set_shared_tags", description="共有フォルダ内ファイルのタグを設定します。")
    async def _set_shared_tags(i: discord.Interaction, file_id: str, tags: str):
        db = i.client.db
        await i.response.defer(ephemeral=True)
        sf = await db.get_shared_file(file_id)
        if not sf:
            return await i.followup.send("❌ 見つかりません。", ephemeral=True)
        member = await db.fetchone(
            "SELECT 1 FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            sf["folder_id"], i.user.id
        )
        if member is None:
            return await i.followup.send("❌ 権限がありません。", ephemeral=True)
        await db.update_shared_tags(file_id, tags)
        await i.followup.send("✅ タグを更新しました。", ephemeral=True)

    @tree.command(name="getfile", description="指定したファイルを取得します。")
    async def _getfile(i: discord.Interaction, file_id: str):
        db = i.client.db
        await i.response.defer(ephemeral=True)
        rec = await db.get_file(file_id)
        pk = await db.get_user_pk(i.user.id)
        if not rec or (rec["user_id"] != pk and not rec.get("is_shared", False)):
            await i.followup.send("❌ 見つからないか権限なし。", ephemeral=True)
            return
        size = rec["size"]
        limit = SIZE_LIMIT.get(int(getattr(i.user, "premium_type", 0)), 25 << 20)
        if size <= limit:
            await i.followup.send(file=discord.File(Path(rec["path"]), filename=rec["original_name"]))
        else:
            now = int(datetime.now(timezone.utc).timestamp())
            url = f"https://{os.getenv('PUBLIC_DOMAIN','localhost:9040')}/download/{_sign(file_id, now+URL_EXPIRES_SEC)}"
            await i.followup.send(f"🔗 ダウンロードリンク: {url}", ephemeral=True)

    @tree.command(name="share", description="ファイルの共有状態を切り替えます（所有者のみ）")
    @app_commands.describe(file_id="操作対象のファイル ID")
    async def _share(i: discord.Interaction, file_id: str):
        db = i.client.db
        await i.response.defer(ephemeral=True)
        rec = await db.get_file(file_id)
        pk = await db.get_user_pk(i.user.id)
        if not rec:
            await i.followup.send("❌ ファイルが見つかりません。", ephemeral=True)
            return
        if rec['user_id'] != pk:
            await i.followup.send("❌ あなたはこのファイルの所有者ではありません。", ephemeral=True)
            return
        # ここを変更 ↓
        current_shared = bool(rec["is_shared"]) if "is_shared" in rec.keys() else False
        new_state = not current_shared
        # ↑ここまで
        await db.set_shared(file_id, new_state)
        status = '共有' if new_state else '非共有'
        await i.followup.send(f"✅ ファイル {file_id} を{status}にしました。", ephemeral=True)

    @tree.command(name="getlink", description="ファイルのダウンロードリンクを取得します。")
    @app_commands.describe(file_id="リンク取得対象のファイル ID")
    async def _getlink(i: discord.Interaction, file_id: str):
        db = i.client.db
        await i.response.defer(ephemeral=True)

        rec = await db.get_file(file_id)
        pk = await db.get_user_pk(i.user.id)
        # sqlite3.Row は dict.get を持たないので、直接キーで参照します
        is_shared = bool(rec["is_shared"]) if rec and "is_shared" in rec.keys() else False

        if not rec or (not is_shared and rec["user_id"] != pk):
            await i.followup.send("❌ 見つからないか権限なし。", ephemeral=True)
            return

        now = int(datetime.now(timezone.utc).timestamp())
        token = _sign(file_id, now + URL_EXPIRES_SEC)
        url = f"https://{os.getenv('PUBLIC_DOMAIN','localhost:9040')}/download/{token}"

        await i.followup.send(f"🔗 ダウンロードリンク: {url}", ephemeral=True)


    @tree.command(name="get_login", description="ログイン情報を DM で取得します（オーナー専用）")
    async def _get_login(i: discord.Interaction):
        db = i.client.db
        if i.user.id != owner_id:
            await i.response.send_message("権限がありません。", ephemeral=True)
            return
        pw = secrets.token_urlsafe(12)
        await db.add_user(i.user.id, str(i.user), pw)
        login_url = f"https://{os.getenv('PUBLIC_DOMAIN','localhost:9040')}/login"
        await i.response.send_message(
            f"🔑 **ログイン情報**\nURL: {login_url}\nユーザ名: {i.user}\nパスワード: `{pw}`",
            ephemeral=True,
        )

    @tree.command(name="sync", description="コマンドを同期します（オーナー専用）")
    async def _sync(i: discord.Interaction):
        db = i.client.db
        if i.user.id != owner_id:
            await i.response.send_message("権限がありません。", ephemeral=True)
            return
        await i.response.defer(thinking=True, ephemeral=True)
        await tree.sync()
        await i.followup.send("✅ 同期しました。", ephemeral=True)

    @tree.command(
        name="create_shared_folder",
        description="フォルダを作成して指定メンバーと共有します（所有者のみ）"
    )
    @app_commands.describe(
        folder_name="作成するフォルダ名",
        members="共有メンバー（例: @User1 @User2 の形式で複数可）"
    )
    async def create_shared_folder(
        interaction: discord.Interaction,
        folder_name: str,
        members: str,
    ):
        await interaction.response.defer(ephemeral=True)
        db = interaction.client.db

        # メンバー解析
        member_objs: list[discord.Member] = []
        for token in members.split():
            member_id = token.strip("<@!>")
            if member_id.isdigit():
                m = interaction.guild.get_member(int(member_id))
                if m:
                    member_objs.append(m)
        if not member_objs:
            await interaction.followup.send("❌ 有効なメンバーが指定されていません。", ephemeral=True)
            return

        # 1) Discord 側でチャンネルを先に作成
        category = discord.utils.get(interaction.guild.categories, name="共有フォルダ")
        if not category:
            category = await interaction.guild.create_category(
                "共有フォルダ",
                overwrites={interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
            )
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, manage_channels=True),
            **{m: discord.PermissionOverwrite(view_channel=True) for m in member_objs}
        }
        channel = await interaction.guild.create_text_channel(
            name=folder_name,
            overwrites=overwrites,
            category=category
        )
        webhook = await channel.create_webhook(name="WDS Notify")

        # 2) DB に name, channel_id, webhook URL を登録
        shared_id = await db.create_shared_folder(folder_name, channel.id, webhook.url)

        # メンバー登録
        for m in member_objs:
            await db.add_shared_folder_member(shared_id, m.id)

        # 4）オーナー自身もメンバーとして登録 ← ここを追加！
        await db.add_shared_folder_member(shared_id, interaction.user.id)

        # 結果を返す
        embed = discord.Embed(
            title="📁 共有フォルダ作成完了",
            description=(
                f"フォルダ `{folder_name}` を作成し、"
                f"{', '.join(m.mention for m in member_objs)} と共有しました。\n"
                f"▶️ チャンネル: {channel.mention}"
            ),
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


    @tree.command(name="manage_shared_folder", description="共有フォルダのメンバーを管理します。")
    @app_commands.describe(channel="対象の共有チャンネル")
    async def manage_shared_folder(i: discord.Interaction, channel: discord.TextChannel):
        db = i.client.db
        await i.response.defer(ephemeral=True)
        bot = i.client
        row = await bot.db.fetchone("SELECT id FROM shared_folders WHERE channel_id = ?", channel.id)
        if not row:
            await i.followup.send("❌ このチャンネルは共有フォルダではありません。", ephemeral=True); return
        fid = row["id"]
        all_m = [m for m in channel.guild.members if not m.bot and m.joined_at]
        curr = await bot.db.fetchall("SELECT discord_user_id FROM shared_folder_members WHERE folder_id = ?", fid)
        curr_ids = {r["discord_user_id"] for r in curr}
        members = [m for m in all_m if m.id in curr_ids]
        non_m = [m for m in all_m if m.id not in curr_ids]
        view = ManageFolderView(bot, fid, channel, members, non_m)
        await i.followup.send("🔧 メンバー管理", view=view, ephemeral=True)

    @tree.command(name="shared_files", description="自分が属する共有フォルダのファイルを確認します。")
    async def shared_files(i: discord.Interaction):
        db = i.client.db
        await i.response.defer(ephemeral=True)
        bot = i.client
        ufs = await bot.db.fetchall(
            "SELECT sf.name, sf.id FROM shared_folders sf JOIN shared_folder_members m ON sf.id=m.folder_id WHERE m.discord_user_id=?", i.user.id
        )
        if not ufs:
            await i.followup.send("あなたは共有フォルダに参加していません。", ephemeral=True); return
        emb = discord.Embed(title="あなたの共有フォルダ一覧")
        for f in ufs:
            rows = await bot.db.fetchall("SELECT file_name, uploaded_at FROM shared_files WHERE folder_id=?", f["id"])
            content = "\n".join([f"{r['file_name']} ({r['uploaded_at']})" for r in rows]) or "ファイルなし"
            emb.add_field(name=f["name"], value=content, inline=False)
        await i.followup.send(embed=emb, ephemeral=True)

    @tree.command(
        name="delete_shared_folder",
        description="共有フォルダとリンク済みチャンネルを削除します（所有者 or 管理者向け）"
    )
    @app_commands.describe(
        channel="削除したい共有フォルダ用チャンネルを選択"
    )
    async def delete_shared_folder(
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        await interaction.response.defer(ephemeral=True)
        db = interaction.client.db

        # 1) DB からレコード取得
        rec = await db.get_shared_folder_by_channel(channel.id)
        if not rec:
            await interaction.followup.send("❌ 指定されたチャンネルは共有フォルダ用ではありません。", ephemeral=True)
            return

        # 2) チャンネル削除
        await channel.delete(reason=f"Shared folder deletion by {interaction.user}")

        # 3) DB 上も削除（folder_members は CASCADE で消える想定）
        await db.delete_shared_folder(rec["id"])

        # 4) 完了通知
        await interaction.followup.send(
            f"✅ 共有フォルダ `{rec['name']}` (ID:{rec['id']}) を削除しました。",
            ephemeral=True
        )

    @tree.command(
        name="upload_shared",
        description="共有フォルダ用チャンネルにファイルをアップロードします。"
    )
    @app_commands.describe(
        channel="アップロード先の共有フォルダ用チャンネルを選択",
        file="アップロードするファイル（添付）"
    )
    async def upload_shared(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        file: discord.Attachment
    ):
        await interaction.response.defer(thinking=True, ephemeral=True)
        db = interaction.client.db

        # 1) channel が共有フォルダかチェック
        rec = await db.get_shared_folder_by_channel(channel.id)
        if not rec:
            await interaction.followup.send("❌ 指定されたチャンネルは共有フォルダ用ではありません。", ephemeral=True)
            return
        folder_id = rec["id"]

        # 2) チャンネルの閲覧 or 送信権限を見て、参加者かどうか判定
        perm = channel.permissions_for(interaction.user)
        if not (perm.view_channel and perm.send_messages):
            await interaction.followup.send("❌ あなたはこの共有フォルダに参加していません。", ephemeral=True)
            return

        # 3) ファイルサイズ制限チェック（Nitro 別）
        limit = SIZE_LIMIT.get(int(getattr(interaction.user, "premium_type", 0)), 25 << 20)
        if file.size > limit:
            await interaction.followup.send(f"❌ 上限 {limit>>20} MiB を超えています。", ephemeral=True)
            return

        # 4) ファイル保存＆DB 登録
        data = await file.read()
        fid = str(uuid.uuid4())
        path = DATA_DIR / fid
        path.write_bytes(data)
        from .auto_tag import generate_tags
        tags = generate_tags(path)
        await db.add_shared_file(fid, folder_id, file.filename, str(path), tags)

        # 5) Webhook で通知
        await interaction.client.notify_shared_upload(folder_id, interaction.user, file.filename)

        # 6) 成功通知を返す
        await interaction.followup.send("✅ 共有フォルダにアップロードしました。", ephemeral=True)

    @tree.command(
        name="add_shared_webhook",
        description="既存の共有フォルダにWebhook通知を設定します。"
    )
    @app_commands.describe(channel="Webhookを設定する共有フォルダのチャンネル")
    async def add_shared_webhook(
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        await interaction.response.defer(ephemeral=True)
        db = interaction.client.db

        rec = await db.get_shared_folder_by_channel(channel.id)
        if not rec:
            await interaction.followup.send("❌ 指定されたチャンネルは共有フォルダではありません。", ephemeral=True)
            return

        perm = channel.permissions_for(interaction.user)
        if not perm.manage_channels:
            await interaction.followup.send("❌ この共有フォルダを管理する権限がありません。", ephemeral=True)
            return

        webhook = await channel.create_webhook(name="WDS Notify")
        await db.set_folder_webhook(rec["id"], webhook.url)
        await interaction.followup.send("✅ Webhook を設定しました。", ephemeral=True)

    @tree.command(name="cleanup_shared", description="空の共有フォルダをまとめて削除します。")
    async def cleanup_shared(i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        db = i.client.db

        # 空フォルダ一覧を取得
        rows = await db.fetchall(
            "SELECT id, name, channel_id FROM shared_folders "
            "WHERE id NOT IN (SELECT folder_id FROM shared_files)"
        )
        if not rows:
            return await i.followup.send("✅ 空の共有フォルダはありません。", ephemeral=True)

        cnt = 0
        for r in rows:
            # チャンネルも削除
            ch = i.guild.get_channel(r["channel_id"])
            if ch:
                await ch.delete(reason="空の共有フォルダクリーンアップ")
            await db.delete_shared_folder(r["id"])
            cnt += 1

        await i.followup.send(f"✅ {cnt} 件の空フォルダを削除しました。", ephemeral=True)

    # commands.py ── setup_commands() の中
    @tree.command(name="enable_totp",
                description="二要素認証 (TOTP) を有効化して QR を DM で受け取ります。")
    async def enable_totp(inter: discord.Interaction):
        bot, db = inter.client, inter.client.db
        await inter.response.defer(ephemeral=True)

        row = await db.fetchone(
            "SELECT totp_enabled FROM users WHERE discord_id=?", inter.user.id
        )
        if row and row["totp_enabled"]:
            return await inter.followup.send("✅ すでに有効化済みです。", ephemeral=True)

        # 新シークレット + バックアップ発行
        secret = pyotp.random_base32()
        await db.execute(
            "UPDATE users SET totp_secret=?, totp_enabled=1 WHERE discord_id=?",
            secret, inter.user.id,
        )
        await db.commit()

        uri      = pyotp.TOTP(secret).provisioning_uri(str(inter.user), issuer_name="WDS")
        otp_link = make_otp_link(uri)

        qr  = qrcode.make(uri)
        buf = io.BytesIO(); qr.save(buf, format="PNG"); buf.seek(0)

        try:
            await inter.user.send(
                "🔐 **二要素認証を設定してください**\n"
                f"QR が読めない場合はリンクをタップ:\n{otp_link}\n"
                f"`{secret}`",
                file=discord.File(buf, "totp.png")
            )
            await inter.followup.send("📨 DM に QR を送信しました！", ephemeral=True)
        except discord.Forbidden:
            await inter.followup.send("❌ DM が拒否されています。", ephemeral=True)

    @tree.command(
        name="admin_reset_totp",
        description="[ADMIN] ユーザの TOTP を無効化します"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_reset_totp(inter: discord.Interaction, user: discord.Member):
        db = inter.client.db                   # ← これを追加
        await db.execute(
            "UPDATE users SET totp_enabled=0 WHERE discord_id=?",
            user.id
        )
        await db.commit()

        await inter.response.send_message(
            f"✅ {user.display_name} の TOTP を無効化しました。", ephemeral=True
        )

        # 本人へ通知（DM 拒否は握り潰し）
        try:
            await user.send(
                "🔄 管理者が TOTP をリセットしました。\n"
                "/enable_totp で再設定してください。"
            )
        except discord.Forbidden:
            pass

    # ── ② コマンド登録 ──
    @tree.command(
        name="remove_shared_folder",
        description="共有フォルダを削除または参加解除します"
    )
    async def remove_shared_folder(i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        db = i.client.db

        # 1) shared_folders 全件取得
        all_folders = await db.fetchall("SELECT id, name, channel_id FROM shared_folders")

        owner_folders = []
        member_folders = []
        for f in all_folders:
            ch = i.guild.get_channel(f["channel_id"])
            if ch and ch.permissions_for(i.user).manage_channels:
                owner_folders.append({"id": f["id"], "name": f["name"], "channel_id": f["channel_id"]})
            else:
                # メンバー登録があるかチェック
                row = await db.fetchone(
                    "SELECT 1 FROM shared_folder_members WHERE folder_id=? AND discord_user_id=?",
                    f["id"], i.user.id
                )
                if row:
                    member_folders.append({"id": f["id"], "name": f["name"], "channel_id": f["channel_id"]})

        # オーナーUI優先、それ以外はメンバーUI
        folders = owner_folders if owner_folders else member_folders
        if not folders:
            return await i.followup.send("❌ 操作可能な共有フォルダがありません。", ephemeral=True)


        view = DeleteSharedFolderView(i.client, i.user, folders)
        await i.followup.send("共有フォルダの削除メニューです。", view=view, ephemeral=True)

    @tree.command(name="search_files", description="タグで自分のファイルを検索します")
    @app_commands.describe(tag="検索ワード")
    async def search_files_cmd(i: discord.Interaction, tag: str):
        db = i.client.db
        pk = await db.get_user_pk(i.user.id)
        if pk is None:
            await i.response.send_message("ユーザー登録が見つかりません。", ephemeral=True)
            return
        rows = await db.search_files(pk, tag)
        if not rows:
            await i.response.send_message("該当ファイルがありません。", ephemeral=True)
            return
        now = int(datetime.now(timezone.utc).timestamp())
        emb = discord.Embed(title=f"検索結果: {tag}")
        for r in rows[:10]:
            url = f"https://{os.getenv('PUBLIC_DOMAIN','localhost:9040')}/download/{_sign(r['id'], now+URL_EXPIRES_SEC)}"
            emb.add_field(name=r['original_name'], value=f"[DL]({url}) tags:{r['tags']}", inline=False)
        await i.response.send_message(embed=emb, ephemeral=True)