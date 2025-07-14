from pathlib import Path

CSS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-fresh.css'


def test_fresh_css_has_accent_colors():
    text = CSS_PATH.read_text(encoding='utf-8')
    assert '--accent-start' in text
    assert '--accent-end' in text


def test_fresh_css_uses_new_font():
    text = CSS_PATH.read_text(encoding='utf-8')
    assert 'Poppins' in text
    assert 'Noto Sans JP' in text
