from pathlib import Path

JS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'


def test_copy_toast_autohide_delay():
    text = JS.read_text(encoding='utf-8')
    assert 'autohide: true' in text
    assert 'delay: 3000' in text
