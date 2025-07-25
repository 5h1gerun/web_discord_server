from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / 'web' / 'app.py'


def test_shared_folder_download_uses_private_link():
    text = APP.read_text(encoding='utf-8')
    pattern = re.compile(
        "async def shared_folder_view[\\s\\S]+?f\\[\\\"download_path\\\"\\] = f\\\"/download/",
        re.S,
    )
    assert pattern.search(text)
    assert 'download_path"] = f"/shared/download' not in text
