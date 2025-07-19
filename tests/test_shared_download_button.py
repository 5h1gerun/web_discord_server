from pathlib import Path

SHARED_TABLE = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'partials' / 'shared_folder_table.html'


def test_shared_download_button_no_blank():
    html = SHARED_TABLE.read_text(encoding='utf-8')
    assert 'target="_blank"' not in html
