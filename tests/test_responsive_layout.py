from pathlib import Path

BASE_HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'base.html'
INDEX_HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'index.html'
CSS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-fresh.css'


def test_base_contains_viewport_meta():
    text = BASE_HTML.read_text(encoding='utf-8')
    assert '<meta name="viewport"' in text
    assert 'width=device-width' in text


def test_index_has_bootstrap_grid_classes():
    html = INDEX_HTML.read_text(encoding='utf-8')
    assert 'container-fluid' in html
    assert 'col-sm-8' in html
    assert 'col-sm-4' in html


def test_css_has_mobile_responsive_rules():
    css = CSS_PATH.read_text(encoding='utf-8')
    assert '@media (max-width: 576px)' in css
    assert 'word-break: break-word' in css
    assert 'overflow-x: auto' in css
