from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_discord_callback_logs_state():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'discord_callback states' in text
    assert 'log.info' in text
