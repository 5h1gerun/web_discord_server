from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_totp_get_sets_no_store():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'Cache-Control"] = "no-store"' in text
