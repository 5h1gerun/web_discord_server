# Utility functions for web application
from __future__ import annotations
import base64
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timezone
from typing import Dict, Optional

import aiohttp
from aiohttp import web
from aiohttp_jinja2 import render_template
import aiohttp_session

from .app import FILE_HMAC_SECRET, MOBILE_TEMPLATES


def is_mobile(user_agent: str) -> bool:
    if not user_agent:
        return False
    pattern = (
        r"iPhone|Android.*Mobile|Windows Phone|iPod|BlackBerry|Opera Mini|IEMobile"
    )
    return re.search(pattern, user_agent, re.I) is not None


def render(req: web.Request, tpl: str, ctx: Dict[str, object]):
    ctx.setdefault("user_id", req.get("user_id"))
    ua = req.headers.get("User-Agent", "")
    if is_mobile(ua):
        tpl = MOBILE_TEMPLATES.get(tpl, tpl)
    return render_template(tpl, req, ctx)


def sign_token(fid: str, exp: int) -> str:
    msg = f"{fid}:{exp}".encode()
    sig = hmac.new(FILE_HMAC_SECRET, msg, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(msg + b":" + sig).decode()


def verify_token(tok: str) -> Optional[str]:
    try:
        raw = base64.urlsafe_b64decode(tok.encode())
        fid, exp_raw, sig = raw.split(b":", 2)
        exp_val = int(exp_raw)
        if exp_val != 0 and exp_val < int(datetime.now(timezone.utc).timestamp()):
            return None
        valid = hmac.compare_digest(
            sig,
            hmac.new(FILE_HMAC_SECRET, f"{fid.decode()}:{exp_raw.decode()}".encode(), hashlib.sha256).digest(),
        )
        return fid.decode() if valid else None
    except Exception:
        return None


async def issue_csrf(request: web.Request) -> str:
    session = await aiohttp_session.get_session(request)
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(16)
    return session["csrf_token"]


async def _send_shared_webhook(db, folder_id: int, message: str) -> None:
    rec = await db.get_shared_folder(int(folder_id))
    url = rec["webhook_url"] if rec else None
    if not url:
        return
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"content": message})


async def notify_shared_upload(db, folder_id: int, discord_id: int, file_name: str) -> None:
    mention = f"<@{discord_id}>"
    message = f"\N{INBOX TRAY} {mention} が `{file_name}` をアップロードしました。"
    await _send_shared_webhook(db, folder_id, message)
