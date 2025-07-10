from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_dst_cookie_has_secure_lax_path():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'set_cookie(' in text
    assert '"dst"' in text
    assert 'samesite="Lax"' in text
    assert 'secure=True' in text
    assert 'path="/"' in text
