from pathlib import Path
import re

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'

def test_ws_flag_set_before_fetch():
    text = JS.read_text(encoding='utf-8')
    pattern = re.compile(r"async function handleToggle[\s\S]*wsSkipReload\s*=\s*true[\s\S]*fetch\(", re.S)
    assert pattern.search(text)
