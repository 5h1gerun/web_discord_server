from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_state_not_saved_in_session():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'sess["discord_state"] = state' not in text


def test_state_not_popped_in_callback():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'sess.pop("discord_state"' not in text
