from __future__ import annotations

"""Automatic tagging with Gemini AI."""

from pathlib import Path
import base64
import mimetypes
import os

import google.generativeai as genai
from google.generativeai import GenerationConfig
from PyPDF2 import PdfReader


def generate_tags(file_path: Path) -> str:
    """Analyze the file and return comma separated tags using Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return ""

    # API キー設定＆モデル準備（温度や出力トークン数もここでまとめて指定）
    genai.configure(api_key=api_key)
    gen_cfg = GenerationConfig(
        temperature=0.2,
        max_output_tokens=256,
    )
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        generation_config=gen_cfg,
    )

    # ファイル読み込み
    mime, _ = mimetypes.guess_type(file_path)
    data = file_path.read_bytes()

    if not mime:
        mime = "application/octet-stream"

    # 1) プレーンテキスト処理
    if mime and mime.startswith("text"):
        text = data.decode(errors="ignore")
        prompt = (
            "以下のテキストから重要と思われるキーワードを5個抽出し、"
            "カンマ区切りで出力してください:\n" + text[:16000]
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()

    # 2) PDF はテキスト抽出を試み、失敗時はバイナリ解析
    if mime == "application/pdf":
        reader = PdfReader(str(file_path))
        pages = [p.extract_text() or "" for p in reader.pages]
        full_text = "\n".join(pages)
        if not full_text.strip():
            b64 = base64.b64encode(data).decode()
            prompt = (
                "与えられたPDFの内容を解析し、関連するキーワードを5個"
                " 日本語で抽出してカンマ区切りで返してください。"
            )
            resp = model.generate_content([
                {"mime_type": "application/pdf", "data": b64},
                {"text": prompt},
            ])
            return resp.text.strip()
        prompt = (
            "以下のPDF本文から重要と思われるキーワードを5個抽出し、"
            "カンマ区切りで出力してください:\n" + full_text[:16000]
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()

    # 3) MIME 未判定だがテキストとして解釈できる場合
    if b"\x00" not in data:
        try:
            text = data.decode()
        except UnicodeDecodeError:
            text = None
        if text and text.strip():
            prompt = (
                "以下のテキストから重要と思われるキーワードを5個抽出し、"
                "カンマ区切りで出力してください:\n" + text[:16000]
            )
            resp = model.generate_content(prompt)
            return resp.text.strip()

    # 4) 画像やその他バイナリ
    b64 = base64.b64encode(data).decode()
    prompt = (
        f"与えられた {mime or 'ファイル'} の内容を解析し、関連するキーワードを5個"
        " 日本語で抽出してカンマ区切りで返してください。"
    )
    resp = model.generate_content([
        {
            "mime_type": mime or "application/octet-stream",  # Blob 用にスネークケース
            "data": b64,
        },
        {
            "text": prompt,  # Part として扱われるプロンプト
        },
    ])
    return resp.text.strip()
