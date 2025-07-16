from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'
TEMPLATE_SHARED = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'shared' / 'folder_view.html'
TEMPLATE_MOBILE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'folder_view.html'


def test_zip_url_variable_defined():
    text = APP_PATH.read_text(encoding='utf-8')
    assert "zip_token = _sign_token(" in text
    assert "/zip/{folder_id}?token=" in text
    assert "external=True" in text


def test_templates_use_zip_url():
    shared = TEMPLATE_SHARED.read_text(encoding='utf-8')
    mobile = TEMPLATE_MOBILE.read_text(encoding='utf-8')
    assert '{{ zip_url }}' in shared
    assert '{{ zip_url }}' in mobile
