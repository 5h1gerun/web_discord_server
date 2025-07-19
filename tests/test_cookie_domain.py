from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_cookie_domain_support():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'COOKIE_DOMAIN' in text
    assert 'cookie_domain = os.getenv("COOKIE_DOMAIN")' in text
    assert 'storage_kwargs["domain"] = cookie_domain' in text
