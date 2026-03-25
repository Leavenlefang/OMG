#!/usr/bin/env python3
"""
Menu CLI — manage the OMG Coffee menu from the command line.

Usage:
  python3 -m biz.menu.cli list                    # list all items
  python3 -m biz.menu.cli list --platform Shopee   # items for a specific platform
  python3 -m biz.menu.cli status                   # quick summary
  python3 -m biz.menu.cli soldout <item-id>        # mark item as sold out
  python3 -m biz.menu.cli restock <item-id>        # mark item back in stock
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from biz.menu import engine


def cmd_list(args):
    if args.platform:
        items = engine.get_platform_menu(args.platform)
        print(f"\n📋 {args.platform} menu ({len(items)} items):\n")
    else:
        items = [i for i in engine.load_menu() if i.is_available()]
        print(f"\n📋 All available items ({len(items)}):\n")

    for item in items:
        stock = "✅" if item.in_stock else "❌"
        seasonal = " 🌸" if "seasonal" in item.tags else ""
        options_str = ""
        if item.options:
            opts = ", ".join(f"{o['name']} +{o['price_delta']}" for o in item.options)
            options_str = f"  ({opts})"
        print(f"  {stock} {item.name_zh} ({item.name_en}) — NT${item.base_price}{options_str}{seasonal}")
        print(f"     ID: {item.id} | Platforms: {', '.join(item.platforms)}")


def cmd_status(args):
    print(engine.summary())


def cmd_soldout(args):
    engine.set_stock(args.item_id, False)
    print(f"❌ {args.item_id} marked as sold out (all platforms)")


def cmd_restock(args):
    engine.set_stock(args.item_id, True)
    print(f"✅ {args.item_id} restocked (all platforms)")


def main():
    parser = argparse.ArgumentParser(description="OMG Coffee Menu CLI")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="List menu items")
    p_list.add_argument("--platform", help="Filter by platform")

    sub.add_parser("status", help="Quick summary")

    p_sold = sub.add_parser("soldout", help="Mark item as sold out")
    p_sold.add_argument("item_id", help="Item ID to mark sold out")

    p_restock = sub.add_parser("restock", help="Mark item back in stock")
    p_restock.add_argument("item_id", help="Item ID to restock")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    {"list": cmd_list, "status": cmd_status, "soldout": cmd_soldout, "restock": cmd_restock}[args.command](args)


if __name__ == "__main__":
    main()
