from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_discord_login_logs_cookie():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'LOGIN: session_id=%s new_state=%s set_cookie=%s' in text
    assert 'log.debug' in text
