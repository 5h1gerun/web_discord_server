import os
import io
import json
from pathlib import Path
from typing import List, Tuple, Dict

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request

_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
_CRED_PATH = os.getenv("GDRIVE_CREDENTIALS")


def build_flow(redirect_uri: str) -> Flow:
    if not _CRED_PATH:
        raise RuntimeError("GDRIVE_CREDENTIALS is not set")
    return Flow.from_client_secrets_file(
        _CRED_PATH, scopes=_SCOPES, redirect_uri=redirect_uri
    )


def _service_from_token(token_json: str):
    info = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(info, _SCOPES)
    if not creds.valid:
        creds.refresh(Request())
    service = build("drive", "v3", credentials=creds)
    return service, creds.to_json()


def upload_file(local_path: Path, filename: str, token_json: str) -> Tuple[str, str]:
    service, token_json = _service_from_token(token_json)
    file_metadata = {"name": filename}
    media = MediaFileUpload(local_path)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    return file.get("id"), token_json


def download_file(file_id: str, token_json: str) -> Tuple[bytes, str]:
    service, token_json = _service_from_token(token_json)
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue(), token_json


def get_file_name(file_id: str, token_json: str) -> Tuple[str, str]:
    service, token_json = _service_from_token(token_json)
    meta = service.files().get(fileId=file_id, fields="name").execute()
    return meta.get("name", file_id), token_json


def list_files(
    token_json: str, page_size: int = 20
) -> Tuple[List[Dict[str, str]], str]:
    """Return a list of recent files on Drive."""
    service, token_json = _service_from_token(token_json)
    res = (
        service.files()
        .list(pageSize=page_size, fields="files(id,name,mimeType)")
        .execute()
    )
    return res.get("files", []), token_json
