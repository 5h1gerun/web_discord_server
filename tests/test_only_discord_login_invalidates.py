from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_only_discord_login_invalidates():
    text = APP_PATH.read_text(encoding='utf-8')
    no_comments = '\n'.join(
        line for line in text.splitlines() if not line.strip().startswith('#')
    )
    assert no_comments.count('sess.invalidate()') == 1
    assert 'session.invalidate()' not in no_comments
    assert 'new_session(' not in no_comments
