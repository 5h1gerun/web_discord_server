from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_import_shared_returns_success():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r'return\s+web.json_response\(\{"success":\s*True,\s*"file_id"')
    assert pattern.search(text)

