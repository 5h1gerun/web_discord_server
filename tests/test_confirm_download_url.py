from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_confirm_download_url_external():
    text = APP_PATH.read_text(encoding='utf-8')
    assert "_make_download_url(req.path + \"?dl=1\", external=True)" in text
