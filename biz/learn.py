#!/usr/bin/env python3
"""
learn.py — The self-evolution feedback loop.

When AI makes a mistake or you want to add a business rule:
  python3 biz/learn.py "Uber Eats promo discounts should not count as revenue"

This does three things:
  1. Appends the correction to CLAUDE.md Section 8 (so Claude reads it next session)
  2. Appends to biz/rules.yaml corrections list (for programmatic use)
  3. Marks relevant review_queue items as resolved (if rule_id given)

Usage:
  python3 biz/learn.py "your correction here"
  python3 biz/learn.py --resolve EX2 Shopee
  python3 biz/learn.py --list                  # show open review queue
"""

import argparse
import json
import sys
from datetime import datetime, date
from pathlib import Path

import yaml

REPO_ROOT    = Path(__file__).parent.parent
CLAUDE_MD    = REPO_ROOT / "CLAUDE.md"
RULES_YAML   = Path(__file__).parent / "rules.yaml"
REVIEW_QUEUE = Path(__file__).parent / "data" / "review_queue.json"


def append_to_claude_md(correction: str):
    """Append a correction to CLAUDE.md Section 8."""
    today = date.today().isoformat()
    entry = f"\n- {today}: {correction}"

    content = CLAUDE_MD.read_text()

    # Find the correction log section and append before the closing comment
    marker = "_(No corrections yet — this is a fresh system.)_"
    if marker in content:
        content = content.replace(marker, entry.strip())
    else:
        # Find the end of Section 8 (before Section 9 or end of file)
        section9 = "\n## 9."
        if section9 in content:
            content = content.replace(section9, f"{entry}\n{section9}")
        else:
            content += entry

    CLAUDE_MD.write_text(content)
    print(f"✅ Added to CLAUDE.md Section 8:\n   {today}: {correction}")


def append_to_rules_yaml(correction: str):
    """Append to the corrections list in rules.yaml."""
    today = date.today().isoformat()

    with open(RULES_YAML) as f:
        rules = yaml.safe_load(f) or {}

    corrections = rules.get("corrections", [])
    if corrections is None:
        corrections = []

    corrections.append({
        "date":        today,
        "description": correction,
        "rule_added":  "pending manual rule update",
    })
    rules["corrections"] = corrections

    with open(RULES_YAML, "w") as f:
        yaml.dump(rules, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ Added to biz/rules.yaml corrections log")


def list_queue():
    """Print all unresolved items in the review queue."""
    if not REVIEW_QUEUE.exists():
        print("📋 Review queue is empty.")
        return

    with open(REVIEW_QUEUE) as f:
        items = json.load(f)

    unresolved = [i for i in items if not i.get("resolved")]
    if not unresolved:
        print("📋 No unresolved items. All clear!")
        return

    print(f"📋 Review queue — {len(unresolved)} unresolved item(s):\n")
    for item in unresolved:
        severity_icon = {"red": "🔴", "yellow": "⚠️", "celebrate": "🎉"}.get(item.get("severity"), "•")
        print(f"  {severity_icon} [{item['rule_id']}] {item['platform']} — {item['message']}")
        print(f"     Date: {item.get('date', '?')}")
        print()

    print("To resolve an item:")
    print("  python3 biz/learn.py --resolve <RULE_ID> <PLATFORM>")
    print()
    print("To add a rule so it doesn't happen again:")
    print('  python3 biz/learn.py "your correction here"')


def resolve_item(rule_id: str, platform: str):
    """Mark a review queue item as resolved."""
    if not REVIEW_QUEUE.exists():
        print("⚠️  Review queue is empty.")
        return

    with open(REVIEW_QUEUE) as f:
        items = json.load(f)

    found = False
    for item in items:
        if item["rule_id"] == rule_id and item["platform"] == platform and not item.get("resolved"):
            item["resolved"]    = True
            item["resolved_at"] = datetime.now().isoformat()
            found = True

    if not found:
        print(f"⚠️  No unresolved item found for rule_id={rule_id} platform={platform}")
        return

    with open(REVIEW_QUEUE, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    print(f"✅ Resolved: [{rule_id}] {platform}")


def main():
    parser = argparse.ArgumentParser(
        description="Add business rules / corrections to CLAUDE.md and rules.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 biz/learn.py "Uber Eats promotions should not count as negative revenue"
  python3 biz/learn.py --list
  python3 biz/learn.py --resolve EX2 Shopee
        """,
    )
    parser.add_argument("correction", nargs="?", help="The correction / new rule in plain language")
    parser.add_argument("--list",    "-l", action="store_true", help="List all unresolved review queue items")
    parser.add_argument("--resolve", "-r", nargs=2, metavar=("RULE_ID", "PLATFORM"),
                        help="Mark a review queue item as resolved")

    args = parser.parse_args()

    if args.list:
        list_queue()
        return

    if args.resolve:
        rule_id, platform = args.resolve
        resolve_item(rule_id, platform)
        return

    if not args.correction:
        parser.print_help()
        sys.exit(1)

    correction = args.correction.strip()
    print()
    append_to_claude_md(correction)
    append_to_rules_yaml(correction)
    print()
    print("Claude will apply this rule in the next session.")
    print("To also update the code-level rules, edit biz/rules.yaml directly.")


if __name__ == "__main__":
    main()
