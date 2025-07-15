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

def test_mobile_templates_have_fouc_script():
    phone = BASE_PHONE.read_text(encoding='utf-8')
    mobile = BASE_MOBILE.read_text(encoding='utf-8')
    friendly = BASE_FRIENDLY.read_text(encoding='utf-8')
    snippet = 'prefers-color-scheme: dark'
    assert snippet in phone
    assert snippet in mobile
    assert snippet in friendly

def test_mobile_css_has_dark_filename_rule():
    text = CSS_MOBILE.read_text(encoding='utf-8')
    assert 'body.dark-mode .file-card .file-name' in text

def test_friendly_css_has_dark_filename_rule():
    text = CSS_FRIENDLY.read_text(encoding='utf-8')
    assert 'body.dark-mode .file-card .file-name' in text

def test_phone_css_has_dark_filename_rule():
    text = CSS_PHONE.read_text(encoding='utf-8')
    assert 'body.dark-mode .file-card .file-name' in text

def test_css_has_dark_expiration_rule():
    phone_css = CSS_PHONE.read_text(encoding='utf-8')
    mobile_css = CSS_MOBILE.read_text(encoding='utf-8')
    friendly_css = CSS_FRIENDLY.read_text(encoding='utf-8')
    snippet = 'body.dark-mode .expiration-cell small'
    assert snippet in phone_css
    assert snippet in mobile_css
    assert snippet in friendly_css

def test_css_has_dark_list_group_rule():
    phone_css = CSS_PHONE.read_text(encoding='utf-8')
    mobile_css = CSS_MOBILE.read_text(encoding='utf-8')
    friendly_css = CSS_FRIENDLY.read_text(encoding='utf-8')
    snippet = 'body.dark-mode .list-group-item'
    assert snippet in phone_css
    assert snippet in mobile_css
    assert snippet in friendly_css
