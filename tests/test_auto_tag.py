from pathlib import Path
import types
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

dummy_google = types.ModuleType("google.generativeai")
class _DummyCfg:
    def __init__(self, *a, **kw):
        pass

dummy_google.GenerationConfig = _DummyCfg
dummy_google.GenerativeModel = lambda *a, **kw: None
dummy_google.configure = lambda **kw: None
sys.modules.setdefault("google", types.ModuleType("google"))
sys.modules["google.generativeai"] = dummy_google

dummy_pdf2 = types.ModuleType("PyPDF2")

class _DummyPage:
    def extract_text(self):
        return ""

class _DummyPdf:
    def __init__(self, *a, **kw):
        self.pages = [_DummyPage()]

dummy_pdf2.PdfReader = _DummyPdf
sys.modules["PyPDF2"] = dummy_pdf2

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
        GenerativeModel=lambda *a, **kw: DummyModel(),
    )
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.setattr(auto_tag, "genai", dummy_genai)
    tags = auto_tag.generate_tags(f)
    assert tags == "tagA, tagB"


def test_generate_tags_binary(monkeypatch, tmp_path):
    f = tmp_path / "unknown.bin"
    f.write_bytes(b"\x00\x01\x02")
    dummy_genai = types.SimpleNamespace(
        configure=lambda **kw: None,
        GenerativeModel=lambda *a, **kw: DummyModel(),
    )
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.setattr(auto_tag, "genai", dummy_genai)
    tags = auto_tag.generate_tags(f)
    assert tags == "tagA, tagB"
