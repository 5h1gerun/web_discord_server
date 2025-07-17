from pathlib import Path
import re

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'

def test_tag_input_updates_on_change():
    text = JS.read_text(encoding='utf-8')
    pattern = re.compile(r'document\.addEventListener\("change".*classList\.contains\("tag-input"\)', re.S)
    assert pattern.search(text)
