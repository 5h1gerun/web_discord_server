from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_session_cookie_samesite_none():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'EncryptedCookieStorage(' in text
    assert 'cookie_name="wdsid"' in text
    assert 'samesite="None"' in text
    assert 'secure=True' in text
    assert 'path="/"' in text
