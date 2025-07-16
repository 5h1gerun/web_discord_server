from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_gdrive_callback_calls_gdrive_auth_on_invalid_state():
    lines = APP.read_text(encoding='utf-8').splitlines()
    start = next(i for i, l in enumerate(lines) if 'async def gdrive_callback' in l)
    snippet = '\n'.join(lines[start:start + 20])
    assert 'await gdrive_auth(req)' in snippet
