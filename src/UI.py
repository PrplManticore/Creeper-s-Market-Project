from typing import List, Dict, Any

from data_input import (
    get_inventory_data,
    get_market_data,
    find_item_in_inventory,
    find_item_in_market,
)

def format_item(item: Dict[str, Any]) -> str:
    if not isinstance(item, dict):
        return str(item)
    parts = []
    for key in ("item_id", "item_name", "quantity", "selling_price", "location"):
        if key in item:
            parts.append(f"{key}: {item.get(key)}")
    return " | ".join(parts) if parts else str(item)

def display_list(items: List[Dict[str, Any]], limit: int = 50) -> None:
    for i, item in enumerate(items[:limit], start=1):
        print(f"{i:3}, {format_item(item)}")
    if len(items) > limit:
        print(f"... and {len(items) - limit} more items")

def start_ui() -> None:
    # Simple interactive CLI to inspect loaded inventory and market data
    while True:
        print("\nCreeper's Market - UI")
        print("1) Show inventory data (first 50)")
        print("2) Show market data (first 50)")
        print("3) Find item by item_id")
        print("4) Quit")

        choice = input("Select option: ").strip().lower()
        if choice == "1":
            inv = get_inventory_data() or []
            print(f"\nInventory ({len(inv)} items):")
            display_list(inv)
        elif choice == "2":
            m = get_market_data() or []
            print(f"\nMarket ({len(m)} items):")
            display_list(m)
        elif choice == "3":
            raw = input("Enter item_id to find: ").strip()
            try:
                item_id = int(float(raw))
            except Exception:
                print("Invalid item_id - must be a number")
                continue
            inv_item = find_item_in_inventory(item_id)
            market_item = find_item_in_market(item_id)
            if inv_item:
                print("\nInventory match:")
                print(format_item(inv_item))
            else:
                print("No inventory match found.")
            if market_item:
                print("\nMarket match:")
                print(format_item(market_item))
            else:
                print("No market match found.")
        elif choice == "4":
            print("Exiting UI, thanks for using Creeper's Market!")
            break
        else:
            print("Unkown option. Please choose 1, 2, 3, or 4")

if __name__ == "__main__":
    start_ui()