from pathlib import Path
import re

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_chunk_cleanup_task_defined():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'async def _cleanup_chunks' in text
    assert 'asyncio.create_task(_cleanup_chunks())' in text

