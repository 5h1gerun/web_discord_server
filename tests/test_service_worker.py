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


def test_fetch_excludes_cross_origin():
    sw = read_sw()
    pattern = re.compile(
        r"url\.origin\s*!==\s*location\.origin\)\s*{\s*return;",
        re.S,
    )
    assert pattern.search(sw)


def test_network_first_skips_post_requests():
    sw = read_sw()
    assert "request.method !== 'GET'" in sw
    assert 'return fetch(request);' in sw


def test_download_requests_not_cached():
    sw = read_sw()
    pattern = re.compile(
        r"if\s*\(\s*url\.pathname\.startsWith\('/download'\)\s*\|\|\s*url\.pathname\.startsWith\('/shared/download'\)\s*\)\s*{\s*event\.respondWith\(fetch\(request\)\);\s*return;",
        re.S,
    )
    assert pattern.search(sw)


def test_download_check_before_navigate():
    sw = read_sw()
    download_pos = sw.index("url.pathname.startsWith('/download')")
    navigate_pos = sw.index("request.mode === 'navigate'")
    assert download_pos < navigate_pos


def test_previews_cached_with_stale_while_revalidate():
    sw = read_sw()
    for path in ['/previews/', '/hls/']:
        pattern = re.compile(
            rf"url\.pathname\.startsWith\('{path}'\).*staleWhileRevalidate",
            re.S,
        )
        assert pattern.search(sw)


def test_has_cache_clear_message_handler():
    sw = read_sw()
    assert "addEventListener('message'" in sw
    assert 'caches.delete' in sw

def test_stale_while_revalidate_checks_status():
    sw = read_sw()
    pattern = re.compile(r"res\.ok\)\s*\{\s*cache.put", re.S)
    assert pattern.search(sw)


def test_cache_version_variable():
    sw = read_sw()
    assert 'const CACHE_VERSION' in sw
    pattern = re.compile(r"const CACHE_NAME = `wds-cache-\${CACHE_VERSION}`;")
    assert pattern.search(sw)
