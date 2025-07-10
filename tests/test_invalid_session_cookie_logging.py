from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'

def test_invalid_session_cookie_logging():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'wdsid cookie present but session could not be restored' in text
    assert 'log.warning' in text
