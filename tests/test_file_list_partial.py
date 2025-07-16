from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'
JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'

def test_partial_files_route_exists():
    text = APP.read_text(encoding='utf-8')
    assert '/partial/files' in text

def test_reload_uses_partial_route():
    text = JS.read_text(encoding='utf-8')
    assert '/partial/files' in text

def test_reload_uses_mobile_route():
    text = JS.read_text(encoding='utf-8')
    assert '/mobile' in text
