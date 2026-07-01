from typing import Any, Dict, List, Optional

from data_input import get_inventory_data, get_market_data, safe_int, standardize_string


def match_items_between_files(
    inventory_records: Optional[list[Dict[str, Any]]] = None,
    market_records: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Match inventory items to market items using item_id, then item_name.

    Returns a list of dictionaries with the inventory and market entries for each
    matched item. Items that do not have a counterpart are returned with a None
    value for the missing side.
    """

    inventory_records = list(
        inventory_records if inventory_records is not None else get_inventory_data() or []
    )
    market_records = list(
        market_records if market_records is not None else get_market_data() or []
    )

    market_lookup_by_id: Dict[int, Dict[str, Any]] = {}
    market_lookup_by_name: Dict[str, Dict[str, Any]] = {}

    for item in market_records:
        if not isinstance(item, dict):
            continue

        item_id = safe_int(item.get("item_id"))
        item_name = standardize_string(item.get("item_name", ""))
        if item_id:
            market_lookup_by_id[item_id] = item
        if item_name:
            market_lookup_by_name[item_name.lower()] = item

    matches: List[Dict[str, Any]] = []
    matched_market_ids = set()

    for inventory_item in inventory_records:
        if not isinstance(inventory_item, dict):
            continue

        item_id = safe_int(inventory_item.get("item_id"))
        item_name = standardize_string(inventory_item.get("item_name", ""))
        market_item: Optional[Dict[str, Any]] = None
        match_method = None

        if item_id and item_id in market_lookup_by_id:
            market_item = market_lookup_by_id[item_id]
            match_method = "item_id"
            matched_market_ids.add(item_id)
        elif item_name and item_name.lower() in market_lookup_by_name:
            market_item = market_lookup_by_name[item_name.lower()]
            match_method = "item_name"

        matches.append(
            {
                "item_id": item_id,
                "inventory_item": inventory_item,
                "market_item": market_item,
                "match_method": match_method,
            }
        )

    for market_item in market_records:
        if not isinstance(market_item, dict):
            continue

        item_id = safe_int(market_item.get("item_id"))
        if item_id and item_id in matched_market_ids:
            continue

        matches.append(
            {
                "item_id": item_id,
                "inventory_item": None,
                "market_item": market_item,
                "match_method": None,
            }
        )

    return sorted(matches, key=lambda entry: safe_int(entry.get("item_id")))