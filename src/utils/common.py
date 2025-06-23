from typing import Dict

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
def generate_headers(request: dict, token: str) -> Dict[str, str]:
    # 尝试解析 Authorization 头
    agent_id_from_header, hy_user, hy_token = parse_authorization_header(authorization)
    if not agent_id_from_header:
        agent_id_from_header=request["agent_id"]
    if not hy_user:
        hy_user=request['hy_user']
    if not hy_token:
        hy_token=request['hy_token']
    return {
        "Cookie": f"hy_source={request['hy_source']}; hy_user={hy_user}; hy_token={hy_token}",
        "Origin": "https://yuanbao.tencent.com",
        "Referer": f"https://yuanbao.tencent.com/chat/{agent_id_from_header}",
        "X-Agentid":agent_id_from_header ,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }
