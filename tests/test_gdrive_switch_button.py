from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'web' / 'templates'
INDEX_HTML = BASE / 'index.html'
MOBILE_INDEX_HTML = BASE / 'mobile' / 'index.html'

def test_switch_button_present():
    text = INDEX_HTML.read_text(encoding='utf-8')
    assert '/gdrive_switch' in text
    assert '連携解除' in text


def test_mobile_switch_button_present():
    text = MOBILE_INDEX_HTML.read_text(encoding='utf-8')
    assert '/gdrive_switch' in text
    assert '連携解除' in text
