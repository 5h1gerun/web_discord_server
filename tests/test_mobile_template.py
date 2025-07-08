from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'index.html'


def test_mobile_index_has_subfolder_links():
    text = TEMPLATE.read_text(encoding='utf-8')
    assert '/mobile?folder=' in text
