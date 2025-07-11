from pathlib import Path
import re

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_invalid_state_logs():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'Invalid Discord OAuth state' in text
    assert re.search(r'Invalid gdrive state.*session', text)
    assert 'flow not found' in text
