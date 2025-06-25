from pathlib import Path
import types
import bot.auto_tag as auto_tag

class DummyResp:
    def __init__(self, text):
        self.text = text

class DummyModel:
    def __init__(self, *args, **kwargs):
        pass
    def generate_content(self, *args, **kwargs):
        return DummyResp("tagA, tagB")

def test_generate_tags(monkeypatch, tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("sample text")
    dummy_genai = types.SimpleNamespace(
        configure=lambda **kw: None,
        GenerativeModel=lambda name: DummyModel(),
    )
    monkeypatch.setattr(auto_tag, "genai", dummy_genai)
    tags = auto_tag.generate_tags(f)
    assert tags == "tagA, tagB"
