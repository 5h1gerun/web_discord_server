from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'gdrive_import.html'
MOBILE_TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'gdrive_import.html'
JS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'gdrive_import.js'


def test_manual_form_removed():
    html = TEMPLATE.read_text(encoding='utf-8')
    assert 'ファイルIDまたは共有リンク' not in html
    assert 'name="file_id"' not in html


def test_mobile_matches_pc():
    html = MOBILE_TEMPLATE.read_text(encoding='utf-8')
    assert 'ファイルIDまたは共有リンク' not in html
    assert 'name="file_id"' not in html
    assert 'id="driveFileList"' in html


def test_import_refreshes_list():
    text = JS_PATH.read_text(encoding='utf-8')
    assert text.count('loadFiles(') >= 5

