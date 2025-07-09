from pathlib import Path

template = Path(__file__).resolve().parents[1] / 'web' / 'templates' / 'base.html'
js_path = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'


def test_base_template_has_install_button():
    text = template.read_text(encoding='utf-8')
    assert 'id="installBtn"' in text


def test_main_js_handles_beforeinstallprompt():
    js = js_path.read_text(encoding='utf-8')
    assert 'beforeinstallprompt' in js
    assert 'deferredPrompt' in js
