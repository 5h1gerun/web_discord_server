from pathlib import Path

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'
TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'index.html'
MOBILE_TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'index.html'

def test_create_folder_js_reload():
    text = JS.read_text(encoding='utf-8')
    assert 'createFolderForm' in text
    assert '作成失敗' in text

def test_templates_have_form_id():
    text = TEMPLATE.read_text(encoding='utf-8')
    mobile = MOBILE_TEMPLATE.read_text(encoding='utf-8')
    assert 'id="createFolderForm"' in text
    assert 'id="createFolderForm"' in mobile

