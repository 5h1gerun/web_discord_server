from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_shared_folder_uses_file_to_dict_external():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(r"async def shared_folder_view[\s\S]+?_file_to_dict\([^\n]*external=True", re.S)
    assert pattern.search(text)
