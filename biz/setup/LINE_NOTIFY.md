# Setting Up LINE Notify (5 minutes)

LINE Notify lets this system send messages directly to your LINE account.
It's free and takes about 5 minutes.

---

## Step 1 — Get your token

1. Open this URL in your browser:
   **https://notify-bot.line.me/**

2. Click **Log in** (top right) → log in with your LINE account

3. Click your profile name (top right) → **My page**

4. Scroll down to **Generate token**

5. Click **Generate token**

6. In the popup:
   - **Token name**: `OMG Daily Brief` (or anything you want)
   - **Chat**: choose **Send to yourself** (sends to your personal LINE chat)
   - Or choose a group chat if you want the brief in a group

7. Click **Generate**

8. **Copy the token** — it looks like: `AbCdEfGhIjKlMnOpQr12345`
   ⚠️ You only see it once. Copy it now.

---

## Step 2 — Add token to config

Open `biz/config.yaml` and paste your token:

```yaml
line_notify:
  token: "AbCdEfGhIjKlMnOpQr12345"   # ← your token here
```

---

## Step 3 — Test it

```bash
cd /path/to/OMG
python3 biz/run_daily.py --preview     # prints brief, no LINE send
python3 biz/run_daily.py               # fetches data AND sends to LINE
```

You should receive a LINE message within a few seconds.

---

## Step 4 — Install the daily scheduler (Mac)

```bash
bash biz/setup/install_mac.sh
```

That's it. Every morning at 7:00am you'll get your brief in LINE.

---

## Troubleshooting

**"Invalid access token"**
→ Check that you copied the full token with no extra spaces.

**No LINE message received**
→ Run `python3 biz/run_daily.py` and check for error output.
→ Make sure your Mac is awake at 7am, or run it manually after waking up.

**Want to change the time?**
```bash
bash biz/setup/install_mac.sh --hour 8   # switch to 8am
```
