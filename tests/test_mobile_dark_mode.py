from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_phone.html'
CSS  = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-phone.css'

def test_base_phone_contains_dark_switch():
    text = BASE.read_text(encoding='utf-8')
    assert 'darkModeSwitch' in text

def test_phone_css_has_dark_mode_rules():
    text = CSS.read_text(encoding='utf-8')
    assert 'body.dark-mode' in text
