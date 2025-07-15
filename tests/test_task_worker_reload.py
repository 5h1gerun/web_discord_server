from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_task_worker_triggers_reload():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r"async def _task_worker.*broadcast_ws\(\{\"action\": \"reload\"\}\)", re.S)
    assert pattern.search(text)
