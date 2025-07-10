from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_cookie_secure_env_variable():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'COOKIE_SECURE' in text
    assert 'secure=True' in text
