from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-modern.css'


def test_file_name_has_max_width():
    text = CSS.read_text(encoding='utf-8')
    assert 'max-width: 18rem' in text


def test_expiration_cell_has_width():
    text = CSS.read_text(encoding='utf-8')
    assert 'width: 8rem' in text
