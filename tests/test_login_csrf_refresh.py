from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'web' / 'templates'
LOGIN_HTML = BASE / 'login.html'
MOBILE_LOGIN_HTML = BASE / 'mobile' / 'login.html'
TOTP_HTML = BASE / 'totp.html'


def test_login_templates_refresh_csrf():
    assert 'refreshCsrfToken' in LOGIN_HTML.read_text(encoding='utf-8')
    assert 'refreshCsrfToken' in MOBILE_LOGIN_HTML.read_text(encoding='utf-8')
    assert 'refreshCsrfToken' in TOTP_HTML.read_text(encoding='utf-8')
