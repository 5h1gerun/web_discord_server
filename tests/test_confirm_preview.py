from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'public' / 'confirm_download.html'

def test_confirm_preview_param():
    text = HTML.read_text(encoding='utf-8')
    assert text.count('?preview=1') >= 3
