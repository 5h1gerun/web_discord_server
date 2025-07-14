from pathlib import Path

JS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'

def test_share_toggle_network_error_message():
    text = JS_PATH.read_text(encoding='utf-8')
    assert 'サーバーに接続できません。ネットワークを確認してください。' in text
