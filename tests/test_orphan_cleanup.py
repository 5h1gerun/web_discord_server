from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_orphan_cleanup_task_defined():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'async def _cleanup_orphan_files' in text
    assert 'asyncio.create_task(_cleanup_orphan_files(app))' in text
    assert 'DATA_DIR.iterdir()' in text
