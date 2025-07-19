from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_shared_private_download_internal():
    text = APP_PATH.read_text(encoding='utf-8')
    found = False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if '認証が必要なため DOWNLOAD_DOMAIN は使用しない' in line:
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            assert '_make_download_url(' in next_line
            assert 'external=True' not in next_line
            found = True
            break
    assert found
