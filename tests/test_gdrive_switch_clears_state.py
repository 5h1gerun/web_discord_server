from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_switch_clears_state():
    text = APP.read_text(encoding='utf-8')
    assert 'sess.pop("gdrive_state"' in text
    assert '"/gdrive_auth")' in text
