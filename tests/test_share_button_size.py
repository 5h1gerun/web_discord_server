from pathlib import Path

CSS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-phone.css'


def test_shared_toggle_has_larger_size():
    text = CSS_PATH.read_text(encoding='utf-8')
    assert '.shared-toggle' in text
    assert 'padding: 0.4rem 0.6rem;' in text
    assert 'font-size: 0.9rem;' in text
