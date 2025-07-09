from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_dm_upload_limit_constant():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'DM_UPLOAD_LIMIT' in text
    assert 'size <= DM_UPLOAD_LIMIT' in text
