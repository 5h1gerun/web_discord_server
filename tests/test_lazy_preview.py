from pathlib import Path

PARTIALS = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'partials'
MOBILE_PARTIALS = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'partials'

def read(p):
    return p.read_text(encoding='utf-8')

def test_lazy_preview_class_exists():
    files = [
        PARTIALS / 'file_table.html',
        PARTIALS / 'shared_folder_table.html',
        MOBILE_PARTIALS / 'file_cards.html',
        MOBILE_PARTIALS / 'shared_folder_cards.html',
    ]
    for f in files:
        text = read(f)
        assert 'lazy-preview' in text
