import os
import io
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
_CRED_PATH = os.getenv("GDRIVE_CREDENTIALS")
_TOKEN_PATH = os.getenv("GDRIVE_TOKEN", "token.json")
_service = None


def get_service():
    global _service
    if _service is not None:
        return _service
    if not _CRED_PATH:
        return None
    creds: Optional[Credentials] = None
    if os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(_CRED_PATH, _SCOPES)
        creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    _service = build("drive", "v3", credentials=creds)
    return _service


def upload_file(local_path: Path, filename: str) -> str:
    service = get_service()
    if service is None:
        raise RuntimeError("GDRIVE_CREDENTIALS is not set")
    file_metadata = {"name": filename}
    media = MediaFileUpload(local_path)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    return file.get("id")


def download_file(file_id: str) -> bytes:
    service = get_service()
    if service is None:
        raise RuntimeError("GDRIVE_CREDENTIALS is not set")
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue()
