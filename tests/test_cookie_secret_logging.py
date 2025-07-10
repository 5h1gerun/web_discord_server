from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_cookie_secret_logged():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'COOKIE_SECRET=' in text
    assert 'log.info' in text
