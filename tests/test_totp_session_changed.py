from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_totp_get_marks_changed():
    text = APP_PATH.read_text(encoding='utf-8')
    start = text.index('async def totp_get')
    end = text.index('async def totp_post')
    part = text[start:end]
    assert 'sess.changed()' in part
