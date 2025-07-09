from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_download_allows_preview_inline():
    text = APP_PATH.read_text(encoding='utf-8')
    assert text.count('req.query.get("preview") == "1"') >= 2
