"""
Sends messages via LINE Messaging API (replaces deprecated LINE Notify).

Setup: see biz/setup/LINE_MESSAGING.md
Docs:  https://developers.line.biz/en/docs/messaging-api/
"""

import json
import urllib.request


def send(channel_token: str, user_id: str, message: str) -> bool:
    """
    Push a text message to a LINE user or group.

    Args:
        channel_token: Channel Access Token from LINE Developers console
        user_id:       Target userId or groupId
        message:       Text to send (up to 5,000 chars)

    Returns True on success, raises on failure.
    """
    if not channel_token:
        raise ValueError("LINE channel_token is empty. Set line.channel_token in config.yaml.")
    if not user_id:
        raise ValueError("LINE user_id is empty. Set line.user_id in config.yaml.")

    payload = json.dumps({
        "to": user_id,
        "messages": [{"type": "text", "text": message}],
    }).encode()

    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push",
        data=payload,
        headers={
            "Authorization": f"Bearer {channel_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode()
        if resp.status == 200:
            return True
        raise RuntimeError(f"LINE Messaging API returned {resp.status}: {body}")
