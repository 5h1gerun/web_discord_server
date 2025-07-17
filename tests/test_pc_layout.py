from pathlib import Path

INDEX_HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'index.html'
CSS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-fresh.css'


def test_index_has_pc_container_class():
    html = INDEX_HTML.read_text(encoding='utf-8')
    assert 'pc-container' in html


def test_css_contains_pc_container_rule():
    text = CSS_PATH.read_text(encoding='utf-8')
    assert '.pc-container' in text
    assert '@media (min-width: 1200px)' in text
