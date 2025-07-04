from pathlib import Path

def read_template():
    tmpl_path = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'public' / 'confirm_download.html'
    return tmpl_path.read_text(encoding='utf-8')


def test_download_button_has_query_param_and_target_blank():
    html = read_template()
    assert '?dl=1&browser=1' in html
    assert 'target="_blank"' in html
