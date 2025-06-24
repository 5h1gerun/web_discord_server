"""Async DB layer for Web_Discord_Server"""

from __future__ import annotations

# ── 標準ライブラリ ─────────────────────────
import asyncio, os, secrets, hashlib
import datetime as dt
from pathlib import Path
from typing import Any, List, Optional

# ── サードパーティ ────────────────────────
import aiosqlite
import scrypt                       # pip install scrypt

# ── パス & 定数 ───────────────────────────
DB_PATH = Path(__file__).parents[1] / "data" / "web_discord_server.db"

SCRYPT_N, SCRYPT_r, SCRYPT_p = 2**15, 8, 1     # 32768:8:1
SCRYPT_BUFLEN = 64                             # 512-bit

# ── スキーマ ──────────────────────────────
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id  INTEGER UNIQUE,
    username    TEXT    UNIQUE NOT NULL,
    pw_hash     TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS files (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    path          TEXT    NOT NULL,
    original_name TEXT    NOT NULL,
    size          INTEGER NOT NULL,
    sha256        TEXT    NOT NULL,
    uploaded_at   TEXT    NOT NULL,
    expires_at    INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

# ── scrypt util ────────────────────────────
def scrypt_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = scrypt.hash(password.encode(), salt,
                    N=SCRYPT_N, r=SCRYPT_r, p=SCRYPT_p, buflen=SCRYPT_BUFLEN)
    return f"{SCRYPT_N}:{SCRYPT_r}:{SCRYPT_p}${salt.hex()}${dk.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        params, salt_hex, dk_hex = hashed.split("$")
        n, r, p = map(int, params.split(":"))
        salt, dk_exp = bytes.fromhex(salt_hex), bytes.fromhex(dk_hex)
        dk_act = scrypt.hash(password.encode(), salt, N=n, r=r, p=p, buflen=len(dk_exp))
        return secrets.compare_digest(dk_act, dk_exp)
    except Exception:
        return False

# ── DB 初期化 ──────────────────────────────
async def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()

# ───────────────────────────────────────────
# Database クラス
# ───────────────────────────────────────────
class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def verify_user(self, username: str, password: str) -> bool:
        """
        users テーブルから pw_hash を取り出し、
        平文 password を scrypt で検証して一致すれば True を返す。
        """
        # 1. ハッシュを取得
        row = await self.fetchone(
            "SELECT pw_hash FROM users WHERE username = ?", 
            username
        )
        if not row:
            return False

        # 2. verify_password ヘルパーでチェック
        #    verify_password(password: str, hashed: str) -> bool
        return verify_password(password, row["pw_hash"])

    async def get_user_pk(self, discord_id: int) -> Optional[int]:
        """Discord ユーザID から users.id（PK）を返す"""
        row = await self.fetchone("SELECT id FROM users WHERE discord_id=?", discord_id)
        return row["id"] if row else None

    async def set_shared(self, file_id: str, shared: bool):
        """指定ファイルの共有フラグを更新"""
        val = 1 if shared else 0
        await self.execute("UPDATE files SET is_shared=? WHERE id=?", val, file_id)

    async def open(self):
        """Bot 常駐用：非コンテキストで接続を確立する"""
        if self.conn:           # すでに開いていれば何もしない
            return
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row

    async def create_shared_folder(self, folder_name: str, channel_id: int) -> int:
        """
        shared_folders テーブルに name と channel_id を同時に INSERT する。
        """
        cursor = await self.conn.execute(
            "INSERT INTO shared_folders (name, channel_id) VALUES (?, ?)",
            (folder_name, channel_id)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def set_folder_channel(self, folder_id: int, channel_id: int) -> None:
        await self.conn.execute(
            "UPDATE shared_folders SET channel_id = ? WHERE id = ?",
            (channel_id, folder_id)
        )
        await self.conn.commit()

    async def add_shared_folder_member(self, folder_id: int, discord_user_id: int) -> None:
        await self.conn.execute(
            """
            INSERT OR IGNORE INTO shared_folder_members
                (folder_id, discord_user_id)
            VALUES (?, ?)
            """,
            (folder_id, discord_user_id),
        )
        await self.conn.commit()

    async def get_shared_folder(self, folder_id: int) -> sqlite3.Row | None:
        """
        shared_folders テーブルからレコードを取得
        """
        cursor = await self.conn.execute(
            "SELECT id, name, channel_id FROM shared_folders WHERE id = ?",
            (folder_id,),
        )
        return await cursor.fetchone()

    async def delete_shared_folder(self, folder_id: int) -> None:
        """
        shared_folders と folder_members を削除
        FOREIGN KEY ... ON DELETE CASCADE が効いていれば
        shared_folder_members は自動で消えます。
        """
        await self.conn.execute(
            "DELETE FROM shared_folders WHERE id = ?",
            (folder_id,),
        )
        await self.conn.commit()  # ← ここでコミット

    async def delete_shared_folder_member(
        self,
        folder_id: int,
        discord_user_id: int
    ) -> None:
        """
        shared_folder_members テーブルから
        (folder_id, discord_user_id) のレコードを削除
        """
        await self.conn.execute(
            "DELETE FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            (folder_id, discord_user_id),
        )
        await self.conn.commit()

    async def get_shared_folder_by_channel(self, channel_id: int) -> sqlite3.Row | None:
        """
        channel_id から shared_folders レコードを取得。
        """
        cursor = await self.conn.execute(
            "SELECT id, name FROM shared_folders WHERE channel_id = ?",
            (channel_id,),
        )
        return await cursor.fetchone()

    async def add_shared_file(self, file_id: str, folder_id: int, filename: str, path: str) -> None:
        """
        shared_files テーブルにレコードを追加。
        uploaded_at は DB 側で DEFAULT CURRENT_TIMESTAMP などの仕掛けを想定。
        """
        await self.conn.execute(
            "INSERT INTO shared_files "
            "  (id, folder_id, file_name, path, size, is_shared, share_token, uploaded_at, expires_at) "
            "VALUES (?,     ?,         ?,         ?,    ?,    1,         NULL,       strftime('%s','now'), 0)",
            (file_id, folder_id, filename, path, os.path.getsize(path)),
        )
        await self.conn.commit()

    async def get_shared_file(self, file_id: str) -> Optional[aiosqlite.Row]:
        """shared_files から単一レコードを取得"""
        return await self.fetchone(
            "SELECT * FROM shared_files WHERE id = ?", file_id
        )

    async def set_shared_file_shared(self, file_id: str, shared: bool):
        """shared_files テーブルの is_shared を更新"""
        val = 1 if shared else 0
        await self.execute(
            "UPDATE shared_files SET is_shared = ?, share_token = ? WHERE id = ?",
            val,
            shared and None or None,  # share_token は HMAC で都度生成する場合は NULL、DBに保持しない
            file_id
        )

    # --- context manager ---
    async def __aenter__(self):          # type: ignore[override]
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        return self

    async def __aexit__(self, *_):       # type: ignore[override]
        await self.conn.close()

    async def commit(self):
        """明示コミット用"""
        if self.conn:
            await self.conn.commit()

    # --- generic helpers ---
    async def execute(self, sql: str, *params: Any):
        await self.conn.execute(sql, params)
        await self.conn.commit()

    async def fetchone(self, sql: str, *params: Any):
        cur = await self.conn.execute(sql, params)
        row = await cur.fetchone()
        await cur.close()
        return row

    async def fetchall(self, sql: str, *params: Any):
        cur = await self.conn.execute(sql, params)
        rows = await cur.fetchall()
        await cur.close()
        return rows

    # ========== domain-specific ==========

    # ユーザ
    async def add_user(self, discord_id: int, username: str, password: str):
        await self.execute(
            "INSERT OR REPLACE INTO users(discord_id, username, pw_hash, created_at) VALUES (?,?,?,?)",
            discord_id, username, scrypt_hash(password), dt.datetime.utcnow().isoformat()
        )

    async def user_exists(self, discord_id: int) -> bool:
        row = await self.fetchone("SELECT 1 FROM users WHERE discord_id=?", discord_id)
        return bool(row)

    # ファイル
    async def add_file(
        self,
        file_id: str,
        user_id: int,
        original_name: str,
        path: str,
        size: int,
        sha256: str,
    ):
        await self.conn.execute(
            """INSERT INTO files
            (id, user_id, original_name, path, size, sha256, uploaded_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, strftime('%s','now'), 0)""",
            (file_id, user_id, original_name, path, size, sha256),
        )
        await self.conn.commit()


    async def list_files(self, user_id: int):
        return await self.fetchall(
            "SELECT id, original_name, size, uploaded_at, is_shared, token "
            "FROM   files "
            "WHERE  user_id=? "
            "ORDER  BY uploaded_at DESC",
            user_id
        )

    async def get_file(self, file_id: str):
        return await self.fetchone("SELECT * FROM files WHERE id=?", file_id)

    async def delete_file(self, file_id: str):
        await self.execute("DELETE FROM files WHERE id=?", file_id)

# ───────────────────────────────────────────
# CLI
# ───────────────────────────────────────────
def _cli():
    import argparse, textwrap, sys
    parser = argparse.ArgumentParser(
        description="DB maintenance helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            commands:
              init-db                 初期化
              add-user USERNAME [-p PW] [--discord-id ID]
            """
        ),
    )
    parser.add_argument("cmd")
    parser.add_argument("username", nargs="?")
    parser.add_argument("-p", "--password")
    parser.add_argument("--discord-id", type=int)
    args = parser.parse_args()

    async def run():
        if args.cmd == "init-db":
            await init_db()
            print("✔ DB initialized:", DB_PATH)
        elif args.cmd == "add-user":
            pw = args.password or secrets.token_urlsafe(12)
            async with Database() as db:
                await db.add_user(args.discord_id or 0, args.username, pw)
            print("✔ user added:", args.username)
            print("  password:", pw)
        else:
            parser.print_help(); sys.exit(1)

    asyncio.run(run())

if __name__ == "__main__":
    _cli()
