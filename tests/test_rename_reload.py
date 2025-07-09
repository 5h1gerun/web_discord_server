from pathlib import Path

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'

def test_rename_triggers_reload():
    text = JS.read_text(encoding='utf-8')
    assert 'btn.dataset.current = j.new_name;' in text
    assert 'await reloadFileList();' in text
