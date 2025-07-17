from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-fresh.css'
PHONE_CSS = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-phone.css'

PC_TEMPLATES = [
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'index.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'partials' / 'home.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'shared' / 'folder_view.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'shared' / 'index.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'gdrive_import.html',
]

PHONE_TEMPLATES = [
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'folder_view.html',
    Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'gdrive_import.html',
]

def test_css_has_breadcrumb_pills():
    text = CSS.read_text(encoding='utf-8')
    assert '.breadcrumb-pills' in text
    assert '\\F285' in text


def test_phone_css_has_breadcrumb_phone():
    text = PHONE_CSS.read_text(encoding='utf-8')
    assert '.breadcrumb-phone' in text
    assert 'content: ">"' in text

def test_templates_use_correct_breadcrumb_classes():
    for tpl in PC_TEMPLATES:
        html = tpl.read_text(encoding='utf-8')
        assert 'breadcrumb-pills' in html
    for tpl in PHONE_TEMPLATES:
        html = tpl.read_text(encoding='utf-8')
        assert 'breadcrumb-phone' in html
