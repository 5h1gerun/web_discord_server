from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_oauth_state_defined():
    content = APP_PATH.read_text(encoding='utf-8')
    assert 'oauth_state' in content
