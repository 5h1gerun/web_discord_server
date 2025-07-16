from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_oauth_state_session_storage():
    content = APP_PATH.read_text(encoding='utf-8')
    assert 'sess["oauth_state"]' in content
    assert 'sess.pop("oauth_state"' in content
