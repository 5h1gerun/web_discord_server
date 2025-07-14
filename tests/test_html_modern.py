from pathlib import Path

BASE_TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'base.html'
INDEX_TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'index.html'


def test_base_navbar_has_accent_class():
    text = BASE_TEMPLATE.read_text(encoding='utf-8')
    assert 'navbar-accent' in text


def test_index_has_hero_header():
    text = INDEX_TEMPLATE.read_text(encoding='utf-8')
    assert '<header class="hero' in text
