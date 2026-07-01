import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_input import load_inventory_data, load_market_data
from analysis_engine import match_items_between_files


def test_matching_item_by_id_from_loaded_files():
    inventory_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "test" / "inventory_test_data_cleaned.json"
    market_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "test" / "market_test_data_cleaned.json"

    load_inventory_data(inventory_path)
    load_market_data(market_path)

    matches = match_items_between_files()
    item_1004 = next((item for item in matches if item["item_id"] == 1004), None)

    assert item_1004 is not None
    assert item_1004["inventory_item"]["item_name"] == "Kuta"
    assert item_1004["market_item"]["location"] == "Deshaan"
