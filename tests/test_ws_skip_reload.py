from pathlib import Path
import re

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'


def test_skip_flag_defined():
    text = JS.read_text(encoding='utf-8')
    assert 'let wsSkipReload' in text


def test_handle_toggle_sets_flag():
    text = JS.read_text(encoding='utf-8')
    pattern = re.compile(r"async function handleToggle.*wsSkipReload\s*=\s*true", re.S)
    assert pattern.search(text)
