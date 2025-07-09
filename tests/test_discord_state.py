from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_discord_states_removed():
    content = APP_PATH.read_text(encoding='utf-8')
    assert 'discord_states' not in content


def test_state_cookie_used():
    content = APP_PATH.read_text(encoding='utf-8')
    assert 'set_cookie(' in content and '"dst"' in content
