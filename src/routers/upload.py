import logging
from fastapi import APIRouter, Depends, HTTPException, Header

from src.dependencies.auth import get_authorized_headers
from src.schemas.common import Media
from src.schemas.upload import UploadFileRequest
from src.services.upload.info import get_upload_info
from src.services.upload.uploader import upload_file_to_cos

router = APIRouter()


def parse_authorization_header(auth_header: str | None):
    if not auth_header:
        return None, None, None
    try:
        if auth_header.startswith("Bearer "):
            auth_header = auth_header[len("Bearer "):]
        parts = auth_header.split(";")
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
    except Exception as e:
        logging.warning(f"Failed to parse Authorization header: {e}")
    return None, None, None


@router.post("/v1/upload", response_model=Media)
async def upload_file(
    request: UploadFileRequest,
    headers: dict = Depends(get_authorized_headers),
    authorization: str = Header(default=None),
):
    try:
        # 尝试解析 Authorization 头
        agent_id_from_header, hy_user, hy_token = parse_authorization_header(authorization)
                # 如果 header 中有，就覆盖 request.agent_id
        if agent_id_from_header:
            request.agent_id = agent_id_from_header
        if hy_user:
            request.hy_user = hy_user
        if hy_token:
            request.hy_user = hy_token
        # 如果解析出 hy_user 和 hy_token，则注入 headers
        if hy_user and hy_token:
            headers["hy_user"] = hy_user
            headers["hy_token"] = hy_token

        upload_info = await get_upload_info(request.file.file_name, headers)
        logging.info("Upload info retrieved successfully")
        logging.debug(f"upload_info: {upload_info}")

        file_info = await upload_file_to_cos(
            request.file,
            upload_info,
            headers.get("User-Agent", "unknown"),
        )
        logging.info("File uploaded successfully")
        logging.debug(f"File uploaded successfully: {file_info}")
        return file_info
    except Exception as e:
        logging.error(f"Error in upload_file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
