from pathlib import Path

PARTIALS = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'partials'


def test_private_showfull_uses_preview_param():
    text = (PARTIALS / 'file_table.html').read_text(encoding='utf-8')
    assert "showFull('{{ f.url }}?preview=1')" in text
    assert "showFull('{{ f.hls_url or (f.url + '?preview=1') }}', true)" in text


def test_shared_showfull_uses_preview_param():
    text = (PARTIALS / 'shared_folder_table.html').read_text(encoding='utf-8')
    assert "replace('?dl=1', '?preview=1')" in text
