from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_setup_tokens_defined():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'setup_tokens' in text


def test_setup_route_defined():
    text = APP_PATH.read_text(encoding='utf-8')
    assert '/setup/{token}' in text
