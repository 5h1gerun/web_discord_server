from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_state_saved_in_session():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'auth["oauth_state"] = state' in text


def test_state_popped_in_callback():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'auth.pop("oauth_state"' in text
