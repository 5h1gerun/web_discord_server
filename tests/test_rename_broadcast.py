from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_rename_file_triggers_reload():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r"async def rename_file.*broadcast_ws\(\{\"action\": \"reload\"\}\)", re.S)
    assert pattern.search(text)


def test_rename_shared_triggers_reload():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r"async def rename_shared_file.*broadcast_ws\(\{\"action\": \"reload\"\}\)", re.S)
    assert pattern.search(text)
