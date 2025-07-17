from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-fresh.css'
TEMPLATES = [
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'index.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'partials' / 'home.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'shared' / 'folder_view.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'shared' / 'index.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'folder_view.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'gdrive_import.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'gdrive_import.html',
]

def test_css_has_breadcrumb_pills():
    text = CSS.read_text(encoding='utf-8')
    assert '.breadcrumb-pills' in text
    assert '\\F285' in text

def test_templates_use_breadcrumb_pills():
    for tpl in TEMPLATES:
        html = tpl.read_text(encoding='utf-8')
        assert 'breadcrumb-pills' in html
