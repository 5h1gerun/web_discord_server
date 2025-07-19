from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_shared_download_button_opens_confirm_page():
    text = APP_PATH.read_text(encoding='utf-8')
    start = text.index('プレビュー用は inline')
    snippet = text[start:start + 120]
    assert '?dl=1' not in snippet
