from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'
BASE_HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'base.html'
BASE_PHONE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_phone.html'


def test_logout_redirect_has_flag():
    text = APP_PATH.read_text(encoding='utf-8')
    assert '/login?logged_out=1' in text


def test_base_templates_send_clear_cache_message():
    for tpl in [BASE_HTML, BASE_PHONE]:
        text = tpl.read_text(encoding='utf-8')
        assert 'logged_out' in text
        assert "postMessage({ action: 'clearCache' })" in text

