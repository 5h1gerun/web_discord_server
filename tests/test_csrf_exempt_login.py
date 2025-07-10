from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'

def test_login_csrf_exempt():
    text = APP_PATH.read_text(encoding='utf-8')
    start = text.index('async def csrf_protect_mw')
    end = text.index('async def auth_mw')
    part = text[start:end]
    assert 'request.path == "/login"' in part
