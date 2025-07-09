from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_hls_generation_parallel():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'asyncio.gather' in text
