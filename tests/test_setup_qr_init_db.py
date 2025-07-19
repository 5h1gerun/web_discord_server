from pathlib import Path
import re

CMD_PATH = Path(__file__).resolve().parents[1] / 'bot' / 'commands.py'

def test_setup_qr_initializes_db():
    text = CMD_PATH.read_text(encoding='utf-8')
    pattern = re.compile(r"async def setup_qr.*init_db", re.S)
    assert pattern.search(text)
