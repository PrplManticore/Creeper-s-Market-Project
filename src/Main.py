from data_input import (
    choose_inventory_file,
    load_inventory_data,
    load_market_data,
    get_inventory_data,
    get_market_data,
    validate_file_format,
)
from UI import MarketApp
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "raw" / "test"

# Let the user select which inventory file to load
try:
    inventory_file = choose_inventory_file(DATA_DIR)
    print(f"\nSelected inventory file: {inventory_file}")
    load_inventory_data(inventory_file)
    if validate_file_format(inventory_file):
        print(f"Inventory file format is valid: {inventory_file}")
except Exception as e:
    print(f"ERROR! Failed loading inventory data: {e}")
    raise

# Load the default market data file
market_file = DATA_DIR / "market_test_data.json"
try:
    load_market_data(market_file)
    if validate_file_format(market_file):
        print(f"Market file format is valid: {market_file}\n")
except Exception as e:
    print(f"ERROR! Failed loading market data: {e}")
    raise

# Use the data
inventory = get_inventory_data()
market = get_market_data()
print(f"Loaded {len(inventory)} inventory items and {len(market)} market items")

if __name__ == "__main__":
    MarketApp().run()