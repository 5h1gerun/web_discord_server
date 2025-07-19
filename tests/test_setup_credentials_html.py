from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'
TEMPLATE_PATH = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'setup_credentials.html'


def test_setup_credentials_template_exists():
    assert TEMPLATE_PATH.exists()


def test_setup_credentials_uses_template():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'setup_credentials.html' in text
    assert 'application/json' in text
