import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'mobile'


def assert_download_attr(path: Path):
    html = path.read_text(encoding='utf-8')
    assert 'target="_blank"' not in html
    assert re.search(r'<a[^>]+download', html)


def test_file_cards_download():
    assert_download_attr(BASE / 'partials' / 'file_cards.html')


def test_shared_cards_download():
    assert_download_attr(BASE / 'partials' / 'shared_folder_cards.html')


def test_folder_view_zip_download():
    assert_download_attr(BASE / 'folder_view.html')
