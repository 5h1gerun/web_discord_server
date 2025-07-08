from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_download_domain_variable_used_multiple_times():
    text = APP_PATH.read_text(encoding='utf-8')
    assert text.count('DOWNLOAD_DOMAIN') >= 5
