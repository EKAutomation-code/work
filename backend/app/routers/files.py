from pathlib import Path
from uuid import uuid4

import boto3
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.dependencies import require_approved
from app.models import User
from app.schemas import PresignIn, PresignOut

router = APIRouter(prefix="/files", tags=["files"])


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )


def build_download_url(file_key: str, file_name: str | None = None) -> str:
    params = {"Bucket": settings.s3_bucket, "Key": file_key}
    if file_name:
        params["ResponseContentDisposition"] = f'attachment; filename="{Path(file_name).name}"'
    return s3_client().generate_presigned_url(
        ClientMethod="get_object",
        Params=params,
        ExpiresIn=3600,
    )


@router.post("/presign", response_model=PresignOut)
def presign_upload(payload: PresignIn, user: User = Depends(require_approved)):
    safe_purpose = payload.purpose if payload.purpose in {"homework", "avatars", "chat"} else "homework"
    file_key = f"{safe_purpose}/{user.id}/{uuid4()}-{payload.file_name}"
    upload_url = s3_client().generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": settings.s3_bucket, "Key": file_key, "ContentType": payload.content_type},
        ExpiresIn=900,
    )
    return PresignOut(upload_url=upload_url, file_key=file_key)
