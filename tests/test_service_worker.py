import re
from pathlib import Path

SW_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'service-worker.js'


def read_sw():
    return SW_PATH.read_text(encoding='utf-8')


def test_offline_urls_contains_cdn():
    sw = read_sw()
    cdn_urls = [
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
        'https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/6.4.0/mdb.min.css',
        'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css',
        'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css',
        'https://cdnjs.cloudflare.com/ajax/libs/hover.css/2.3.1/css/hover-min.css',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.2/vanilla-tilt.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/6.4.0/mdb.min.js',
        'https://cdn.jsdelivr.net/npm/hls.js@latest',
    ]
    for url in cdn_urls:
        assert url in sw


def test_handle_navigate_uses_cache_first():
    sw = read_sw()
    assert 'async function handleNavigate' in sw
    assert 'if (cached)' in sw
    assert 'return cached;' in sw
