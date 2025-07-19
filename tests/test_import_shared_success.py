from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_import_shared_function_removed():
    text = APP.read_text(encoding='utf-8')
    assert 'def import_shared' not in text

