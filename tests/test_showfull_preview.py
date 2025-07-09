from pathlib import Path

PARTIALS = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'partials'


def test_private_showfull_uses_preview_param():
    text = (PARTIALS / 'file_table.html').read_text(encoding='utf-8')
    assert "showFull('{{ f.download_path }}?preview=1')" in text
    assert "showFull('{{ f.hls_url or (f.download_path + '?preview=1') }}', true)" in text


def test_shared_showfull_uses_preview_param():
    text = (PARTIALS / 'shared_folder_table.html').read_text(encoding='utf-8')
    assert "showFull('{{ f.download_path }}?preview=1')" in text
    assert "showFull('{{ f.hls_url or (f.download_path + '?preview=1') }}', true)" in text
