from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_rate_limit_setting():
    text = APP_PATH.read_text(encoding='utf-8')
    assert 'AsyncLimiter(1000, 60)' in text
