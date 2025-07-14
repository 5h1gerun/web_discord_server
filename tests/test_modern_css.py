from pathlib import Path

CSS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-modern.css'

def test_modern_css_has_accent_colors():
    text = CSS_PATH.read_text(encoding='utf-8')
    assert '--accent-start' in text
    assert '--accent-end' in text


def test_modern_css_uses_inter_font():
    text = CSS_PATH.read_text(encoding='utf-8')
    assert 'Inter' in text
    assert 'Noto Sans JP' in text

