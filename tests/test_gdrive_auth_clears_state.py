from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_auth_clears_state():
    text = APP.read_text(encoding='utf-8').splitlines()
    start = next(i for i, line in enumerate(text) if 'async def gdrive_auth' in line)
    snippet = '\n'.join(text[start:start + 15])
    assert 'sess.pop("gdrive_state"' in snippet
    assert 'app["gdrive_flows"].pop' in snippet
