from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_shared_private_download_internal():
    text = APP_PATH.read_text(encoding='utf-8')
    assert '認証付きでも DOWNLOAD_DOMAIN を使用' in text
    assert '_make_download_url(' in text
    assert 'external=True' in text
