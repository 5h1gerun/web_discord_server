from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_ws_handler_checks_transport():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'request.transport is None' in text
