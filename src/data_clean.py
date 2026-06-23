from pathlib import Path
import re
import json
import csv
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union
import shutil

Record = Dict[str, Any]

def remove_duplicate_records(
    records: Sequence[Record],
    key_fields: Optional[Sequence[str]] = None,
    preserve_first: bool = True,
) -> List[Record]:
    """
    Remove duplicate records from a list of dects.
    If key_fields is provided, duplicates are detected by those field values.
    Otherwise the entire record dict is used.
    """
    seen = set()
    deduped: List[Record] = []

    for record in records:
        if key_fields:
            key=tuple(record.get(field) for field in key_fields)
        else:
            key = tuple(sorted(record.items()))
        if key in seen:
            if not preserve_first:
                # Replace last seen record with current one
                deduped = [r for r in deduped if tuple(sorted(r.items())) != key]
                deduped.append(record)
            continue
        seen.add(key)
        deduped.append(record)

    return deduped


def handle_missing_values(
    records: Sequence[Record],
    fill_defaults: Optional[Dict[str, Any]] = None,
    fill_value: Any = "",
    required_fields: Optional[Sequence[str]] = None,
    drop_missing: bool = False,
) -> List[Record]:
    """
    Fill or drop missing values in records.
    - fill_defaults: dict of field->value to fill only those fields.
    - fill_value: fallback value for any missing field.
    - required_fields: list of fields that must exist and not be empty.
    - drop_missing: if True, remove records missing any required field.
    """
    fill_defaults = fill_defaults or {}
    cleaned: List[Record] = []

    for record in records:
        record = dict(record)
        for field, default in fill_defaults.items():
            if record.get(field) in (None, "", []):
                record[field] = default

        if fill_value is not None:
            for field, value in list(record.items()):
                if value in (None, ""):
                    record[field] = fill_value

        if required_fields:
            missing = any(record.get(field) in (None, "") for field in required_fields)
            if missing:
                if drop_missing:
                    continue
                # if not dropping, ensure required fields are filled
                for field in required_fields:
                    if record.get(field) in (None, ""):
                        record[field] = fill_defaults.get(field, fill_value)

        cleaned.append(record)

    return cleaned


def filter_irrelevant_data(
    records: Sequence[Record],
    allowed_fields: Optional[Sequence[str]] = None,
    exclude_fields: Optional[Sequence[str]] = None,
    predicate: Optional[callable] = None,
) -> List[Record]:
    """
    Keep only relevant records and optionally prune irrelevant fields.
    - allowed_fields: whitelist of field names to preserve in each record.
    - exclude_fields: blacklist of fields to remove from each record.
    - predicate: function(record) -> bool to decide whether to keep a record.
    """
    filtered: List[Record] = []

    for record in records:
        if predicate is not None and not predicate(record):
            continue

        if allowed_fields is not None:
            record = {k: v for k, v in record.items() if k in allowed_fields}
        elif exclude_fields is not None:
            record = {k: v for k, v in record.items() if k not in exclude_fields}

        filtered.append(record)
    
    return filtered


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