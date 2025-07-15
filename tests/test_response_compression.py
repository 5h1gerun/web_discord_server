from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_compress_middleware_added():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'compress_middleware' in text
    assert 'app.middlewares.append(compress_middleware)' in text
