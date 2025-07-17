from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'public' / 'confirm_download.html'


def test_confirm_download_has_back_button():
    text = HTML.read_text(encoding='utf-8')
    assert "{{ request.headers.get('Referer', '/') }}" in text
