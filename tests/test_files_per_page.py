from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_files_per_page_constant():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'FILES_PER_PAGE' in text
    assert 'LIMIT ? OFFSET ?' in text
