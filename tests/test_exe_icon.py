from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'

def test_icon_map_contains_exe():
    text = APP_PATH.read_text(encoding='utf-8')
    assert '"exe": "bi-file-earmark-binary"' in text
