from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_csp_allows_google_fonts():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'https://fonts.googleapis.com' in text
    assert 'https://fonts.gstatic.com' in text
