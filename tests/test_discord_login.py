from pathlib import Path
import re

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_oauth_url_contains_disable_mobile_redirect():
    src = APP_PATH.read_text(encoding='utf-8')
    pattern = re.compile(r"disable_mobile_redirect\"?\s*:\s*\"true\"")
    assert pattern.search(src)
