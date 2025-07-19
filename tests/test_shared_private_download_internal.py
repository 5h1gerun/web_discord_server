from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_shared_private_download_internal():
    text = APP_PATH.read_text(encoding='utf-8')
    assert '認証付きでも DOWNLOAD_DOMAIN を使用' not in text
    assert '_make_download_url(' in text
    lines = [l for l in text.splitlines() if '_make_download_url(' in l]
    assert any('external=True' not in l for l in lines)
