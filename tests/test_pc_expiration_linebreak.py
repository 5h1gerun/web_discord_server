from pathlib import Path
import re

JS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'main.js'
CSS_PATH = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style-fresh.css'


def test_format_expiration_has_newline():
    text = JS_PATH.read_text(encoding='utf-8')
    pattern = re.compile(r'\$\{mins\}分\\n\$\{secs\}秒`')
    assert pattern.search(text)


def test_pc_css_uses_pre_line():
    text = CSS_PATH.read_text(encoding='utf-8')
    pattern = re.compile(r'\.expiration-cell\s+small\s*{[^}]*white-space:\s*pre-line;', re.S)
    assert pattern.search(text)
