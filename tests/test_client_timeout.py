from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'
BOT_PATH = Path(__file__).resolve().parents[1] / 'bot' / 'bot.py'


def test_http_timeout_defined():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'HTTP_TIMEOUT' in text
    assert 'ClientTimeout' in text
    assert 'timeout=HTTP_TIMEOUT' in text


def test_bot_http_timeout():
    text = BOT_PATH.read_text(encoding='utf-8')
    assert 'HTTP_TIMEOUT' in text
    assert 'timeout=HTTP_TIMEOUT' in text
