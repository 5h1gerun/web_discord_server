from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'public' / 'confirm_download.html'
APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'

def test_import_button_exists():
    text = HTML.read_text(encoding='utf-8')
    assert 'importBtn' in text
    assert '/import_shared' in text

def test_import_route_added():
    text = APP.read_text(encoding='utf-8')
    assert '/import_shared' in text
