from pathlib import Path

CSS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-fresh.css'


def test_shared_index_dark_mode_link_color():
    text = CSS_PATH.read_text(encoding='utf-8')
    assert 'body.dark-mode a.list-group-item-action' in text
    assert 'var(--text-color-dark)' in text

def test_expiration_text_dark_mode_color():
    text = CSS_PATH.read_text(encoding='utf-8')
    assert 'body.dark-mode .expiration-cell small' in text
