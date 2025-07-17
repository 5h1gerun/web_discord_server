from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "web" / "app.py"


def test_file_list_api_uses_shared_preview():
    text = APP.read_text(encoding="utf-8")
    start = text.index("async def file_list_api")
    end = text.index("async def search_files_api")
    snippet = text[start:end]
    assert "/shared/download" in snippet


def test_mobile_index_uses_shared_preview():
    text = APP.read_text(encoding="utf-8")
    start = text.index("async def mobile_index")
    end = text.index("async def upload")
    snippet = text[start:end]
    assert "/shared/download" in snippet
