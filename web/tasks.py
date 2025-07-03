from __future__ import annotations
import asyncio
import logging
import mimetypes
import os
import subprocess
from pathlib import Path

from PIL import Image
from pdf2image import convert_from_path
from aiohttp import web

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
PREVIEW_DIR = DATA_DIR / "previews"
HLS_DIR = DATA_DIR / "hls"

log = logging.getLogger("web")


def generate_preview_and_tags(path: Path, fid: str, file_name: str) -> str:
    mime, _ = mimetypes.guess_type(file_name)
    preview_path = PREVIEW_DIR / f"{fid}.jpg"
    try:
        if mime and mime.startswith("image"):
            img = Image.open(path)
            img.thumbnail((320, 320))
            img.convert("RGB").save(preview_path, "JPEG")
        elif mime and mime.startswith("video"):
            subprocess.run([
                "ffmpeg","-y","-i", str(path),"-ss","00:00:01","-vframes","1", str(preview_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif mime == "application/pdf":
            pages = convert_from_path(str(path), first_page=1, last_page=1)
            if pages:
                img = pages[0]
                img.thumbnail((320, 320))
                img.save(preview_path, "JPEG")
        elif mime and mime.startswith("application/vnd"):
            tmp_pdf = path.with_suffix(".pdf")
            subprocess.run([
                "libreoffice","--headless","--convert-to","pdf", str(path), "--outdir", str(path.parent)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if tmp_pdf.exists():
                pages = convert_from_path(str(tmp_pdf), first_page=1, last_page=1)
                if pages:
                    img = pages[0]
                    img.thumbnail((320, 320))
                    img.save(preview_path, "JPEG")
                tmp_pdf.unlink(missing_ok=True)
        else:
            preview_path = None
    except Exception as e:
        log.warning("preview generation failed: %s", e)
        if preview_path and preview_path.exists():
            preview_path.unlink(missing_ok=True)
    from bot.auto_tag import generate_tags
    return generate_tags(path, file_name)


async def generate_hls(path: Path, fid: str) -> None:
    variants = [
        ("360p", 640, 360, 800_000),
        ("720p", 1280, 720, 2_400_000),
    ]
    out_dir = HLS_DIR / fid
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, w, h, br in variants:
        out = out_dir / f"{name}.m3u8"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg","-y","-i", str(path),"-vf", f"scale=w={w}:h={h}",
            "-c:v","libx264","-c:a","aac","-b:v", str(br),"-hls_time","4","-hls_playlist_type","vod", str(out),
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
    master = out_dir / "master.m3u8"
    with master.open("w") as f:
        f.write("#EXTM3U\n#EXT-X-VERSION:3\n")
        for name, w, h, br in variants:
            f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={br},RESOLUTION={w}x{h}\n")
            f.write(f"{name}.m3u8\n")


async def task_worker(app: web.Application):
    queue: asyncio.Queue = app["task_queue"]
    while True:
        job = await queue.get()
        try:
            tags = await asyncio.to_thread(generate_preview_and_tags, job["path"], job["fid"], job["file_name"])
            if job.get("shared"):
                await app["db"].update_shared_tags(job["fid"], tags)
            else:
                await app["db"].update_tags(job["fid"], tags)
        except Exception as e:
            log.exception("Background task failed: %s", e)
        finally:
            queue.task_done()

