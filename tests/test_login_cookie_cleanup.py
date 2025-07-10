from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_login_post_clears_dst_cookie():
    text = APP_PATH.read_text(encoding='utf-8')
    start = text.index('async def login_post')
    end = text.index('async def discord_login')
    part = text[start:end]
    assert part.count('del_cookie("dst", path="/")') == 4
