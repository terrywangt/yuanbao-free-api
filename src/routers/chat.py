import logging

from fastapi import APIRouter, Depends, HTTPException, Header
from sse_starlette.sse import EventSourceResponse

from src.dependencies.auth import get_authorized_headers
from src.schemas.chat import ChatCompletionRequest, YuanBaoChatCompletionRequest
from src.services.chat.completion import create_completion_stream
from src.services.chat.conversation import create_conversation
from src.utils.chat import get_model_info, parse_messages

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


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    headers: dict = Depends(get_authorized_headers),
    authorization: str = Header(default=None),
):
    try:
        # 尝试从 Authorization 头解析 agent_id, hy_user, hy_token
        agent_id_from_header, hy_user, hy_token = parse_authorization_header(authorization)

        # 如果 header 中有，就覆盖 request.agent_id
        if agent_id_from_header:
            request.agent_id = agent_id_from_header
        if hy_user:
            request.hy_user = hy_user
        if hy_token:
            request.hy_user = hy_token

        # 为后续调用准备 headers
        if hy_user and hy_token:
            headers["hy_user"] = hy_user
            headers["hy_token"] = hy_token

        if not request.chat_id:
            request.chat_id = await create_conversation(request.agent_id, headers)
            logging.info(f"Conversation created with chat_id: {request.chat_id}")

        prompt = parse_messages(request.messages)
        model_info = get_model_info(request.model)
        if not model_info:
            raise HTTPException(status_code=400, detail="invalid model")

        chat_request = YuanBaoChatCompletionRequest(
            agent_id=request.agent_id,
            chat_id=request.chat_id,
            prompt=prompt,
            chat_model_id=model_info["model"],
            multimedia=request.multimedia,
            support_functions=model_info.get("support_functions"),
        )

        generator = create_completion_stream(chat_request, headers, request.should_remove_conversation)
        logging.info(f"Streaming chat completion for chat_id: {request.chat_id}")
        return EventSourceResponse(generator, media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Error in chat_completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
