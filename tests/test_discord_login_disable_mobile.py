from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_disable_mobile_redirect_param():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'disable_mobile_redirect' in text
