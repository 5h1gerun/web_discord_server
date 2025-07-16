from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_private_download_uses_download_domain():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'download_url"] = _make_download_url(' in text
    assert 'external=True' in text
