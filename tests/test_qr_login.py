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
    assert '/discord_login' in mobile_html


def test_pc_login_includes_form():
    html = LOGIN_TEMPLATE.read_text(encoding='utf-8')
    assert '<form' in html
    assert 'username' in html


def test_qr_done_rendered_on_mobile_flow():
    text = APP_PATH.read_text(encoding='utf-8')
    assert text.count('qr_done.html') >= 4


def test_ws_event_handler_added():
    js = (Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js').read_text(encoding='utf-8')
    assert "data.action === 'qr_login'" in js


def test_visibility_handler_in_template():
    html = LOGIN_TEMPLATE.read_text(encoding='utf-8')
    assert 'visibilitychange' in html


def test_login_get_stores_qr_image():
    text = APP_PATH.read_text(encoding='utf-8')
    assert '"image": buf.getvalue()' in text


def test_qr_image_uses_cached_data():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'info.get("image")' in text
