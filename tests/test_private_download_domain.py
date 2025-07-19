from pathlib import Path
import re

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_private_download_not_external():
    text = APP_PATH.read_text(encoding='utf-8')
    lines = [l for l in text.splitlines() if 'download_url"] = _make_download_url(' in l]
    assert any('external=True' not in l for l in lines)
