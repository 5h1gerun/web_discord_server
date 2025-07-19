from pathlib import Path
import re

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'

def test_setup_token_not_popped():
    text = APP_PATH.read_text(encoding='utf-8')
    pattern = re.compile(r'setup_tokens"\]\.get\(')
    assert pattern.search(text)
