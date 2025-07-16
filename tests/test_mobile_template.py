from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'index.html'


def test_mobile_index_has_subfolder_links():
    text = TEMPLATE.read_text(encoding='utf-8')
    assert '/mobile?folder=' in text

def test_mobile_index_has_folder_container():
    text = TEMPLATE.read_text(encoding='utf-8')
    assert 'id="subfolderList"' in text

def test_base_phone_sets_flag():
    base = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile' / 'base_phone.html'
    html = base.read_text(encoding='utf-8')
    assert 'IS_MOBILE' in html
