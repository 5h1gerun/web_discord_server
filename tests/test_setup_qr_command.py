from pathlib import Path

BOT_PATH = Path(__file__).resolve().parents[1] / 'bot' / 'bot.py'


def test_setup_qr_command_exists():
    text = BOT_PATH.read_text(encoding='utf-8')
    assert 'setup_qr' in text
