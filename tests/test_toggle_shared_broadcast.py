from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'

def test_toggle_shared_triggers_reload():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r"async def toggle_shared.*broadcast_ws\(\{\"action\": \"reload\"\}\)", re.S)
    assert pattern.search(text)

def test_shared_toggle_triggers_reload():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r"async def shared_toggle.*broadcast_ws\(\{\"action\": \"reload\"\}\)", re.S)
    assert pattern.search(text)
