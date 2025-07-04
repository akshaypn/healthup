"""
Amazfit login utility for backend token management
"""

import requests
import urllib.parse
import random
from typing import Tuple, Optional

# URL and payload definitions
URLS = {
    "tokens_amazfit": "https://api-user.huami.com/registrations/{user_email}/tokens",
    "login_amazfit": "https://account.huami.com/v2/client/login",
}

PAYLOADS = {
    "tokens_amazfit": {
        "client_id": "HuaMi",
        "password": "",
        "redirect_uri": "https://api-user.huami.com/v2/client/login",
        "token": "access"
    },
    "login_amazfit": {
        "app_name": "com.xiaomi.hm.health",
        "app_version": "6.10.5",
        "code": "",
        "country_code": "US",
        "device_id": "",
        "device_model": "phone",
        "grant_type": "access_token",
        "third_name": "huami"
    }
}

def get_amazfit_token(email: str, password: str) -> Tuple[str, str]:
    """
    Get Amazfit app_token and user_id using email/password
    Returns: (app_token, user_id)
    """
    # Generate random device ID
    device_id = "02:00:00:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )
    
    # Step 1: Get access token
    auth_url = URLS["tokens_amazfit"].format(
        user_email=urllib.parse.quote(email)
    )
    payload = PAYLOADS["tokens_amazfit"] | {"password": password}
    
    resp = requests.post(auth_url, data=payload, allow_redirects=False)
    resp.raise_for_status()
    
    redir = urllib.parse.urlparse(resp.headers["Location"])
    params = urllib.parse.parse_qs(redir.query)
    
    if "error" in params:
        raise ValueError(f"Login error: {params['error']}")
    
    access_token = params["access"][0]
    country_code = params.get("country_code", ["US"])[0]
    
    # Step 2: Exchange for app_token
    login_url = URLS["login_amazfit"]
    data = PAYLOADS["login_amazfit"] | {
        "country_code": country_code,
        "device_id": device_id,
        "third_name": "huami",
        "code": access_token,
        "grant_type": "access_token"
    }
    
    res = requests.post(login_url, data=data)
    res.raise_for_status()
    info = res.json()
    
    if "error_code" in info:
        raise RuntimeError(f"Login failed: {info.get('error_code', 'unknown error')}")
    
    app_token = info["token_info"]["app_token"]
    user_id = info["token_info"]["user_id"]
    
    return app_token, user_id 