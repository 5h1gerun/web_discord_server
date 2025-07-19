from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_cookie_domain_configured():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'domain=cookie_domain' in text
