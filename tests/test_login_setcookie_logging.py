from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_login_setcookie_logging():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'LOGIN-SETCOOKIE' in text
