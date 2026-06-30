"""File storage abstraction.

One interface for evidence, support attachments and training videos. Defaults to
local disk (STORAGE_BACKEND=local). Set STORAGE_BACKEND=s3 or r2 with the matching
credentials to store in S3-compatible object storage instead - no call-site changes.

Call sites should depend only on:
    save_bytes(key, data)            -> stores bytes at `key`
    open_response(key, filename, mime) -> a Starlette response that streams the file
    exists(key) -> bool
    delete(key)
"""
import os
import io
from typing import Optional

from fastapi import HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.core.config import settings
from app.core import platform_config as pc

_S3_BACKENDS = {"s3", "r2"}


def _is_s3() -> bool:
    return pc.storage_cfg()["backend"] in _S3_BACKENDS


def _bucket() -> str:
    return pc.storage_cfg()["bucket"]


def _s3_client():
    import boto3  # imported lazily so local installs don't need boto3
    cfg = pc.storage_cfg()
    kwargs = {
        "aws_access_key_id": cfg["access_key_id"],
        "aws_secret_access_key": cfg["secret_access_key"],
    }
    if cfg["backend"] == "r2" and cfg["account_id"]:
        kwargs["endpoint_url"] = f"https://{cfg['account_id']}.r2.cloudflarestorage.com"
    return boto3.client("s3", **kwargs)


def save_bytes(key: str, data: bytes) -> str:
    """Persist `data` at `key`. Returns the key."""
    if _is_s3():
        _s3_client().put_object(Bucket=_bucket(), Key=key, Body=data)
        return key
    path = os.path.join(settings.STORAGE_LOCAL_PATH, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    return key


def read_bytes(key: str) -> bytes:
    """Read the whole object into memory (used for small previews)."""
    if _is_s3():
        obj = _s3_client().get_object(Bucket=_bucket(), Key=key)
        return obj["Body"].read()
    with open(os.path.join(settings.STORAGE_LOCAL_PATH, key), "rb") as fh:
        return fh.read()


def exists(key: Optional[str]) -> bool:
    if not key:
        return False
    if _is_s3():
        try:
            _s3_client().head_object(Bucket=_bucket(), Key=key)
            return True
        except Exception:
            return False
    return os.path.exists(os.path.join(settings.STORAGE_LOCAL_PATH, key))


def delete(key: Optional[str]) -> None:
    if not key:
        return
    try:
        if _is_s3():
            _s3_client().delete_object(Bucket=_bucket(), Key=key)
        else:
            p = os.path.join(settings.STORAGE_LOCAL_PATH, key)
            if os.path.exists(p):
                os.remove(p)
    except Exception:
        pass


def open_response(key: Optional[str], filename: Optional[str] = None, mime: Optional[str] = None):
    """Return a streaming response for the stored object, or 404."""
    if not key or not exists(key):
        raise HTTPException(status_code=404, detail="File not found in storage")
    media = mime or "application/octet-stream"
    if _is_s3():
        obj = _s3_client().get_object(Bucket=_bucket(), Key=key)
        headers = {"Content-Disposition": f'inline; filename="{filename or os.path.basename(key)}"'} if filename else {}
        return StreamingResponse(io.BytesIO(obj["Body"].read()), media_type=media, headers=headers)
    path = os.path.join(settings.STORAGE_LOCAL_PATH, key)
    return FileResponse(path, media_type=media, filename=filename)
