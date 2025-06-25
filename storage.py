"""Simple storage backend abstraction supporting local filesystem or Amazon S3."""
from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO, Optional

__all__ = [
    "save_bytes", "open_bytes", "delete", "generate_download_url", "STORAGE_BACKEND"
]

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()

if STORAGE_BACKEND == "s3":
    import boto3
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_REGION = os.getenv("AWS_REGION", None)
    _s3_client = boto3.client("s3", region_name=S3_REGION)
else:
    DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent / "data"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_bytes(fid: str, data: bytes) -> str:
    """Save bytes and return path or key."""
    if STORAGE_BACKEND == "s3":
        _s3_client.put_object(Bucket=S3_BUCKET, Key=fid, Body=data)
        return fid
    else:
        path = DATA_DIR / fid
        path.write_bytes(data)
        return str(path)


def open_bytes(fid: str) -> bytes:
    if STORAGE_BACKEND == "s3":
        obj = _s3_client.get_object(Bucket=S3_BUCKET, Key=fid)
        return obj["Body"].read()
    else:
        return (DATA_DIR / fid).read_bytes()


def delete(fid: str) -> None:
    if STORAGE_BACKEND == "s3":
        _s3_client.delete_object(Bucket=S3_BUCKET, Key=fid)
    else:
        (DATA_DIR / fid).unlink(missing_ok=True)


def generate_download_url(fid: str, filename: str, expires: int = 3600) -> str:
    """Return local path or pre-signed URL for downloads."""
    if STORAGE_BACKEND == "s3":
        return _s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": fid,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=expires,
        )
    else:
        return str(DATA_DIR / fid)
