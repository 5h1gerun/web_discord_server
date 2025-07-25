from pathlib import Path

BASE_HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'base.html'
INDEX_HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'index.html'
CSS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-modern.css'
FILE_TABLE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'partials' / 'file_table.html'
SHARED_TABLE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'partials' / 'shared_folder_table.html'


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


def test_css_thumb_size_variable():
    css = CSS_PATH.read_text(encoding='utf-8')
    assert '--thumb-size: 60px' in css
    assert '--thumb-size: 40px' in css


def test_templates_use_thumb_classes():
    file_html = FILE_TABLE.read_text(encoding='utf-8')
    shared_html = SHARED_TABLE.read_text(encoding='utf-8')
    assert 'thumb-btn' in file_html
    assert 'thumb-media' in file_html
    assert 'thumb-btn' in shared_html
    assert 'thumb-media' in shared_html
