from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_cookie_secret_file_fallback():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'COOKIE_SECRET_FILE' in text
    assert 'cookie_secret.key' in text
    assert 'read_text' in text
    assert 'write_text' in text
