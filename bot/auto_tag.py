from __future__ import annotations

"""Automatic tagging with Gemini AI."""

from pathlib import Path
import base64
import mimetypes
import os

import google.generativeai as genai


def generate_tags(file_path: Path) -> str:
    """Analyze the file and return comma separated tags using Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return ""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    mime, _ = mimetypes.guess_type(file_path)
    with file_path.open("rb") as f:
        data = f.read()

    if mime and mime.startswith("text"):
        text = data.decode(errors="ignore")
        prompt = (
            "以下のテキストから重要と思われるキーワードを5個抽出し、"\
            "カンマ区切りで出力してください:\n" + text[:16000]
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()

    b64 = base64.b64encode(data).decode()
    prompt = (
        f"与えられた{mime or 'ファイル'}の内容を解析し、関連するキーワードを5個"\
        "日本語で抽出してカンマ区切りで返してください。"
    )
    resp = model.generate_content([
        {
            "mime_type": mime or "application/octet-stream",
            "data": b64,
        },
        prompt,
    ])
    return resp.text.strip()
