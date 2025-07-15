from pathlib import Path
import re

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'

def test_csrf_token_route_exists():
    text = APP_PATH.read_text(encoding='utf-8')
    assert '/csrf_token' in text
    assert re.search(r'async def \w*csrf_token', text)
    pattern = re.compile(r'json_response\(\{[^}]*"csrf_token"', re.S)
    assert pattern.search(text)
