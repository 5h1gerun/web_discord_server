from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'

def test_update_tags_triggers_reload():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r"async def update_tags.*broadcast_ws\(\{\"action\": \"reload\"\}\)", re.S)
    assert pattern.search(text)

def test_shared_update_tags_triggers_reload():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r"async def shared_update_tags.*broadcast_ws\(\{\"action\": \"reload\"\}\)", re.S)
    assert pattern.search(text)
