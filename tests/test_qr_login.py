from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'
LOGIN_TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'login.html'
MOBILE_TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'login.html'


def test_qr_tokens_defined():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'qr_tokens' in text


def test_login_template_has_qr_image():
    html = LOGIN_TEMPLATE.read_text(encoding='utf-8')
    assert '/qr_image/' in html


def test_discord_button_removed():
    pc_html = LOGIN_TEMPLATE.read_text(encoding='utf-8')
    mobile_html = MOBILE_TEMPLATE.read_text(encoding='utf-8')
    assert '/discord_login' not in pc_html
    assert '/discord_login' not in mobile_html
