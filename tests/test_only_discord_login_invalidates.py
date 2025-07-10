from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_only_discord_login_invalidates():
    text = APP_PATH.read_text(encoding='utf-8')
    assert text.count('sess.invalidate()') == 1
    assert 'session.invalidate()' not in text
