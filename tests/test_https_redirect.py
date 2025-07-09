from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_https_redirect_middleware_exists():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'https_redirect_mw' in text
    assert 'FORCE_HTTPS' in text
    assert 'HTTPPermanentRedirect' in text
