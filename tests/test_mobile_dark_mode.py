from pathlib import Path

BASE_PHONE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_phone.html'
BASE_MOBILE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_mobile.html'
BASE_FRIENDLY = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_friendly.html'

CSS_PHONE = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-phone.css'
CSS_MOBILE = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-mobile.css'
CSS_FRIENDLY = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-mobile-friendly.css'

def test_base_phone_contains_dark_switch():
    text = BASE_PHONE.read_text(encoding='utf-8')
    assert 'darkModeSwitch' in text

def test_base_mobile_contains_dark_switch():
    text = BASE_MOBILE.read_text(encoding='utf-8')
    assert 'darkModeSwitch' in text

def test_base_friendly_contains_dark_switch():
    text = BASE_FRIENDLY.read_text(encoding='utf-8')
    assert 'darkModeSwitch' in text

def test_phone_css_has_dark_mode_rules():
    text = CSS_PHONE.read_text(encoding='utf-8')
    assert 'body.dark-mode' in text

def test_mobile_css_has_dark_filename_rule():
    text = CSS_MOBILE.read_text(encoding='utf-8')
    assert 'body.dark-mode .file-card .file-name' in text

def test_friendly_css_has_dark_filename_rule():
    text = CSS_FRIENDLY.read_text(encoding='utf-8')
    assert 'body.dark-mode .file-card .file-name' in text

def test_phone_css_has_dark_filename_rule():
    text = CSS_PHONE.read_text(encoding='utf-8')
    assert 'body.dark-mode .file-card .file-name' in text
