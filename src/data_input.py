from pathlib import Path
import json
import csv

inventory_data = []
market_data = []

def choose_inventory_file(directory=None):
    # Prompt the user to select an inventory file from a directory
    if directory is None:
        directory = Path(__file__).resolve().parent.parent / "data" / "raw" / "test"
    else:
        directory = Path(directory)

    if directory.is_file():
        return directory
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    inventory_files = sorted(
        [path for path in directory.glob("inventory*.*")
         if path.suffix.lower() in [".json", ".csv"]]
    )

    if not inventory_files:
        raise FileNotFoundError(f"No inventory files found in directory: {directory}")

    print("Available inventory files:")
    for index, path in enumerate(inventory_files, start=1):
        print(f"  {index}. {path.name}")

    while True:
        selection = input("select an inventory file by number or enter a file path: ").strip()
        if selection.isdigit():
            selected_index = int(selection) - 1
            if 0 <= selected_index < len(inventory_files):
                return inventory_files[selected_index]
        else:
            candidate = Path(selection)
            if not candidate.is_absolute():
                candidate = directory / candidate
            if candidate.exists() and candidate.is_file():
                return candidate
            
        print("Invalid selection. Please enter a valid number or file path.")

def load_inventory_data(file_path=None):
    global inventory_data
    if file_path is None:
        file_path = choose_inventory_file()
    else:
        file_path = Path(file_path)
        if file_path.is_dir():
            file_path = choose_inventory_file(file_path)

    if not validate_file_format(file_path):
        raise ValueError(f"Invalid file format: {file_path}")
    
    if file_path.suffix.lower() == ".json":
        with open(file_path, "r") as file:
            data = json.load(file)
            inventory_data = data["inventory"]
    elif file_path.suffix.lower() == ".csv":
        with open(file_path, "r", newline="") as file:
            reader = csv.DictReader(file)
            inventory_data = list(reader)

    else:
        raise ValueError(f"Unsupported inventory file type: {file_path.suffix}")

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

    print("Inventory Data:\n")
    for item in get_inventory_data():
        print(item)

    print("\nMarket Data:\n")
    for item in get_market_data():
        print(item)