from pathlib import Path
import re

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'

def test_handle_toggle_refreshes_csrf():
    text = JS.read_text(encoding='utf-8')
    pattern = re.compile(r"async function handleToggle.*refreshCsrfToken", re.S)
    assert pattern.search(text)
