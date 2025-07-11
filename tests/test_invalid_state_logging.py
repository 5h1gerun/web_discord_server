from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_invalid_state_logs():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'Invalid Discord OAuth state' in text
    assert 'Invalid gdrive state: session=%s query=%s' in text
    assert 'Invalid gdrive state: flow not found for %s' in text
