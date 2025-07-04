"""
huami_get_http_token.py
Fully rewritten script that logs in to Huami/Amazfit/Xiaomi Cloud **and
prints the HTTPS `app_token`** you must send as the `apptoken` header
for every cloud API call (e.g. `/v1/data/band_data.json`).

Differences from the original:
* clearly separates the *login flow* and *BLE device query*;
* prints the `APP_TOKEN=` line immediately after successful login;
* optional `--token-only` flag exits right after printing the token;
* cleans up unused code paths but keeps BLE‐key / AGPS / firmware helpers.

Usage examples
--------------
# just get the cloud header token and exit
python huami_get_http_token.py -m amazfit -e you@mail.com -p 'your-pw' --token-only

# full flow (token + BLE keys + AGPS)
python huami_get_http_token.py -m amazfit -e you@mail.com -p 'your-pw' -b -g
"""

import argparse
import getpass
import json
import random
import shutil
import sys
import urllib.parse
import uuid
import time

import requests
from rich import box
from rich.console import Console
from rich.table import Table

# URL and payload definitions
URLS = {
    "login_xiaomi": "https://account.xiaomi.com/oauth2/authorize?skip_confirm=true&client_id=HuaMi&response_type=code&redirect_uri=https%3A%2F%2Fapi-user.huami.com%2Fv2%2Fclient%2Flogin&_locale=en_US",
    "tokens_amazfit": "https://api-user.huami.com/registrations/{user_email}/tokens",
    "login_amazfit": "https://account.huami.com/v2/client/login",
    "devices": "https://api-user.huami.com/v1/user/{user_id}/devices",
    "agps": "https://api-user.huami.com/v1/app/agps/{pack_name}",
    "logout": "https://account.huami.com/v2/client/logout"
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
    },
    "devices": {
        "appname": "com.xiaomi.hm.health",
        "appPlatform": "web",
        "User-Agent": "Zepp/6.10.5 PythonScript"
    },
    "agps": {
        "appname": "com.xiaomi.hm.health",
        "appPlatform": "web",
        "User-Agent": "Zepp/6.10.5 PythonScript"
    },
    "logout": {
        "app_name": "com.xiaomi.hm.health",
        "app_version": "6.10.5",
        "device_id": "",
        "device_model": "phone"
    }
}

ERRORS = {
    "10001": "Invalid email or password",
    "10002": "Account not found",
    "10003": "Account locked",
    "10004": "Too many login attempts",
    "10005": "Invalid verification code",
    "10006": "Account not activated",
    "10007": "Invalid token",
    "10008": "Token expired",
    "10009": "Invalid device",
    "10010": "Device not found"
}


class HuamiAmazfit:
    """Login helper & data fetcher"""
    def __init__(self, method="amazfit", email=None, password=None):
        if method == "amazfit" and (not email or not password):
            raise ValueError("For Amazfit login you must pass e-mail and password.")

        self.method = method
        self.email = email
        self.password = password

        self.access_token: str | None = None
        self.country_code: str | None = None

        self.app_token: str | None = None    # <- the HTTPS header value we need
        self.login_token: str | None = None
        self.user_id: str | None = None

        self.device_id = "02:00:00:%02x:%02x:%02x" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )

    # --------------------------------------------------------------------- #
    # 1) obtain short "code" (access token) from login redirect
    # --------------------------------------------------------------------- #
    def get_access_token(self) -> str:
        print(f"[+] requesting login code via {self.method} method")

        if self.method == "xiaomi":
            # web-login flow
            login_url = URLS["login_xiaomi"]
            print(f"Open this URL in a browser and sign in:\n{login_url}\n")
            redirect = input("Paste the final redirected URL: ").strip()
            parsed = urllib.parse.urlparse(redirect)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" not in params:
                raise ValueError("URL missing ?code=… parameter")
            self.access_token = params["code"][0]
            self.country_code = "US"

        else:  # amazfit account
            auth_url = URLS["tokens_amazfit"].format(
                user_email=urllib.parse.quote(self.email)
            )
            payload = PAYLOADS["tokens_amazfit"] | {"password": self.password}
            resp = requests.post(auth_url, data=payload, allow_redirects=False)
            resp.raise_for_status()
            redir = urllib.parse.urlparse(resp.headers["Location"])
            params = urllib.parse.parse_qs(redir.query)

            if "error" in params:
                raise ValueError(f"Login error: {params['error']}")

            self.access_token = params["access"][0]
            self.country_code = params.get("country_code", ["US"])[0]

        print(f"[+] received short access token: {self.access_token}")
        return self.access_token

    # --------------------------------------------------------------------- #
    # 2) exchange code for long-lived `app_token`
    # --------------------------------------------------------------------- #
    def login(self) -> str:
        print("[+] exchanging code for app_token")
        login_url = URLS["login_amazfit"]
        data = PAYLOADS["login_amazfit"] | {
            "country_code": self.country_code,
            "device_id": self.device_id,
            "third_name": "huami" if self.method == "amazfit" else "mi-watch",
            "code": self.access_token,
            "grant_type": "access_token"
            if self.method == "amazfit"
            else "request_token",
        }

        res = requests.post(login_url, data=data)
        res.raise_for_status()
        info = res.json()

        if "error_code" in info:
            raise RuntimeError(ERRORS.get(info["error_code"], "unknown error"))

        self.app_token = info["token_info"]["app_token"]
        self.login_token = info["token_info"]["login_token"]
        self.user_id = info["token_info"]["user_id"]

        print(f"[+] APP_TOKEN={self.app_token}")  # <-- main result
        print(f"[+] USER_ID={self.user_id}")
        return self.app_token

    # --------------------------------------------------------------------- #
    # 3) (optional) device list to retrieve BLE auth_keys
    # --------------------------------------------------------------------- #
    def get_wearables(self):
        print("[+] fetching linked devices (BLE keys)")
        url = URLS["devices"].format(user_id=urllib.parse.quote(self.user_id))
        headers = PAYLOADS["devices"] | {"apptoken": self.app_token}
        res = requests.get(url, params={"enableMultiDevice": "true"}, headers=headers)
        res.raise_for_status()
        return res.json().get("items", [])

    # --------------------------------------------------------------------- #
    # utilities kept unchanged (AGPS, firmware, logout)
    # --------------------------------------------------------------------- #
    def download_agps(self):
        agps_types = [
            ("AGPS_ALM", "cep_1week.zip"),
            ("AGPSZIP", "cep_7days.zip"),
            ("LLE", "lle_1week.zip"),
            ("AGPS", "cep_pak.bin"),
        ]
        hdr = PAYLOADS["agps"] | {"apptoken": self.app_token}
        for pack, fname in agps_types:
            print(f"[+] downloading {fname}")
            res = requests.get(URLS["agps"].format(pack_name=pack), headers=hdr)
            res.raise_for_status()
            with requests.get(res.json()[0]["fileUrl"], stream=True) as r, open(
                fname, "wb"
            ) as f:
                shutil.copyfileobj(r.raw, f)

    def logout(self):
        data = PAYLOADS["logout"] | {"login_token": self.login_token}
        res = requests.post(URLS["logout"], data=data)
        if res.json().get("result") == "ok":
            print("[+] logged out")
        else:
            print("[!] logout failed")


# ------------------------------------------------------------------------- #
# CLI interface
# ------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser("Retrieve Huami/Amazfit cloud app_token")
    p.add_argument("-m", "--method", choices=["amazfit", "xiaomi"], default="amazfit")
    p.add_argument("-e", "--email")
    p.add_argument("-p", "--password")
    p.add_argument("--token-only", action="store_true", help="print token & exit")
    p.add_argument("-b", "--bt-keys", action="store_true", help="list BLE auth keys")
    p.add_argument("-g", "--gps", action="store_true", help="download AGPS packs")
    p.add_argument("--no-logout", action="store_true")
    args = p.parse_args()

    if args.method == "amazfit" and not args.email:
        p.error("-e/--email required for amazfit login")
    if args.method == "amazfit" and not args.password:
        args.password = getpass.getpass("Password: ")

    dev = HuamiAmazfit(args.method, args.email, args.password)
    dev.get_access_token()
    dev.login()

    # early-exit if only token requested
    if args.token_only:
        sys.exit(0)

    # BLE keys
    if args.bt_keys:
        tbl = Table(box=box.ASCII, header_style="bold")
        tbl.add_column("MAC", width=17)
        tbl.add_column("auth_key", width=40)
        for itm in dev.get_wearables():
            info = json.loads(itm["additionalInfo"])
            tbl.add_row(itm["macAddress"], "0x" + info.get("auth_key", ""))
        Console().print(tbl)

    if args.gps:
        dev.download_agps()

    if not args.no_logout:
        dev.logout()


if __name__ == "__main__":
    main() 