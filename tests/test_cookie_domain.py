from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_cookie_domain_variable_used():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'COOKIE_DOMAIN' in text
