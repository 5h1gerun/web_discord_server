"""aiohttp Web application core for Web_Discord_Server."""

from __future__ import annotations
import time
import asyncio
import base64
import hashlib
import hmac
import logging
import mimetypes
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
from typing import Dict, List, Optional

import discord

from aiohttp import web
import aiohttp
from aiohttp_session import new_session, setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_session
import aiohttp_jinja2
import jinja2
from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_session import get_session
from jinja2 import pass_context
from aiohttp_jinja2 import static_root_key
from aiolimiter import AsyncLimiter
import io, qrcode, pyotp      # ← 二要素用
from PIL import Image
import subprocess
from pdf2image import convert_from_path

from bot.db import init_db  # スキーマ初期化用
Database = import_module("bot.db").Database  # type: ignore

# ─────────────── Paths & Constants ───────────────
ROOT         = Path(__file__).resolve().parent.parent
DATA_DIR     = Path(os.getenv("DATA_DIR", ROOT / "data"))
STATIC_DIR   = Path(os.getenv("STATIC_DIR", ROOT / "static"))
TEMPLATE_DIR = Path(os.getenv("TEMPLATE_DIR", ROOT / "templates"))
DB_PATH      = Path(os.getenv("DB_PATH", ROOT / "data" / "web_discord_server.db"))
CHUNK_DIR    = DATA_DIR / "chunks"
PREVIEW_DIR  = DATA_DIR / "previews"

for d in (DATA_DIR, STATIC_DIR, TEMPLATE_DIR, CHUNK_DIR, PREVIEW_DIR):
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("web")

# ─────────────── Secrets ───────────────
COOKIE_SECRET_STR = os.getenv("COOKIE_SECRET", "").strip().strip('"').strip("'")
if len(COOKIE_SECRET_STR) != 44:
    raise RuntimeError("COOKIE_SECRET が未設定、または 44 文字の URL-safe Base64 ではありません")
COOKIE_SECRET = COOKIE_SECRET_STR

FILE_HMAC_SECRET = base64.urlsafe_b64decode(
    os.getenv("FILE_HMAC_SECRET", base64.urlsafe_b64encode(os.urandom(32)).decode())
)
URL_EXPIRES_SEC = int(os.getenv("UPLOAD_EXPIRES_SEC", 86400))  # default 1 day

# ─────────────── Helpers ───────────────
MOBILE_TEMPLATES = {
    "index.html": "mobile/index.html",
    "login.html": "mobile/login.html",
    "totp.html": "mobile/totp.html",
    "shared/index.html": "mobile/shared_index.html",
    "shared/folder_view.html": "mobile/folder_view.html",
}

def _is_mobile(user_agent: str) -> bool:
    if not user_agent:
        return False
    pattern = r"iPhone|Android.*Mobile|Windows Phone|iPod|BlackBerry|Opera Mini|IEMobile"
    return re.search(pattern, user_agent, re.I) is not None

def _render(req: web.Request, tpl: str, ctx: Dict[str, object]):
    ctx.setdefault("user_id", req.get("user_id"))
    ua = req.headers.get("User-Agent", "")
    if _is_mobile(ua):
        tpl = MOBILE_TEMPLATES.get(tpl, tpl)
    return aiohttp_jinja2.render_template(tpl, req, ctx)

def _sign_token(fid: str, exp: int) -> str:
    msg = f"{fid}:{exp}".encode()
    sig = hmac.new(FILE_HMAC_SECRET, msg, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(msg + b":" + sig).decode()

def _verify_token(tok: str) -> Optional[str]:
    try:
        raw = base64.urlsafe_b64decode(tok.encode())
        fid, exp_raw, sig = raw.split(b":", 2)

        # 無期限トークンは exp==0
        exp_val = int(exp_raw)
        if exp_val != 0 and exp_val < int(datetime.now(timezone.utc).timestamp()):
            return None
        valid = hmac.compare_digest(
            sig,
            hmac.new(FILE_HMAC_SECRET, f"{fid.decode()}:{exp_raw.decode()}".encode(), hashlib.sha256).digest()
        )
        return fid.decode() if valid else None
    except Exception:
        return None

async def issue_csrf(request: web.Request) -> str:
    session = await aiohttp_session.get_session(request)
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(16)
    return session["csrf_token"]

async def _send_shared_webhook(db: Database, folder_id: int, message: str) -> None:
    """指定フォルダの Webhook にメッセージを送信"""
    rec = await db.get_shared_folder(int(folder_id))
    url = rec["webhook_url"] if rec else None
    if not url:
        return
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"content": message})

async def notify_shared_upload(db: Database, folder_id: int, username: str, file_name: str) -> None:
    """共有フォルダへのアップロードをWebhookで通知"""
    message = f"\N{INBOX TRAY} {username} が `{file_name}` をアップロードしました。"
    await _send_shared_webhook(db, folder_id, message)

# ─────────────── Middleware ───────────────
@web.middleware
async def csrf_protect_mw(request: web.Request, handler):
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        session = await aiohttp_session.get_session(request)

        # ヘッダー優先。なければフォームから取得。
        token = request.headers.get("X-CSRF-Token")
        if token is None:
            form = await request.post()
            token = form.get("csrf_token")

        if token != session.get("csrf_token"):
            raise HTTPForbidden(text="Invalid CSRF token")
    return await handler(request)

@web.middleware
async def auth_mw(request: web.Request, handler):
    sess = await aiohttp_session.get_session(request)
    request["user_id"] = sess.get("user_id")
    return await handler(request)

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;"
)

@web.middleware
async def csp_mw(request: web.Request, handler):
    resp = await handler(request)
    resp.headers.setdefault("Content-Security-Policy", CSP_POLICY)
    return resp

limiter = AsyncLimiter(30, 60)  # 60 秒あたり 30 リクエスト
@web.middleware
async def rl_mw(req, handler):
    ip = req.remote
    async with limiter:
        return await handler(req)

# ─────────────── APP Factory ───────────────
def create_app(bot: Optional[discord.Client] = None) -> web.Application:
    # allow up to 50GiB
    app = web.Application(client_max_size=50 * 1024**3)

    # session setup
    storage = EncryptedCookieStorage(
    COOKIE_SECRET,
    cookie_name="wdsid",
    secure=True,           # HTTPS 限定
    httponly=True,         # JS から参照不可
    samesite="Lax",        # CSRF 低減
    max_age=60*60*24*7     # 7 日
    )
    session_setup(app, storage)

    # middlewares
    app.middlewares.append(csrf_protect_mw)
    app.middlewares.append(auth_mw)
    app.middlewares.append(rl_mw)   # DoS / ブルートフォース緩和
    app.middlewares.append(csp_mw)

    # jinja2 setup
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)))
    env = aiohttp_jinja2.get_env(app)
    if bot:
        app["bot"] = bot

    # ── バイト数を可読サイズへ変換 ──────────────────────────
    def human_size(size: int) -> str:
        """
        1023   → '1023 B'
        1536   → '1.5 KB'
        1_572_864 → '1.5 MB'
        """
        units = ("B", "KB", "MB", "GB", "TB", "PB")
        size_f = float(size)
        for unit in units:
            if size_f < 1024 or unit == units[-1]:
                # B だけは小数点不要、それ以外は 1 桁小数にする
                return f"{int(size_f)} {unit}" if unit == "B" else f"{size_f:.1f} {unit}"
            size_f /= 1024

    env.filters["human_size"] = human_size

    # ── 拡張子 → Bootstrap Icons クラス変換 ───────────────────
    ICON_MAP = {
        # 文書
        "pdf":  "bi-file-earmark-pdf",
        "doc":  "bi-file-earmark-word",  "docx": "bi-file-earmark-word",
        "xls":  "bi-file-earmark-excel", "xlsx": "bi-file-earmark-excel", "csv": "bi-file-earmark-excel",
        "ppt":  "bi-file-earmark-slides","pptx": "bi-file-earmark-slides",
        "txt":  "bi-file-earmark-text",
        # 圧縮
        "zip":  "bi-file-earmark-zip", "rar": "bi-file-earmark-zip",
        "7z":   "bi-file-earmark-zip", "gz":  "bi-file-earmark-zip",
        # ソースコード
        "py": "bi-file-earmark-code", "js": "bi-file-earmark-code",
        "html":"bi-file-earmark-code", "css":"bi-file-earmark-code",
        "java":"bi-file-earmark-code","c": "bi-file-earmark-code","cpp":"bi-file-earmark-code",
        # 音楽
        "mp3":"bi-file-earmark-music","wav":"bi-file-earmark-music","flac":"bi-file-earmark-music",
    }

    def icon_by_ext(name: str) -> str:
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        return ICON_MAP.get(ext, "bi-file-earmark")

    env.globals["icon_by_ext"] = icon_by_ext    # テンプレートから呼べるように

    async def _file_to_dict(row: Row, request: web.Request) -> dict:
        """DB Row → テンプレ用 dict

        共有期限切れの場合は自動的に非共有化する。
        """
        d = dict(row)
        token = d.get("token")

        # DBに保存されたTTL（秒）をプリセット用に渡す
        d["expiration_sec"] = d.get("expiration_sec", URL_EXPIRES_SEC)

        import time
        now_ts = int(time.time())
        exp_ts = int(d.get("expires_at", 0) or 0)
        if exp_ts != 0:
            remaining = exp_ts - now_ts
            if remaining < 0:
                d["expiration"] = 0
                d["expiration_str"] = "期限切れ"
            else:
                d["expiration"] = remaining
        else:
            d["expiration"] = 0

        # ─── 残り期限のヒューマンリーダブル文字列を追加 ───
        sec = d["expiration"]
        if "expiration_str" not in d:
            if sec == 0:
                d["expiration_str"] = "無期限"
            else:
                days = sec // 86400
                hrs  = (sec % 86400) // 3600
                mins = (sec % 3600) // 60
                parts = []
                if days: parts.append(f"{days}日")
                if hrs:  parts.append(f"{hrs}時間")
                if mins: parts.append(f"{mins}分")
                d["expiration_str"] = "".join(parts) if parts else "0分"

        # 共有URL
        if not token:
            d["share_url"] = ""
        else:
            base = "/shared/download" if d.get("folder_id") else "/f"
            d["share_url"] = f"{request.scheme}://{request.host}{base}/{token}"

        # DL用URL
        d["download_url"] = f"/download/{d['id']}"
        if not token:
            d["share_url"] = ""
        else:
            base = "/shared/download" if d.get("folder_id") else "/f"
            d["share_url"] = f"{request.scheme}://{request.host}{base}/{token}"
        # ログインユーザ専用の直接 DL URL
        d["download_url"] = f"/download/{d['id']}"
        return d

    @pass_context
    async def _csrf_token(ctx):
        return await issue_csrf(ctx["request"])
    env.globals["csrf_token"] = _csrf_token
    env.globals["get_flashed_messages"] = lambda: []
    app[static_root_key] = '/static/'

    # ─────────────── otpauth リダイレクト ───────────────
    async def otp_redirect(req: web.Request):
        import base64, urllib.parse
        token = req.match_info["token"]
        try:
            uri = base64.urlsafe_b64decode(token.encode()).decode()
        except Exception:
            raise web.HTTPBadRequest(text="invalid token")
        if not uri.startswith("otpauth://"):
            raise web.HTTPBadRequest(text="scheme not allowed")
        # 302 Found → Authenticator が起動
        raise web.HTTPFound(uri)

    app.router.add_get("/otp/{token}", otp_redirect)


    # ─────────────── File table API (PATCHED) ───────────────
    @aiohttp_jinja2.template("partials/file_table.html")
    async def file_list_api(request: web.Request):
        # 認証チェック
        discord_id = request.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")
        # リクエストから app を取得
        db = request.app["db"]
        user_id = await db.get_user_pk(discord_id)
        if not user_id:
            raise web.HTTPFound("/login")

        now_ts = int(datetime.now(timezone.utc).timestamp())
        await db.execute(
            "UPDATE files SET is_shared=0, token=NULL "
            "WHERE is_shared=1 AND expires_at!=0 AND expires_at < ?",
            now_ts,
        )
        await db.execute(
            "UPDATE shared_files SET is_shared=0, token=NULL "
            "WHERE is_shared=1 AND expires_at!=0 AND expires_at < ?",
            now_ts,
        )

        # ファイル一覧取得
        # SELECT で expiration_sec も取得する
        folder = request.query.get("folder", "")
        rows = await db.fetchall(
            "SELECT *, expiration_sec, expires_at FROM files WHERE user_id = ? AND folder = ?",
            user_id, folder
        )
        now = int(datetime.now(timezone.utc).timestamp())
        file_objs: List[Dict[str, object]] = []

        for row in rows:
            # ① 共有 URL／download_url を含む共通フィールドを生成
            f = await _file_to_dict(row, request)

            # ② ここから先は画面ごとに必要な追加フィールドを足す
            mime, _ = mimetypes.guess_type(f["original_name"])
            f["mime"]      = mime or "application/octet-stream"
            f["is_image"]  = bool(mime and mime.startswith("image/"))
            f["is_video"]  = bool(mime and mime.startswith("video/"))

            # ダウンロード用署名付き URL（ログインユーザだけが使う）
            f["url"]       = f"/download/{_sign_token(f['id'], now + URL_EXPIRES_SEC)}"
            f["user_id"]   = discord_id
            preview_file = PREVIEW_DIR / f"{f['id']}.jpg"
            if preview_file.exists():
                f["preview_url"] = f"/previews/{preview_file.name}"
            else:
                f["preview_url"] = f["url"] + "?preview=1"

            file_objs.append(f)

        # CSRF トークン発行
        token = await issue_csrf(request)
        return {
            'files':       file_objs,
            'csrf_token':  token,
            'user_id':     discord_id
        }

    @aiohttp_jinja2.template("partials/search_results.html")
    async def search_files_api(request: web.Request):
        discord_id = request.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")
        db = request.app["db"]
        user_id = await db.get_user_pk(discord_id)
        if not user_id:
            raise web.HTTPFound("/login")
        term = request.query.get("q", "").strip()
        folder = request.query.get("folder", "")
        rows = await db.search_files(user_id, term, folder) if term else []
        file_objs = [await _file_to_dict(r, request) for r in rows]
        token = await issue_csrf(request)
        return {
            "files": file_objs,
            "csrf_token": token,
            "user_id": discord_id,
            "term": term,
        }

    async def shared_index(request):
        db = request.app["db"]
        session = await get_session(request)  # ← 正しい方法でセッション取得
        user_id = session.get("user_id")

        if not user_id:
            raise web.HTTPFound("/login")

        rows = await db.fetchall("""
            SELECT sf.id, sf.name, COUNT(f.id) as file_count
            FROM shared_folders sf
            JOIN shared_folder_members m ON sf.id = m.folder_id
            LEFT JOIN shared_files f ON f.folder_id = sf.id
            WHERE m.discord_user_id = ?
            GROUP BY sf.id
        """, user_id)

        return _render(request, "shared/index.html", {
            "folders": rows
        })

    async def shared_folder_view(request: web.Request):
        # ── 1. セッション＆認証チェック ──
        sess = await aiohttp_session.get_session(request)
        discord_id = sess.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")

        # ── 2. パラメータ＆DB取得 ──
        folder_id = request.match_info["id"]
        db = request.app["db"]

        # フォルダ参加メンバー確認
        member = await db.fetchall(
            "SELECT 1 FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            folder_id, discord_id
        )
        if not member:
            raise web.HTTPForbidden(text="Not a member")

        now_ts = int(datetime.now(timezone.utc).timestamp())
        await db.execute(
            "UPDATE files SET is_shared=0, token=NULL "
            "WHERE is_shared=1 AND expires_at!=0 AND expires_at < ?",
            now_ts,
        )
        await db.execute(
            "UPDATE shared_files SET is_shared=0, token=NULL "
            "WHERE is_shared=1 AND expires_at!=0 AND expires_at < ?",
            now_ts,
        )

        # フォルダ名取得
        row = await db.fetchone("SELECT name FROM shared_folders WHERE id = ?", folder_id)
        folder_name = row["name"] if row else "(不明なフォルダ)"

        # ── 3. フォルダ内ファイル一覧取得 & 各種フィールド整形 ──
        raw_files = await db.fetchall("SELECT * FROM shared_files WHERE folder_id = ?", folder_id)
        now_ts = int(datetime.now(timezone.utc).timestamp())

        file_objs: list[dict] = []
        for rec in raw_files:
            f = await _file_to_dict(rec, request)
            # ── プレビュー／ダウンロード URL を整備 ──
            if f["is_shared"]:
                # 1) DBに保存されたトークンを使う
                token = f["token"]
                if not token:
                    exp = now_ts + f["expiration_sec"]
                    token = _sign_token(f["id"], exp)
                    await db.execute(
                        "UPDATE shared_files SET token=?, expiration_sec=?, expires_at=? WHERE id=?",
                        token, f["expiration_sec"], exp, f["id"]
                    )
                    await db.commit()
                    f["token"] = token
                # 2) 共有用URL
                # プレビュー用は inline 表示させるため preview=1
                f["preview_url"]  = f"/shared/download/{token}?preview=1"
                f["download_url"] = f"/shared/download/{token}?dl=1"
                preview_fallback = f["preview_url"]
            else:
                private_token = _sign_token(f["id"], now_ts + URL_EXPIRES_SEC)
                f["download_url"] = f"/download/{private_token}"
                preview_fallback = f"/download/{private_token}?preview=1"

            preview_file = PREVIEW_DIR / f"{f['id']}.jpg"
            if preview_file.exists():
                f["preview_url"] = f"/previews/{preview_file.name}"
            else:
                f["preview_url"] = preview_fallback

            # 2) ファイル名表示用
            f["original_name"] = f.get("file_name", "")  # partial では {{ f.original_name }} を使うため

            # 3) DBから取り込まれた size カラムをそのまま利用
            f["size"] = rec["size"]

            # 4) プレビュー用フラグ (画像・動画)
            import mimetypes
            mime, _ = mimetypes.guess_type(f["original_name"])
            f["mime"]      = mime or "application/octet-stream"
            f["is_image"]  = bool(mime and mime.startswith("image/"))
            f["is_video"]  = bool(mime and mime.startswith("video/"))

            # 5) 共有トグル＆リンク用：実 DB 上のフラグ & 必要に応じてトークン生成
            f["user_id"]   = discord_id
            f["is_shared"] = bool(int(rec["is_shared"]))
            if f["is_shared"]:
                # token がまだ無ければ生成して DB に格納
                if not rec["token"]:
                    exp_val = now_ts + URL_EXPIRES_SEC
                    new_token = _sign_token(f["id"], exp_val)
                    await db.execute(
                        "UPDATE shared_files SET token=?, expires_at=? WHERE id=?",
                        new_token, exp_val, f["id"]
                    )
                    await db.commit()
                    f["token"] = new_token
                # token に基づき share_url を必ず再計算
                f["share_url"] = (
                    f"{request.scheme}://{request.host}/shared/download/{f['token']}"
                )

            file_objs.append(f)

        # ── 4. 他の共有フォルダ一覧 (ファイル数付き) ──
        shared_folders = await db.fetchall("""
            SELECT sf.id,
                   sf.name,
                   COUNT(f.id) AS file_count
            FROM shared_folders sf
            JOIN shared_folder_members m ON sf.id = m.folder_id
            LEFT JOIN shared_files f ON f.folder_id = sf.id
            WHERE m.discord_user_id = ?
            GROUP BY sf.id
        """, discord_id)
        session = await get_session(request)
        current_user_id = session.get("user_id")
        base_url = f"{request.scheme}://{request.host}"
        all_folders = await db.fetchall(
            """
            SELECT sf.id, sf.name
            FROM shared_folders       sf
            JOIN shared_folder_members m ON m.folder_id = sf.id
            WHERE m.discord_user_id = ?
            ORDER BY sf.name
            """,
            discord_id
        )
        # ── 5. コンテキスト返却 ──
        return _render(request, "shared/folder_view.html", {
            "folder_id":      folder_id,
            "user_id":        current_user_id,
            "request":        request,
            "base_url":       base_url,
            "folder_name":    folder_name,
            "files":          file_objs,
            "shared_folders": shared_folders,
            "all_folders":    all_folders,
            "csrf_token":     await issue_csrf(request),
            "static_version": int(time.time()),
        })

    # database
    db = Database(DB_PATH)
    app["db"] = db
    async def on_startup(app: web.Application):
        await init_db(DB_PATH)
        await db.open()
    app.on_startup.append(on_startup)

    # static files
    if STATIC_DIR.exists():
        app.router.add_static("/static/", str(STATIC_DIR), name="static")
    if PREVIEW_DIR.exists():
        app.router.add_static("/previews/", str(PREVIEW_DIR), name="previews")

    # handlers
    async def health(req):
        return web.json_response({"status": "ok"})

    async def login_get(req):
        token = await issue_csrf(req)
        return _render(req, "login.html", {"csrf_token": token, "request": req})

    async def login_post(req):
        data = await req.post()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        db      = app["db"]

        if not await db.verify_user(username, password):
            return _render(req, "login.html", {"error": "Invalid", "csrf_token": await issue_csrf(req), "request": req})

        row = await db.fetchone(
            "SELECT discord_id, totp_enabled FROM users WHERE username = ?", username)

        if not row:
            return _render(req, "login.html", {"error": "No user found", "csrf_token": await issue_csrf(req), "request": req})

        sess = await new_session(req)

        if row["totp_enabled"]:
            sess["tmp_user_id"] = row["discord_id"]
            raise web.HTTPFound("/totp")

        sess["user_id"] = row["discord_id"]
        raise web.HTTPFound("/")

    # ── GET: フォーム表示 ──────────────────────
    async def totp_get(req):
        sess = await get_session(req)
        if "tmp_user_id" not in sess:     # 直アクセス対策
            raise web.HTTPFound("/login")
        # CSRF トークンをテンプレに渡す
        return _render(req, "totp.html",
                        {"csrf_token": await issue_csrf(req)})

    # ── POST: 検証 ────────────────────────────
    async def totp_post(req):
        sess = await get_session(req)
        if "tmp_user_id" not in sess:
            raise web.HTTPFound("/login")

        code     = (await req.post()).get("code", "")
        user_id  = sess["tmp_user_id"]
        row      = await db.fetchone("SELECT totp_secret FROM users WHERE discord_id=?", user_id)

        if row and pyotp.TOTP(row["totp_secret"]).verify(code):
            sess["user_id"] = user_id
            del sess["tmp_user_id"]
            raise web.HTTPFound("/")

        return _render(req, "totp.html",
                    {"error": "コードが違います", "csrf_token": await issue_csrf(req)})

    async def logout(req):
        session = await aiohttp_session.get_session(req)
        session.invalidate()
        raise web.HTTPFound("/login")

    async def index(req):
        discord_id = req.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")
        user_id = await app["db"].get_user_pk(discord_id)
        if not user_id:
            raise web.HTTPFound("/login")

        now_ts = int(datetime.now(timezone.utc).timestamp())
        await app["db"].execute(
            "UPDATE files SET is_shared=0, token=NULL "
            "WHERE is_shared=1 AND expires_at!=0 AND expires_at < ?",
            now_ts,
        )
        await app["db"].execute(
            "UPDATE shared_files SET is_shared=0, token=NULL "
            "WHERE is_shared=1 AND expires_at!=0 AND expires_at < ?",
            now_ts,
        )

        user_row = await app["db"].fetchone("SELECT username FROM users WHERE discord_id = ?", discord_id)
        username = user_row["username"] if user_row else "Unknown"
        # expiration_sec を含めて取得するように
        folder = req.query.get("folder", "")
        rows   = await app["db"].fetchall(
            "SELECT *, expiration_sec, expires_at FROM files WHERE user_id = ? AND folder = ?",
            user_id, folder
        )
        parent_id = int(folder) if folder else None
        subfolders = await app["db"].list_user_folders(user_id, parent_id)
        breadcrumbs = []
        cur = parent_id
        while cur:
            rec = await app["db"].get_user_folder(cur)
            if not rec:
                break
            breadcrumbs.insert(0, {"id": cur, "name": rec["name"]})
            cur = rec["parent_id"]
        now_ts = int(datetime.now(timezone.utc).timestamp())
        files  = []

        for r in rows:                           # ← １回だけ回す
            f = await _file_to_dict(r, req)            # share_url / download_url を付与
            f["user_id"]   = discord_id
            f["url"]       = f"/download/{_sign_token(f['id'], now_ts + URL_EXPIRES_SEC)}"

            mime, _        = mimetypes.guess_type(f["original_name"])
            f["mime"]      = mime or "application/octet-stream"
            f["is_image"]  = bool(mime and mime.startswith("image/"))
            f["is_video"]  = bool(mime and mime.startswith("video/"))

            preview_file = PREVIEW_DIR / f"{f['id']}.jpg"
            if preview_file.exists():
                f["preview_url"] = f"/previews/{preview_file.name}"
            else:
                f["preview_url"] = f["url"] + "?preview=1"

            # is_shared フラグは DB のまま
            f["is_shared"] = bool(r["is_shared"])
            if f["is_shared"]:
                f["token"] = _sign_token(f["id"], now_ts + URL_EXPIRES_SEC)

            files.append(f)

        token = await issue_csrf(req)
        return _render(req, "index.html", {
            "files": files,
            "csrf_token": token,
            "username": username,
            "folder_id": folder,
            "subfolders": subfolders,
            "breadcrumbs": breadcrumbs,
            "static_version": int(time.time()),
            "request": req
        })

    async def mobile_index(req):
        """スマホ向けのシンプルな一覧ページ"""
        discord_id = req.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")
        user_id = await app["db"].get_user_pk(discord_id)
        if not user_id:
            raise web.HTTPFound("/login")

        now_ts = int(datetime.now(timezone.utc).timestamp())
        await app["db"].execute(
            "UPDATE files SET is_shared=0, token=NULL "
            "WHERE is_shared=1 AND expires_at!=0 AND expires_at < ?",
            now_ts,
        )
        await app["db"].execute(
            "UPDATE shared_files SET is_shared=0, token=NULL "
            "WHERE is_shared=1 AND expires_at!=0 AND expires_at < ?",
            now_ts,
        )

        user_row = await app["db"].fetchone("SELECT username FROM users WHERE discord_id = ?", discord_id)
        username = user_row["username"] if user_row else "Unknown"
        folder = req.query.get("folder", "")
        rows = await app["db"].fetchall(
            "SELECT *, expiration_sec, expires_at FROM files WHERE user_id = ? AND folder = ?",
            user_id, folder,
        )
        now_ts = int(datetime.now(timezone.utc).timestamp())
        files = []
        for r in rows:
            f = await _file_to_dict(r, req)
            f["user_id"] = discord_id
            f["url"] = f"/download/{_sign_token(f['id'], now_ts + URL_EXPIRES_SEC)}"

            mime, _ = mimetypes.guess_type(f["original_name"])
            f["mime"] = mime or "application/octet-stream"
            f["is_image"] = bool(mime and mime.startswith("image/"))
            f["is_video"] = bool(mime and mime.startswith("video/"))

            preview_file = PREVIEW_DIR / f"{f['id']}.jpg"
            if preview_file.exists():
                f["preview_url"] = f"/previews/{preview_file.name}"
            else:
                f["preview_url"] = f["url"] + "?preview=1"

            f["is_shared"] = bool(r["is_shared"])
            if f["is_shared"]:
                f["token"] = _sign_token(f["id"], now_ts + URL_EXPIRES_SEC)

            files.append(f)

        token = await issue_csrf(req)
        return _render(req, "mobile/index.html", {
            "files": files,
            "csrf_token": token,
            "username": username,
            "static_version": int(time.time()),
            "request": req
        })

    async def upload(req):
        discord_id = req.get("user_id")
        if not discord_id:
            raise web.HTTPForbidden()
        user_id = await app["db"].get_user_pk(discord_id)
        if not user_id:
            raise web.HTTPForbidden()

        data = await req.post()
        # 複数の "file" フィールドをすべて取得
        filefields = data.getall("file")
        if not filefields:
            return web.json_response({"success": False, "error": "no file"}, status=400)

        # 受け取った各ファイルごとに保存＆DB 登録
        for filefield in filefields:
            fid = str(uuid.uuid4())
            path = DATA_DIR / fid
            size = 0
            # 実ファイル書き込み
            with path.open("wb") as f:
                while True:
                    chunk = filefield.file.read(8192)
                    if not chunk:
                        break
                    size += len(chunk)
                    f.write(chunk)
            # ハッシュ計算
            sha256sum = hashlib.sha256(path.read_bytes()).hexdigest()
            # プレビュー生成
            mime, _ = mimetypes.guess_type(filefield.filename)
            preview_path = PREVIEW_DIR / f"{fid}.jpg"
            try:
                if mime and mime.startswith("image"):
                    img = Image.open(path)
                    img.thumbnail((320, 320))
                    img.convert("RGB").save(preview_path, "JPEG")
                elif mime and mime.startswith("video"):
                    subprocess.run([
                        "ffmpeg", "-y", "-i", str(path), "-ss", "00:00:01",
                        "-vframes", "1", str(preview_path)
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif mime == "application/pdf":
                    pages = convert_from_path(str(path), first_page=1, last_page=1)
                    if pages:
                        img = pages[0]
                        img.thumbnail((320, 320))
                        img.save(preview_path, "JPEG")
                elif mime and mime.startswith("application/vnd"):
                    tmp_pdf = path.with_suffix(".pdf")
                    subprocess.run([
                        "libreoffice", "--headless", "--convert-to", "pdf", str(path), "--outdir", str(path.parent)
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if tmp_pdf.exists():
                        pages = convert_from_path(str(tmp_pdf), first_page=1, last_page=1)
                        if pages:
                            img = pages[0]
                            img.thumbnail((320, 320))
                            img.save(preview_path, "JPEG")
                        tmp_pdf.unlink(missing_ok=True)
                else:
                    preview_path = None
            except Exception as e:
                log.warning("preview generation failed: %s", e)
                if preview_path and preview_path.exists():
                    preview_path.unlink(missing_ok=True)
            # 自動タグ生成
            from bot.auto_tag import generate_tags
            tags = generate_tags(path)
            # DB 登録
            folder = data.get("folder") or data.get("folder_id", "")
            await app["db"].add_file(
                fid,
                user_id,
                folder,
                filefield.filename,
                str(path),
                size,
                sha256sum,
                tags,
            )
        # すべてのファイルを正常受信できた
        return web.json_response({"success": True})

    async def toggle_shared(request: web.Request):
        discord_id = request.get("user_id")
        if not discord_id:
            return web.json_response({"error": "unauthorized"}, status=403)

        user_id = await request.app["db"].get_user_pk(discord_id)
        if not user_id:
            return web.json_response({"error": "invalid user"}, status=403)

        file_id = request.match_info["id"]
        rec = await request.app["db"].get_file(file_id)
        # rec は sqlite3.Row なので、そのまま dict() にしてあげる
        if not rec or dict(rec)["user_id"] != user_id:
            return web.json_response({"error": "forbidden"}, status=403)

        rec_dict = dict(rec)

        # ─── JSONボディから expiration（秒）を先に一度だけ取得 ───
        try:
            data    = await request.json()
            exp_sec = int(data.get("expiration", URL_EXPIRES_SEC))
        except:
            exp_sec = URL_EXPIRES_SEC

        new_state = not bool(rec_dict["is_shared"])
        token     = None
        if new_state:                              # 共有 ON
            now_ts = int(time.time())
            exp    = 0 if exp_sec <= 0 else now_ts + exp_sec
            token = _sign_token(file_id, exp)
            if isinstance(token, bytes):
                token = token.decode()
            # トークンとともに expiration_sec も保存
            await request.app["db"].execute(
                "UPDATE files SET is_shared=1, token=?, expiration_sec=?, expires_at=? WHERE id=?",
                token, exp_sec, exp, file_id
            )
        else:                                      # 共有 OFF
            # 非共有に戻すときはデフォルトに
            await request.app["db"].execute(
                "UPDATE files SET is_shared=0, token=NULL, expiration_sec=?, expires_at=0 WHERE id=?",
                URL_EXPIRES_SEC, file_id
            )
        await request.app["db"].commit()
    
        payload = {"status": "ok", "is_shared": new_state, "expiration": exp_sec}
        if token:
            payload |= {
                "token":     token,
                "share_url": f"{request.scheme}://{request.host}/f/{token}",
            }
        return web.json_response(payload)

    async def download(req):
        fid = _verify_token(req.match_info["token"])
        if not fid:
            raise web.HTTPForbidden()

        db = app["db"]
        rec = await db.get_file(fid)
        filename_key = "original_name"

        if not rec:
            # check shared_files for private preview/download
            rec = await db.fetchone(
                "SELECT * FROM shared_files WHERE id = ?",
                fid,
            )
            filename_key = "file_name"
            if rec:
                # validate membership
                discord_id = req.get("user_id")
                if not discord_id:
                    raise web.HTTPForbidden()
                member = await db.fetchone(
                    "SELECT 1 FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
                    rec["folder_id"], discord_id,
                )
                if not member:
                    raise web.HTTPForbidden()

        if not rec:
            raise web.HTTPNotFound()

        path = Path(rec["path"])
        mime, _ = mimetypes.guess_type(rec[filename_key])
        headers = {
            "Content-Type": mime or "application/octet-stream",
            "Content-Disposition": f'attachment; filename="{rec[filename_key]}"'
        }
        return web.FileResponse(path, headers=headers)

    async def upload_chunked(req: web.Request):
        upload_id = req.headers.get("X-Upload-Id")
        idx = int(req.headers.get("X-Chunk-Index", 0))
        is_last = req.headers.get("X-Last-Chunk") == "1"
        if not upload_id:
            return web.HTTPBadRequest(text="Missing X-Upload-Id")
        reader = await req.multipart()
        field = await reader.next()
        if not field or field.name != "file":
            return web.HTTPBadRequest(text="Missing file field")
        chunk = await field.read(decode=False)
        tmp_dir = CHUNK_DIR / upload_id
        tmp_dir.mkdir(parents=True, exist_ok=True)
        part_path = tmp_dir / f"{idx:06}.part"
        part_path.write_bytes(chunk)
        if is_last:
            target_id = str(uuid.uuid4())
            target_path = DATA_DIR / target_id
            with target_path.open("wb") as out:
                for part_file in sorted(tmp_dir.iterdir()):
                    out.write(part_file.read_bytes())
            for part_file in tmp_dir.iterdir():
                part_file.unlink()
            tmp_dir.rmdir()
            discord_id = req.get("user_id")
            if not discord_id:
                raise web.HTTPForbidden()
            user_id = await req.app["db"].get_user_pk(discord_id)
            if not user_id:
                raise web.HTTPForbidden()

            mime, _ = mimetypes.guess_type(field.filename)
            preview_path = PREVIEW_DIR / f"{target_id}.jpg"
            try:
                if mime and mime.startswith("image"):
                    img = Image.open(target_path)
                    img.thumbnail((320, 320))
                    img.convert("RGB").save(preview_path, "JPEG")
                elif mime and mime.startswith("video"):
                    subprocess.run([
                        "ffmpeg", "-y", "-i", str(target_path), "-ss", "00:00:01",
                        "-vframes", "1", str(preview_path)
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif mime == "application/pdf":
                    pages = convert_from_path(str(target_path), first_page=1, last_page=1)
                    if pages:
                        img = pages[0]
                        img.thumbnail((320, 320))
                        img.save(preview_path, "JPEG")
                elif mime and mime.startswith("application/vnd"):
                    tmp_pdf = target_path.with_suffix(".pdf")
                    subprocess.run([
                        "libreoffice", "--headless", "--convert-to", "pdf", str(target_path), "--outdir", str(target_path.parent)
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if tmp_pdf.exists():
                        pages = convert_from_path(str(tmp_pdf), first_page=1, last_page=1)
                        if pages:
                            img = pages[0]
                            img.thumbnail((320, 320))
                            img.save(preview_path, "JPEG")
                        tmp_pdf.unlink(missing_ok=True)
                else:
                    preview_path = None
            except Exception as e:
                log.warning("preview generation failed: %s", e)
                if preview_path and preview_path.exists():
                    preview_path.unlink(missing_ok=True)

            from bot.auto_tag import generate_tags
            tags = generate_tags(target_path)
            folder = req.headers.get("X-Upload-Folder") or req.headers.get("X-Upload-FolderId", "")
            await req.app["db"].add_file(
                target_id, user_id, folder, field.filename,
                str(target_path), target_path.stat().st_size,
                hashlib.sha256(target_path.read_bytes()).hexdigest(),
                tags,
            )
            return web.json_response({"status": "completed", "file_id": target_id})
        return web.json_response({"status": "ok", "chunk": idx})

    async def delete_file(req: web.Request):
        discord_id = req.get("user_id")
        if not discord_id:
            raise web.HTTPForbidden()
        user_id = await req.app["db"].get_user_pk(discord_id)
        if not user_id:
            raise web.HTTPForbidden()

        file_id = req.match_info["id"]
        rec = await req.app["db"].get_file(file_id)
        if not rec or rec["user_id"] != user_id:
            raise web.HTTPForbidden()

        # 実ファイル削除
        try:
            Path(rec["path"]).unlink(missing_ok=True)
        except Exception as e:
            log.warning("Failed to delete file: %s", e)

        # DB削除
        await req.app["db"].delete_file(file_id)

        raise web.HTTPFound("/")

    async def delete_all(req: web.Request):
        discord_id = req.get("user_id")
        if not discord_id:
            raise web.HTTPForbidden()
        user_id = await req.app["db"].get_user_pk(discord_id)
        if not user_id:
            raise web.HTTPForbidden()
        rows = await req.app["db"].fetchall(
            "SELECT path FROM files WHERE user_id=?",
            user_id
        )
        for r in rows:
            try:
                Path(r["path"]).unlink(missing_ok=True)
            except Exception as e:
                log.warning("Failed to delete file: %s", e)
        await req.app["db"].delete_all_files(user_id)
        raise web.HTTPFound("/")

    async def update_tags(req: web.Request):
        discord_id = req.get("user_id")
        if not discord_id:
            return web.json_response({"error": "unauthorized"}, status=403)
        user_id = await req.app["db"].get_user_pk(discord_id)
        if not user_id:
            return web.json_response({"error": "unauthorized"}, status=403)
        file_id = req.match_info["id"]
        rec = await req.app["db"].get_file(file_id)
        if not rec or rec["user_id"] != user_id:
            return web.json_response({"error": "forbidden"}, status=403)
        data = await req.post()
        tags = data.get("tags", "")
        await req.app["db"].update_tags(file_id, tags)
        return web.json_response({"status": "ok", "tags": tags})

    async def send_file_dm(req: web.Request):
        sess = await get_session(req)
        discord_id = sess.get("user_id")
        if not discord_id:
            return web.json_response({"error": "unauthorized"}, status=403)

        data = await req.json()
        file_id = data.get("file_id")
        target  = int(data.get("user_id", 0))
        if not file_id or not target:
            return web.json_response({"error": "bad_request"}, status=400)

        db = req.app["db"]
        user_pk = await db.get_user_pk(discord_id)
        rec = await db.get_file(str(file_id))
        if not rec or rec["user_id"] != user_pk:
            return web.json_response({"error": "not_found"}, status=404)

        bot = req.app.get("bot")
        if not bot:
            return web.json_response({"error": "bot_unavailable"}, status=500)

        try:
            user = bot.get_user(target) or await bot.fetch_user(target)
        except Exception:
            user = None
        if not user:
            return web.json_response({"error": "user_not_found"}, status=404)

        path = Path(rec["path"])
        size = rec["size"]
        sender_row = await db.fetchone("SELECT username FROM users WHERE discord_id = ?", discord_id)
        sender_name = sender_row["username"] if sender_row else str(discord_id)
        try:
            if size <= (25 << 20):
                await user.send(
                    content=f"📨 {sender_name} からのファイルです",
                    file=discord.File(path, filename=rec["original_name"])
                )
            else:
                now = int(datetime.now(timezone.utc).timestamp())
                tok = _sign_token(file_id, now + URL_EXPIRES_SEC)
                url = f"https://{os.getenv('PUBLIC_DOMAIN','localhost:9040')}/download/{tok}"
                await user.send(f"📨 {sender_name} からのファイルです\n🔗 ダウンロードリンク: {url}")
            return web.json_response({"status": "ok"})
        except discord.Forbidden:
            return web.json_response({"error": "forbidden"}, status=403)

    async def user_list(req: web.Request):
        rows = await req.app["db"].list_users()
        # Return user IDs as strings to avoid precision loss in JavaScript
        return web.json_response([
            {"id": str(r["discord_id"]), "name": r["username"]} for r in rows
        ])

    async def shared_update_tags(req: web.Request):
        sess = await get_session(req)
        discord_id = sess.get("user_id")
        if not discord_id:
            return web.json_response({"error": "unauthorized"}, status=403)
        file_id = req.match_info["id"]
        db = req.app["db"]
        sf = await db.fetchone("SELECT folder_id FROM shared_files WHERE id = ?", file_id)
        if not sf:
            return web.json_response({"error": "not_found"}, status=404)
        member = await db.fetchone(
            "SELECT 1 FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            sf["folder_id"], discord_id,
        )
        if member is None:
            return web.json_response({"error": "forbidden"}, status=403)
        data = await req.post()
        tags = data.get("tags", "")
        await db.update_shared_tags(file_id, tags)
        return web.json_response({"status": "ok", "tags": tags})

    async def shared_upload(req: web.Request):
        sess = await get_session(req)
        discord_id = sess.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")

        data = await req.post()
        filefield = data.get("file")
        folder_id = data.get("folder_id")
        if not filefield or not folder_id:
            raise web.HTTPBadRequest()

        db = req.app["db"]
        rows = await db.fetchall(
            "SELECT * FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            folder_id, discord_id
        )
        if not rows:
            raise web.HTTPForbidden(text="Not a member")

        fid = os.urandom(8).hex()
        path = DATA_DIR / fid
        with path.open("wb") as f:
            while True:
                chunk = filefield.file.read(8192)
                if not chunk:
                    break
                f.write(chunk)

        from bot.auto_tag import generate_tags
        tags = generate_tags(path)
        await db.add_shared_file(fid, folder_id, filefield.filename, str(path), tags)
        # アップロード時は自動的に共有しないようフラグをクリア
        await db.execute(
            "UPDATE shared_files SET is_shared=0, token=NULL WHERE id = ?",
            fid
        )
        await db.commit()
        user_row = await db.fetchone("SELECT username FROM users WHERE discord_id = ?", discord_id)
        username = user_row["username"] if user_row else str(discord_id)
        await notify_shared_upload(db, int(folder_id), username, filefield.filename)
        raise web.HTTPFound(f"/shared/{folder_id}")

    async def shared_download(req: web.Request):
        token = req.match_info["token"]
        fid   = _verify_token(token)
        if not fid:
            raise web.HTTPForbidden()

        # ② 共有フォルダファイル期限チェック（期限切れなら非共有化して404）
        import time, base64
        raw = base64.urlsafe_b64decode(token.encode())
        _, exp_raw, _ = raw.split(b":", 2)
        exp_ts = int(exp_raw)
        if exp_ts != 0 and time.time() > exp_ts:
            await req.app["db"].execute(
                "UPDATE shared_files SET is_shared=0, token=NULL, expires_at=0 WHERE id=?",
                fid
            )
            await req.app["db"].commit()
            raise web.HTTPNotFound()

        db  = req.app["db"]
        rec = await db.fetchone(
            "SELECT * FROM shared_files WHERE id = ? AND token = ? AND is_shared = 1",
            fid, token
        )
        if not rec:
            raise web.HTTPNotFound()

        mime, _ = mimetypes.guess_type(rec["file_name"])
        # ① プレビュー表示用 (preview=1)
        if req.query.get("preview") == "1":
            return web.FileResponse(
                rec["path"],
                headers={
                    "Content-Type": mime or "application/octet-stream"
                }
            )

        # ② ダウンロード要求 (dl=1)
        if req.query.get("dl") == "1":
            return web.FileResponse(
                rec["path"],
                headers={
                    "Content-Type": mime or "application/octet-stream",
                    "Content-Disposition":
                        f'attachment; filename="{rec["file_name"]}"'
                }
            )

        # Row → dict へ変換してテンプレートへ
        file_dict = dict(rec)
        file_dict["original_name"] = file_dict.get("file_name", "")   # ← 追加
        preview_file = PREVIEW_DIR / f"{file_dict['id']}.jpg"
        if preview_file.exists():
            file_dict["preview_url"] = f"/previews/{preview_file.name}"
        else:
            file_dict["preview_url"] = f"{req.path}?preview=1"

        return _render(req, "public/confirm_download.html", {
            "file":    file_dict,
            "request": req
        })
    async def shared_delete(req: web.Request):
        sess = await get_session(req)
        discord_id = sess.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")

        file_id = req.match_info["file_id"]
        db = req.app["db"]
        rec = await db.fetchone("SELECT folder_id, path, file_name FROM shared_files WHERE id = ?", file_id)
        if not rec:
            raise web.HTTPNotFound()

        # メンバーかどうか確認
        rows = await db.fetchall(
            "SELECT * FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            rec["folder_id"], discord_id
        )
        if not rows:
            raise web.HTTPForbidden()

        # ファイル削除
        try:
            Path(rec["path"]).unlink(missing_ok=True)
        except Exception:
            pass
        await db.execute("DELETE FROM shared_files WHERE id = ?", file_id)
        await db.commit()

        user_row = await db.fetchone("SELECT username FROM users WHERE discord_id = ?", discord_id)
        username = user_row["username"] if user_row else str(discord_id)
        await _send_shared_webhook(db, rec["folder_id"], f"\N{WASTEBASKET} {username} が `{rec['file_name']}` を削除しました。")

        raise web.HTTPFound(f"/shared/{rec['folder_id']}")

    async def shared_delete_all(req: web.Request):
        sess = await get_session(req)
        discord_id = sess.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")

        folder_id = req.match_info.get("folder_id")
        db = req.app["db"]
        member = await db.fetchone(
            "SELECT 1 FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            folder_id, discord_id,
        )
        if member is None:
            raise web.HTTPForbidden()

        await db.delete_all_shared_files(int(folder_id))
        raise web.HTTPFound(f"/shared/{folder_id}")


    async def download_zip(req: web.Request):
        sess = await get_session(req)
        discord_id = sess.get("user_id")
        if not discord_id:
            raise web.HTTPFound("/login")

        folder_id = req.match_info.get("folder_id")
        db = req.app["db"]
        member = await db.fetchone(
            "SELECT 1 FROM shared_folder_members WHERE folder_id = ? AND discord_user_id = ?",
            folder_id, discord_id,
        )
        if member is None:
            raise web.HTTPForbidden()

        rows = await db.fetchall("SELECT file_name, path FROM shared_files WHERE folder_id=?", folder_id)

        def _create_zip(rows, folder_id):
            import tempfile, zipfile
            tmp_dir = tempfile.mkdtemp()
            zip_path = Path(tmp_dir) / f"folder_{folder_id}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                for r in rows:
                    try:
                        zf.write(r["path"], arcname=r["file_name"])
                    except FileNotFoundError:
                        pass
            return zip_path, tmp_dir

        zip_path, tmp_dir = await asyncio.to_thread(_create_zip, rows, folder_id)

        async def _cleanup():
            await asyncio.sleep(60)
            try:
                zip_path.unlink(missing_ok=True)
                Path(tmp_dir).rmdir()
            except Exception:
                pass

        asyncio.create_task(_cleanup())
        return web.FileResponse(zip_path, headers={
            "Content-Disposition": f'attachment; filename="folder_{folder_id}.zip"'
        })

    # ─────────────── Shared ファイルの共有トグル API ───────────────
    async def shared_toggle(request: web.Request):
        sess = await aiohttp_session.get_session(request)
        discord_id = sess.get("user_id")
        if not discord_id:
            return web.json_response({"error": "unauthorized"}, status=403)

        file_id = request.match_info["id"]
        token = None
        # ─── JSON ボディから expiration（秒）を取得 ───
        # OFF 時にも参照されるので冒頭で定義しておく
        try:
            data    = await request.json()
            exp_sec = int(data.get("expiration", URL_EXPIRES_SEC))
        except:
            exp_sec = URL_EXPIRES_SEC

        # DB メソッド呼び出し
        # トークンと is_shared フラグを同時に検証するよう変更
        # 対象レコードを取得（shared_files テーブルに対して id だけで取得）
        db  = request.app["db"]
        rec = await db.fetchone(
            "SELECT * FROM shared_files WHERE id = ?",
            file_id
        )
        # 共有解除後や不正トークンの場合は 404 とする
        if not rec:
            return web.json_response({"error": "not_found"}, status=404)

        db = request.app["db"]
        # トークン ON/OFF 切り替え
        # ─── トグル後の状態を判定 ───
        new_state = not bool(rec["is_shared"])
        if new_state:
            now_ts = int(time.time())
            # 有効期限タイムスタンプを計算
            exp = 0 if exp_sec <= 0 else now_ts + exp_sec
            token = _sign_token(file_id, exp)
            if isinstance(token, bytes):
                token = token.decode()
            # 共有フォルダ内も同様に、expiration_sec を永続化
            await request.app["db"].execute(
                "UPDATE shared_files SET is_shared=1, token=?, expiration_sec=?, expires_at=? WHERE id=?",
                token, exp_sec, exp, file_id
            )
        else:
            # 非共有に戻すときは既定に戻す
            await request.app["db"].execute(
                "UPDATE shared_files SET is_shared=0, token=NULL, expiration_sec=?, expires_at=0 WHERE id=?",
                URL_EXPIRES_SEC, file_id
            )
        await db.commit()

        user_row = await db.fetchone("SELECT username FROM users WHERE discord_id = ?", discord_id)
        username = user_row["username"] if user_row else str(discord_id)
        action = "共有しました" if new_state else "共有を解除しました"
        await _send_shared_webhook(db, rec["folder_id"], f"\N{LINK SYMBOL} {username} が `{rec['file_name']}` を{action}。")

        payload = {"status": "ok", "is_shared": new_state, "expiration": exp_sec}
        if token:
            # 共有フォルダ用リンクは /shared/download/<token>
            payload |= {
                "token":     token,
                "share_url": f"{request.scheme}://{request.host}/shared/download/{token}",
            }
        return web.json_response(payload)

    # ──────────────── リネームハンドラ (改訂版) ────────────────
    async def rename_file(request: web.Request):
        """
        POST /rename/{id}
        Body: { "name": "<拡張子を除いた新しいファイル名>" }
        - 物理ファイル( uuid名 )は触らない
        - files.original_name だけを書き換える
        """
        discord_id = request.get("user_id")
        if not discord_id:
            return web.json_response({"error": "unauthorized"}, status=403)

        db       = request.app["db"]
        file_id  = request.match_info.get("id")
        if not file_id:
            return web.json_response({"error": "bad_id"}, status=400)

        user_pk  = await db.get_user_pk(discord_id)
        rec      = await db.get_file(file_id)
        if not rec or rec["user_id"] != user_pk:
            return web.json_response({"error": "forbidden"}, status=403)

        # 新しいファイル名（拡張子維持）
        payload  = await request.json()
        new_base = payload.get("name", "").strip()
        if not new_base:
            return web.json_response({"error": "empty"}, status=400)
        if any(ch in new_base for ch in r'\/:*?"<>|') or len(new_base.encode()) > 255:
            return web.json_response({"error": "invalid_name"}, status=422)

        import os
        _, ext   = os.path.splitext(rec["original_name"])
        new_name = f"{new_base}{ext}"

        # 物理ファイルは触らず、DB だけ更新
        await db.execute(
            "UPDATE files SET original_name = ? WHERE id = ?",
            new_name, file_id
        )
        await db.commit()

        return web.json_response({"status": "ok", "new_name": new_name})

    async def rename_shared_file(request: web.Request):
        """
        共有フォルダ内ファイルの表示名（shared_files.file_name）を変更する。
        POST /shared/rename_file/{file_id}
        Body: { "name": "<拡張子を除いた新しいファイル名>" }
        """
        # ── 0. 認証 ───────────────────────────────
        sess = await aiohttp_session.get_session(request)
        discord_id = sess.get("user_id")
        if not discord_id:
            return web.json_response({"error": "unauthorized"}, status=403)

        file_id = request.match_info.get("file_id")          # ルート {file_id}
        if not file_id:
            return web.json_response({"error": "bad_id"}, status=400)

        db = request.app["db"]

        # ── 1. shared_files レコードを取得 ─────────
        sf = await db.fetchone("SELECT * FROM shared_files WHERE id = ?", file_id)
        if not sf:
            return web.json_response({"error": "not_found"}, status=404)

        # ── 2. フォルダのメンバーか確認 ───────────
        member_row = await db.fetchone(
            "SELECT 1 FROM shared_folder_members "
            "WHERE folder_id = ? AND discord_user_id = ?",
            sf["folder_id"], discord_id
        )
        if member_row is None:                               # ← ここが抜けていた
            return web.json_response({"error": "forbidden"}, status=403)

        # ── 4. 新ファイル名バリデーション ──────────
        try:
            new_base = (await request.json()).get("name", "").strip()
        except Exception:
            return web.json_response({"error": "bad_json"}, status=400)

        if not new_base:
            return web.json_response({"error": "empty"}, status=400)

        import re, os
        if re.search(r'[\\/:*?"<>|]', new_base) or len(new_base.encode()) > 255:
            return web.json_response({"error": "invalid_name"}, status=422)

        _, ext   = os.path.splitext(sf["file_name"])
        new_name = f"{new_base}{ext}"

        # ── 5. DB 更新（物理ファイルはそのまま） ──
        await db.execute(
            "UPDATE shared_files SET file_name = ? WHERE id = ?",
            new_name, file_id
        )
        await db.commit()

        user_row = await db.fetchone("SELECT username FROM users WHERE discord_id = ?", discord_id)
        username = user_row["username"] if user_row else str(discord_id)
        await _send_shared_webhook(db, sf["folder_id"], f"\N{PENCIL} {username} が `{sf['file_name']}` を `{new_name}` にリネームしました。")

        return web.json_response({"status": "ok", "new_name": new_name})

    async def create_folder(request: web.Request):
        discord_id = request.get("user_id")
        if not discord_id:
            raise web.HTTPForbidden()
        data = await request.post()
        name = data.get("name", "").strip()
        parent = data.get("parent_id")
        db = request.app["db"]
        user_id = await db.get_user_pk(discord_id)
        if not user_id or not name:
            raise web.HTTPBadRequest()
        parent_id = int(parent) if parent else None
        await db.create_user_folder(user_id, name, parent_id)
        raise web.HTTPFound(request.headers.get("Referer", "/"))

    async def delete_folder(request: web.Request):
        discord_id = request.get("user_id")
        if not discord_id:
            raise web.HTTPForbidden()
        folder_id = int(request.match_info.get("folder_id", 0))
        db = request.app["db"]
        user_id = await db.get_user_pk(discord_id)
        row = await db.fetchone("SELECT user_id FROM user_folders WHERE id=?", folder_id)
        if not user_id or not row or row["user_id"] != user_id:
            raise web.HTTPForbidden()
        await db.delete_user_folder(folder_id)
        raise web.HTTPFound(request.headers.get("Referer", "/"))

    async def delete_subfolders(request: web.Request):
        discord_id = request.get("user_id")
        if not discord_id:
            raise web.HTTPForbidden()
        data = await request.post()
        parent = data.get("parent_id")
        db = request.app["db"]
        user_id = await db.get_user_pk(discord_id)
        if not user_id:
            raise web.HTTPForbidden()
        parent_id = int(parent) if parent else None
        await db.delete_all_subfolders(user_id, parent_id)
        raise web.HTTPFound(request.headers.get("Referer", "/"))

    # ─────────────── Public download confirm ───────────────
    async def public_file(req: web.Request):
        """
        GET /f/{token}[?dl=1]
        - dl=1 付きなら即 FileResponse
        - それ以外は確認ページを表示（誰でもアクセス可）
        """
        token = req.match_info["token"]
        fid   = _verify_token(token)
        if not fid:
            raise web.HTTPForbidden()

        # ① 共有期限チェック（期限切れなら非共有化して404）
        import time, base64
        raw = base64.urlsafe_b64decode(token.encode())
        _, exp_raw, _ = raw.split(b":", 2)
        exp_ts = int(exp_raw)
        if exp_ts != 0 and time.time() > exp_ts:
            await req.app["db"].execute(
                "UPDATE files SET is_shared=0, token=NULL, expires_at=0 WHERE id=?",
                fid
            )
            await req.app["db"].commit()
            raise web.HTTPNotFound()

        # ── ここで必ず is_shared=1 & token が一致するレコードかをチェック ──
        db = req.app["db"]
        rec = await db.fetchone(
            "SELECT * FROM files WHERE id = ? AND token = ? AND is_shared = 1",
            fid, token
        )
        if not rec:
            # 共有解除済み、あるいは無効トークン
            raise web.HTTPNotFound()
        # ?dl=1 が付いていれば直接ダウンロード
        if req.query.get("dl") == "1":
            mime, _ = mimetypes.guess_type(rec["original_name"])
            return web.FileResponse(
                rec["path"],
                headers={
                    "Content-Type":     mime or "application/octet-stream",
                    "Content-Disposition":
                        f'attachment; filename="{rec["original_name"]}"'
                }
            )

        # 確認ページをレンダリング
        file_dict = dict(rec)
        preview_file = PREVIEW_DIR / f"{file_dict['id']}.jpg"
        if preview_file.exists():
            file_dict["preview_url"] = f"/previews/{preview_file.name}"
        else:
            file_dict["preview_url"] = f"{req.path}?preview=1"
        return _render(req, "public/confirm_download.html", {
            "file": file_dict,   # Row → dict でテンプレートから参照しやすく
            "request": req
        })

    # routes
    app.router.add_get("/health", health)
    app.router.add_get("/login", login_get)
    app.router.add_post("/login", login_post)
    app.router.add_get("/logout", logout)
    app.router.add_get("/users", user_list)
    app.router.add_get("/", index)
    app.router.add_get("/mobile", mobile_index)
    app.router.add_post("/upload", upload)
    app.router.add_get("/download/{token}", download)
    app.router.add_post("/upload_chunked", upload_chunked)
    app.router.add_post("/toggle_shared/{id}", toggle_shared)
    app.router.add_post("/delete/{id}", delete_file)
    app.router.add_post("/delete_all", delete_all)
    app.router.add_post("/tags/{id}", update_tags)
    app.router.add_post("/sendfile", send_file_dm)
    app.router.add_get("/search", search_files_api)
    app.router.add_get("/static/api/files", file_list_api)
    app.router.add_get("/partial/files", file_list_api)
    app.router.add_get("/shared", shared_index)
    app.router.add_get("/shared/{id}", shared_folder_view)
    app.router.add_post("/shared/upload", shared_upload)
    app.router.add_get("/shared/download/{token}", shared_download)
    app.router.add_post("/shared/delete/{file_id}", shared_delete)
    app.router.add_post("/shared/delete_all/{folder_id}", shared_delete_all)
    app.router.add_post("/create_folder", create_folder)
    app.router.add_post("/delete_folder/{folder_id}", delete_folder)
    app.router.add_post("/delete_subfolders", delete_subfolders)
    app.router.add_get("/zip/{folder_id}", download_zip)
    app.router.add_post("/shared/tags/{id}", shared_update_tags)
    app.router.add_post("/shared/toggle_shared/{id}", shared_toggle)
    app.router.add_post("/rename/{id}", rename_file)
    app.router.add_get ("/totp",  totp_get)   # 6桁入力フォーム表示
    app.router.add_post("/totp", totp_post)   # コード検証
    app.router.add_post("/shared/rename_file/{file_id}", rename_shared_file)
    app.router.add_get("/f/{token}", public_file)

    return app

async def _runner():
    runner = web.AppRunner(create_app())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 9040))).start()
    log.info("Web server started")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(_runner())
