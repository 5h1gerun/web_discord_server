from pathlib import Path

BOT_PATH = Path(__file__).resolve().parents[1] / 'bot' / 'bot.py'

def test_totp_enabled_on_join():
    text = BOT_PATH.read_text(encoding='utf-8')
    assert 'totp_enabled=1' in text
