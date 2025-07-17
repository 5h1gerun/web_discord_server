from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'gdrive_import.html'
MOBILE_TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'gdrive_import.html'
JS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'gdrive_import.js'


def test_manual_form_removed():
    html = TEMPLATE.read_text(encoding='utf-8')
    assert 'ファイルIDまたは共有リンク' not in html
    assert 'name="file_id"' not in html
    assert 'list-group' in html


def test_mobile_matches_pc():
    html = MOBILE_TEMPLATE.read_text(encoding='utf-8')
    assert 'ファイルIDまたは共有リンク' not in html
    assert 'name="file_id"' not in html
    assert 'id="driveFileList"' in html
    assert 'list-group' in html


def test_import_refreshes_list():
    text = JS_PATH.read_text(encoding='utf-8')
    assert text.count('loadFiles(') >= 5
    assert 'iconByName' in text


def test_back_link_ajax():
    pc = TEMPLATE.read_text(encoding='utf-8')
    mobile = MOBILE_TEMPLATE.read_text(encoding='utf-8')
    assert 'data-ajax' in pc
    assert 'data-ajax' in mobile


def test_clear_button_and_spinner():
    pc = TEMPLATE.read_text(encoding='utf-8')
    mobile = MOBILE_TEMPLATE.read_text(encoding='utf-8')
    js = JS_PATH.read_text(encoding='utf-8')
    assert 'clearSearch' in pc
    assert 'clearSearch' in mobile
    assert 'spinner-border' in js
    assert 'list-group-item-action' in js
    assert 'flex-shrink-0' in js


def test_pc_width():
    html = TEMPLATE.read_text(encoding='utf-8')
    assert 'max-width:640px' in html

