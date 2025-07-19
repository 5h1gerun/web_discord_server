from pathlib import Path

CMD_PATH = Path(__file__).resolve().parents[1] / 'bot' / 'commands.py'

def test_setup_qr_has_descriptions():
    text = CMD_PATH.read_text(encoding='utf-8')
    assert '自動設定用 QR' in text
    assert '二要素認証用 QR' in text
