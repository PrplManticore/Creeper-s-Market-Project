from pathlib import Path
import re
import json
import csv
from typing import Optional, Union
import shutil

def load_data(file_path):
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        # Load JSON content from file
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            # if JSON wraps the list in a root key, pick the first list
            lists = [value for value in data.values() if isinstance(value, list)]
            if len(lists) == 1:
                return lists[0]
            if isinstance(data.get("inventory_data"), list):
                return data["inventory_data"]
            if isinstance(data.get("market_data"), list):
                return data["market_data"]
        if isinstance(data, list):
            return data
        raise ValueError(f"Unsupported JSON structure in {file_path}")
    
    if suffix == ".csv":
        # Load CSV rows as a list of dicts
        with file_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
        
    if suffix == ".lua":
        # Convert Lua table syntax to JSON-like Python data
        text = file_path.read_text(encoding="utf-8")
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 <+ start:
            raise ValueError("No Lua table found in input")
        
        table_text = text[start:end + 1]
        table_text = re.sub(r"(\b[a-zA-Z_][\w]*)\s=", r'"\1":', table_text)
        table_text = table_text.replace("nil", "null")
        table_text = re.sub(r",\s*([}\]])", r"\1", table_text)

        return json.loads(table_text)
        
    raise ValueError(f"Unsupported file format: {file_path.suffix}")


def save_json(output_path, records, root_key=None):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = records
    if root_key:
        payload = {root_key: records}

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def save_csv(output_path, records):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        raise ValueError("No records to write to CSV.")
    
    fieldnames = list(records[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def convert_file(input_path, output_path=None, output_format=None, root_key=None):
    input_path = Path(input_path)
    data = load_data(input_path)

    if output_format is None:
        # Default format flips JSON->CSV or any other input->JSON
        output_format = "csv" if input_path.suffix.lower() == ".json" else "json"
    
    if output_path is None:
        output_path = input_path.with_suffix(f".{output_format}")

    if output_format.lower() == "json":
        save_json(output_path, data, root_key=root_key)
    elif output_format.lower() == "csv":
        save_csv(output_path, data)
    else:
        raise ValueError(f"Unsupported target format: {output_format}")
    
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert between JSON and CSV data files."
    )
    parser.add_argument("input", help="Input file path (.json or .csv)")
    parser.add_argument(
        "-o", "--output", help="Output file path. If "
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv"],
        help="Target format. If omitted, flips the input type.",
    )
    parser.add_argument(
        "--root-key",
        help="When writing JSON, wrap records under this root key (e.g. inventory_data or market_data)"
    )

    args = parser.parse_args()
    output_file = convert_file(
        args.input, output_path=args.output, output_format=args.format, root_key=args.root_key
    )
    print(f"Converted {args.input} -> {output_file}")