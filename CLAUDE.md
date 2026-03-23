# OMG Coffee Shop — Business OS Manual

> This file is the brain of the entire system.
> Claude Code reads this every session. All business rules live here.
> When AI makes a mistake: add a rule below, it never repeats.

---

## 1. Business Identity

- **Shop name**: OMG Coffee
- **Type**: Specialty coffee shop (dine-in + delivery + e-commerce)
- **Currency**: TWD (New Taiwan Dollar)
- **Location**: Taiwan
- **Operating hours**: 09:00–21:00 (Mon–Sun)
- **Peak hours**: 11:00–13:00 and 17:00–19:00
- **Owner**: Solo operator — automation is essential, not optional

### Revenue Streams
| Platform  | Type            | Expected daily range |
|-----------|-----------------|----------------------|
| iChef     | Dine-in POS     | NT$6,000–15,000      |
| Uber Eats | Delivery        | NT$2,000–6,000       |
| Shopee    | E-commerce      | NT$500–5,000         |
| EasyStore | E-commerce/subs | NT$500–3,000         |

---

## 2. Income Processing Rules

### 2a. Auto-Process (no human action needed)
These are handled silently, no flag raised:
- Regular menu item orders under NT$2,000
- Standard delivery platform fees
- Recurring subscription orders (EasyStore)
- Orders from known regular customers

### 2b. Flag for Human Review — 7 Exclusion Rules

These items are **skipped from auto-processing** and queued for human review.
They appear as ⚠️ in the daily brief.

| # | Rule | Reason |
|---|------|--------|
| 1 | **Refund / negative amount** on any platform | Requires manual verification and response |
| 2 | **Single order > NT$3,000** | Unusual — confirm it's legitimate |
| 3 | **Platform API error** | Can't auto-process; data may be incomplete |
| 4 | **Bulk order, first-time buyer** | Risk check before shipping |
| 5 | **Revenue drop > 50%** vs same day last week | May indicate platform outage or issue |
| 6 | **Zero orders during peak hours** (11–13 or 17–19) | Likely a platform problem |
| 7 | **Discrepancy**: one platform silent while others active | System or account issue |

### 2c. Alert Thresholds

| Condition | Action |
|-----------|--------|
| Total revenue < NT$3,000 by 15:00 | 🔴 Alert: slow day warning |
| Total revenue > NT$20,000 in a day | 🎉 Alert: great day — celebrate! |
| Shopee unshipped orders > 5 | ⚡ Action required: ship today |
| Any platform with 0 orders for 4+ hours during operating hours | ⚠️ Check platform status |

---

## 3. Message Handling Rules

### Tone of Voice
- Warm, friendly, slightly casual — like a neighbourhood café
- Respond in the same language as the customer (zh-TW default, EN if they write English)
- Never robotic or copy-paste sounding
- Sign off as: OMG Coffee ☕

### Auto-Reply Allowed
- Opening hours enquiries → standard hours answer
- Menu/price questions → reference current menu
- Order status on Shopee/EasyStore → pull from platform

### Always Escalate to Human (never auto-reply)
- Complaints about food quality
- Refund requests
- Custom large orders (>10 items or >NT$3,000)
- Any message containing: 退款, 客訴, 過敏, allergy, complaint, refund

---

## 4. Menu Rules

### Single Source of Truth
- Master menu lives in `biz/menu/menu.yaml`
- All platform menus are generated FROM this file
- Never edit individual platform menus directly

### Update Rules
- Price changes: update `menu.yaml` → push to all platforms
- Seasonal items: use `available_from` / `available_until` fields
- Sold-out: set `in_stock: false` — this disables on all platforms automatically

### Do Not Auto-Push
- New items (require photo + description review before publishing)
- Price changes > 20% (flag for human review first)

---

## 5. Scheduling

- **Daily brief**: 07:00 every morning → sent to LINE
- **Income fetch**: 06:55 (5 min before brief generation)
- **Shopee ship reminder**: 14:00 if unshipped orders > 0
- **End-of-day summary**: 21:30 (after closing)

---

## 6. MCP Integrations

Connected external services (via Model Context Protocol):

| Service | Purpose | Status |
|---------|---------|--------|
| LINE Notify | Send daily brief + alerts | ✅ Active |
| Google Calendar | Block off events, see schedule | 🔧 Configured |
| Notion | Log decisions, store SOPs | 🔧 Configured |
| Slack | Internal ops channel | ⏳ Planned |
| freee / 會計軟體 | Financial categorisation | ⏳ Planned |

---

## 7. How to Evolve This System

### When AI makes a mistake:
```bash
python3 biz/learn.py "Shopee cash-on-delivery orders should always be flagged"
```

This appends the correction to Section 8 below AND to `biz/rules.yaml`.
Claude reads Section 8 every session — the mistake never repeats.

### When you want to add a rule manually:
Just write it in plain language below in Section 8.

---

## 8. Correction Log

> Append corrections here. Format: `YYYY-MM-DD: [what was wrong] → [new rule]`
> Claude reads this section every session and applies all rules listed.

<!-- Example:
2026-03-23: Uber Eats promo discounts were counted as negative revenue → Rule: Ignore line items with type="promotion_discount" in Uber Eats data
-->

- 2026-03-23: Uber Eats promotions should not count as negative revenue, ignore items with type=promotion_discount

---

## 9. Session Startup Checklist

When Claude Code starts a session in this repo, always:
1. Read this CLAUDE.md fully
2. Check `biz/data/review_queue.json` for unresolved flagged items
3. Report any pending items to the operator before starting new tasks
4. Apply all rules in Section 2b and Section 8 to any data processing
