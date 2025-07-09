from pathlib import Path

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'

def test_download_link_cache_bust():
    text = JS.read_text(encoding='utf-8')
    assert '.download-link' in text
    assert "searchParams.set('_'" in text
