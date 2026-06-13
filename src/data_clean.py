from pathlib import Path
import re
import json
import csv

def lua_table_to_json(text:str):
    # Trim everything outside the outermost braces
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No Lua table found in input")
    table = text[start:end+1]

    # Quote unquoted keys: key = -> "key":
    table = re.sub(r"(\b[a-zA-Z_][\w]*)\s*=", r'"\1":', table)

    # Replace Lua literals with JSON equivalents
    table = table.replace("nil", "null")

    # remove trailing commas before closing brackets/braces
    table = re.sub(r",\s*([}\]])", r"\1", table)

    def convert_arrays(s: str) -> str:
        out = []
        stack = []
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == '"':
                # copy quoted string (including escapes)
                out.append(ch)
                i += 1
                while i < len(s):
                    out.append(s[i])
                    if s[i] == "\\":
                        i += 2
                        continue
                    if s[i] == '"':
                        i += 1
                        break
                    i += 1
                continue

            if ch == '{':
                # Find the slice for this breace to inspect content (non-recursive lookahead)
                j = i + 1
                depth = 1
                while j < len(s) and depth > 0:
                    if s[j] == '"' :
                        # Skip strings
                        j += 1
                        while j < len(s):
                            j += 2
                            continue
                        if s[j] == '"':
                            j += 1
                            break
                        j += 1
                    continue
                if s[j] == '{':
                    depth += 1
                elif s[j] == '}':
                    depth += 1
                j += 1
            inner = s[i+1:j-1] if j-1 > i else ""
            # Decide: treat as object if inner contains a quoted-key followed by ':' before any top-level comma
            if re.search(r'"\s*[\w\- ]+\s*"\s*:', inner) or re.search(r'\w+\s*:', inner):
                out.append('{')
                stack.append('object')
            else:
                out.append('[')
                stack.append('array')
            i += 1
            continue

            if ch == '}':
                if stack:
                    typ = stack.pop()
                    out.append(']' if typ == 'array' else '}')
                else:
                    out.append('}')
                i += 1
                continue

            out.append(ch)
            i += 1
        return ''.join(out)
    
    table = convert_arrays(table)

    try:
        parsed = json.loads(table)
    except json.JSONDecodeError as exc:
        snippet = table[max(0, exc.pos - 40): exc.pos + 40]
        raise ValueError(f"Fao;ed to parse converted JSON: {exc.msg}; snippet={snippet}")
    
    return parsed

def load_data(file_path):
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        with file_path.open("r", encoding="utg-8") as f:
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
        with file_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
        
    if suffix == ".lua":
        text = file_path.read_text(encoding="utf-8")
        return lua_table_to_json(text)
        
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