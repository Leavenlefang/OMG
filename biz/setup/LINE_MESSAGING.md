# Setting Up LINE Messaging API (~10 minutes)

LINE Notify was shut down on 2025-03-31. This system now uses the
**LINE Messaging API**, which is free for up to 200 messages/month.

---

## Step 1 — Create a LINE Official Account

1. Go to **https://manager.line.biz/**
2. Log in with your LINE account
3. Click **Create** → fill in account name (e.g. `OMG Coffee Bot`) and category
4. Select the **Free** plan

---

## Step 2 — Enable Messaging API

1. Inside your new account, go to **Settings → Messaging API**
2. Click **Enable Messaging API**
3. Choose or create a **LINE Developers provider** (just use your name)
4. Confirm → your channel is created

---

## Step 3 — Get your Channel Access Token

1. Go to **https://developers.line.biz/console/**
2. Select your provider → your channel
3. Click the **Messaging API** tab
4. Scroll down to **Channel access token** → click **Issue**
5. Copy the long token (starts with something like `eyJhbGci...`)

---

## Step 4 — Get your User ID

You need to tell the bot *who* to send messages to (you).

1. In the LINE Developers console → **Messaging API** tab
2. Find **Your user ID** under "Bot information" — it starts with `U` (e.g. `U1234abcd...`)
   - If you don't see it: open LINE app → find your Official Account → send it any message
   - Then in the console go to **Webhook** → the message log will show your userId

---

## Step 5 — Add to config

Open `biz/config.yaml` and fill in both values:

```yaml
line:
  channel_token: "eyJhbGci..."   # ← your Channel Access Token
  user_id: "U1234abcd..."        # ← your User ID
```

---

## Step 6 — Make sure you're a "Friend"

The bot can only push messages to users who have added it as a friend.

1. In LINE Developers console → **Messaging API** tab
2. Find the **QR code** for your bot
3. Scan it with your LINE app to add it as a friend

---

## Step 7 — Test it

```bash
python3 biz/run_daily.py --eod     # sends EOD summary to LINE
```

You should receive the message within a few seconds.

---

## Troubleshooting

**"Invalid channel access token"**
→ Re-issue the token in the console and re-paste it.

**"The user has not agreed to the Official Account Terms of Service"**
→ Make sure you've added the bot as a friend (Step 6).

**"403 Forbidden"**
→ Check that your channel is published (not in development mode).
→ In Developers console → Basic settings → scroll to **Channel status** → set to **Published**.
