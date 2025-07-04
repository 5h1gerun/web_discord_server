from pathlib import Path

TPL_PATH = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'public' / 'confirm_download.html'

def read_template():
    return TPL_PATH.read_text(encoding='utf-8')

def test_download_button_opens_new_tab():
    html = read_template()
    assert 'target="_blank"' in html
