from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_discord_login_no_new_session():
    lines = APP_PATH.read_text(encoding='utf-8').splitlines()
    start = next(i for i, l in enumerate(lines) if 'async def discord_login' in l)
    end = next(i for i, l in enumerate(lines[start+1:], start+1) if 'async def discord_callback' in l)
    snippet = '\n'.join(lines[start:end])
    assert 'new_session(req)' not in snippet
