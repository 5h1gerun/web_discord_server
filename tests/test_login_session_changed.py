from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_login_post_marks_changed():
    text = APP_PATH.read_text(encoding='utf-8')
    start = text.index('async def login_post')
    end = text.index('async def discord_login')
    part = text[start:end]
    assert 'sess.changed()' in part


def test_totp_post_marks_changed():
    text = APP_PATH.read_text(encoding='utf-8')
    start = text.index('async def totp_post')
    end = text.index('async def logout')
    part = text[start:end]
    assert 'sess.changed()' in part
