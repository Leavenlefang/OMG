"""
Sends a message to LINE via LINE Notify.
Setup: https://notify-bot.line.me/  (see setup/LINE_NOTIFY.md)
"""

import urllib.request
import urllib.parse


def send(token: str, message: str) -> bool:
    """
    Send a LINE Notify message.
    Returns True on success, raises on failure.
    """
    if not token:
        raise ValueError("LINE Notify token is empty. Set line_notify.token in config.yaml.")

    data = urllib.parse.urlencode({"message": message}).encode()
    req  = urllib.request.Request(
        "https://notify-api.line.me/api/notify",
        data=data,
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode()
        if resp.status == 200:
            return True
        raise RuntimeError(f"LINE Notify returned {resp.status}: {body}")
