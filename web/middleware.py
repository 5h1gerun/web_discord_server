from __future__ import annotations
from collections import defaultdict

from aiohttp import web
from aiohttp_session import get_session
from aiohttp.web_exceptions import HTTPForbidden
from aiolimiter import AsyncLimiter
import aiohttp_session


CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;"
)

limiters = defaultdict(lambda: AsyncLimiter(30, 60))


@web.middleware
async def csrf_protect_mw(request: web.Request, handler):
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        session = await aiohttp_session.get_session(request)
        token = request.headers.get("X-CSRF-Token")
        if token is None:
            form = await request.post()
            token = form.get("csrf_token")
        if token != session.get("csrf_token"):
            if "application/json" in request.headers.get("Accept", ""):
                return web.json_response({"success": False, "error": "invalid csrf"}, status=403)
            raise HTTPForbidden(text="Invalid CSRF token")
    return await handler(request)


@web.middleware
async def auth_mw(request: web.Request, handler):
    sess = await aiohttp_session.get_session(request)
    request["user_id"] = sess.get("user_id")
    return await handler(request)


@web.middleware
async def csp_mw(request: web.Request, handler):
    resp = await handler(request)
    resp.headers["Content-Security-Policy"] = CSP_POLICY
    return resp


@web.middleware
async def rl_mw(req, handler):
    ip = req.remote
    limiter = limiters[ip]
    async with limiter:
        return await handler(req)
