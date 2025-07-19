from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_shared_private_download_internal():
    text = APP_PATH.read_text(encoding='utf-8')
    assert '認証済みのユーザーのみ利用するためドメインを固定しない' in text
    assert '_make_download_url(f["download_path"])' in text
