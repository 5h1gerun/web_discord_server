from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_session_key_logged():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'SESSION_KEY=' in text
    assert 'COOKIE_NAME=' in text
    assert 'aiohttp_session' in text
    assert 'log.info' in text
