from pathlib import Path
import json
import csv

inventory_data = []
market_data = []

def load_inventory_data(file_path):
    global inventory_data
    with open(file_path, 'r') as file:
        data = json.load(file)
        inventory_data = data["inventory"]

def load_market_data(file_path):
    global market_data
    with open(file_path, 'r') as file:
        data = json.load(file)
        market_data = data["market_data"]

def get_inventory_data():
    return inventory_data

def get_market_data():
    return market_data

def safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default
    
def standardize_string(value):
    # Checks that string is not empty and capitalizes the first letter of each word
    value = str(value).strip()
    if not value:
        return ""
    
    parts = []
    for token in value.split():
        if "'" in token:
            parts.append("'".join([part.capitalize() for part in token.split("'")]))
        elif "-" in token:
            parts.append("-".join([part.capitalize() for part in token.split("-")]))
        else:
            parts.append(token.capitalize())

    return " ".join(parts)

def standardize_inventory_data(raw_inventory):
    standardized = []
    for item in raw_inventory:
        standardized.append({
            "item_id": safe_int(item.get("item_id")),
            "item_name": standardize_string(item.get("item_name", "")),
            "quantity": safe_int(item.get("quantity", 0)),
        })
    return standardized

def standardize_market_data(raw_market):
    standardized = []
    for item in raw_market:
        standardized.append({
            "item_id": safe_int(item.get("item_id")),
            "item_name": standardize_string(item.get("item_name", "")),
            "selling_price": safe_int(item.get("selling_price", 0)),
            "quantity": safe_int(item.get("quantity", 0)),
            "location": standardize_string(item.get("location", ""))
        })
    return standardized

def validate_file_format(file_path):
    # Validate that the file exists and is in the correct format (JSON or CSV)
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.stat().st_size == 0:
        raise ValueError(f"File is empty: {file_path}")

    file_extension = file_path.suffix.lower()

    if file_extension not in [".json", ".csv"]:
        return False
    
    try:
        if file_extension == ".json":
            with open(file_path, "r") as file:
                json.load(file)
        elif file_extension == ".csv":
            with open(file_path, "r") as file:
                next(csv.reader(file))
    except (json.JSONDecodeError, StopIteration, Exception):
        return False
    
    return True

def find_item_in_inventory(item_id):
    # Find an item in the inventory data by its item_id
    for item in inventory_data:
        if item['item_id'] == item_id:
            return item
    return None

def find_item_in_market(item_id):
    # Find an item in the market data by its item_id
    for item in market_data:
        if item['item_id'] == item_id:
            return item
    return None

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR.parent / "data" / "raw" / "test"

    load_inventory_data(DATA_DIR / "inventory_test_data.json")
    validate_file_format(DATA_DIR / "inventory_test_data.json")
    load_market_data(DATA_DIR / "market_test_data.json")
    validate_file_format(DATA_DIR / "market_test_data.json")
    print("Inventory Data:\n") 
    for item in get_inventory_data():
        print(item)
    if validate_file_format(DATA_DIR / "inventory_test_data.json"):
        print(f"\nFile format for {DATA_DIR / 'inventory_test_data.json'} is valid.\n")
    print("Market Data:\n")
    for item in get_market_data():
        print(item)
    if validate_file_format(DATA_DIR / "market_test_data.json"):
        print(f"\nFile format for {DATA_DIR / 'market_test_data.json'} is valid.\n")