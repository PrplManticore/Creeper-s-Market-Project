from data_input import (
    choose_inventory_file,
    load_inventory_data,
    load_market_data,
    get_inventory_data,
    get_market_data,
    validate_file_format,
)
from UI import run_app
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "raw" / "test"

inventory_file = choose_inventory_file(DATA_DIR)
load_inventory_data(inventory_file)

market_file = DATA_DIR / "market_test_data.json"
try:
    load_market_data(market_file)
    validate_file_format(market_file)
except Exception:
    pass

if __name__ == "__main__":
    run_app()