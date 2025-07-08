from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_download_domain_variable_used():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'DOWNLOAD_DOMAIN' in text


def test_download_url_uses_sign_token():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'signed = _sign_token(d["id"],' in text
    assert 'download_url"] = _make_download_url(f"/download/{signed}"' in text
