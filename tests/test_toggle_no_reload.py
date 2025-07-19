from pathlib import Path
import re

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'


def test_handle_toggle_no_reload():
    text = JS.read_text(encoding='utf-8')
    m = re.search(r"async function handleToggle[\s\S]*?}\n", text)
    assert m, 'handleToggle function not found'
    assert 'reloadFileList' not in m.group(0)


def test_ws_reload_updates_last_reload():
    text = JS.read_text(encoding='utf-8')
    assert 'lastReload = Date.now()' in text
