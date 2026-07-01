import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading
import data_input as di
from data_input import (
    choose_inventory_file,
    load_inventory_data,
    load_market_data,
    get_inventory_data,
    get_market_data,
    standardize_inventory_data,
    standardize_market_data,
    find_item_in_inventory,
    find_item_in_market,
)
import data_clean as dc
from analysis_engine import match_items_between_files
from data_input import get_inventory_data, get_market_data

class MarketApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Creeper's Market")
        self.geometry("1000x650")
        self.DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "test"
        self.PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed" / "test"
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        self.inventory_file: Optional[Path] = None
        self.market_file: Optional[Path] = self.DATA_DIR / "market_test_data.json"
        self.standardize_inventory_flag = tk.BooleanVar(value=False)
        self.standardize_market_flag = tk.BooleanVar(value=False)

        self.create_widgets()
        # Try to load default market file if present
        if self.market_file and self.market_file.exists():
            self._load_market_in_thread(self.market_file, suppress_error=True)
        self.refresh_all()


    def analyze_matches(self) -> None:
        # Ensure data loaded
        inv = get_inventory_data() or []
        mkt = get_market_data() or []
        if not inv or not mkt:
            messagebox.showwarning("Analyze Matches", "Inventory or Market data not loaded.")
            return
        
        matches = match_items_between_files()

        # Format output lines
        lines = []
        for m in matches:
            iid = m.get("item_id") or "?"
            inv_item = m.get("inventory_item")
            mkt_item = m.get("market_item")
            method = m.get("match_method") or "none"
            if inv_item and mkt_item:
                lines.append(f"{iid}: {inv_item.get('item_name', '<no name>')} — {mkt_item.get('location', '<no loc>')} (matched by {method})")
            elif inv_item:
                lines.append(f"{iid}: {inv_item.get('item_name', '<no name>')} — Market: (no match)")
            else:
                lines.append(f"{iid}: Inventory: (no match) — {mkt_item.get('item_name', '<no name>')} @ {mkt_item.get('location', '<no loc>')}")

        # Show full results in a Toplevel window (safer for long lists)
        win = tk.Toplevel(self)
        win.title("Match Results")
        txt = tk.Text(win, wrap="none", width=100, height=30)
        txt.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=txt.yview)
        scrollbar.pack(side="right", fill="y")
        txt.configure(yscrollcommand=scrollbar.set)
        txt.insert("1.0", "\n".join(lines))
        txt.configure(state="disabled")


    def _prepare_cleaned_data_file(self, input_path: Path, kind: str) -> Path:
        # Clean the selected data file and save it to the processed/test folder.
        input_path = Path(input_path)
        records = dc.load_data(input_path)

        if kind == "inventory":
            records = dc.remove_duplicate_records(records, key_fields=["item_id"])
            records = dc.handle_missing_values(
                records,
                fill_defaults={"item_name": "", "quantity": 0},
                required_fields=["item_id"],
                drop_missing=True,
            )
            records = dc.filter_irrelevant_data(
                records,
                allowed_fields=["item_id", "item_name", "quantity"],
            )
            root_key = "inventory"
        elif kind == "market":
            records = dc.remove_duplicate_records(records, key_fields=["item_id"])
            records = dc.handle_missing_values(
                records,
                fill_defaults={"item_name": "", "selling_price": 0, "quantity": 0, "location": ""},
                required_fields=["item_id"],
                drop_missing=True,
            )
            records = dc.filter_irrelevant_data(
                records,
                allowed_fields=["item_id", "item_name", "selling_price", "quantity", "location"],
            )
            root_key = "market_data"
        else:
            raise ValueError(f"Unsupported data kind: {kind}")
        
        output_path = self.PROCESSED_DIR / f"{input_path.stem}_cleaned.json"
        dc.save_json(output_path, records, root_key=root_key)
        return output_path


    def create_widgets(self) -> None:
        header = ttk.Label(self, text="Creeper's Market", font=("Segoe UI", 18, "bold"))
        header.pack(pady=8)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=8)

        ttk.Button(btn_frame, text="Open Inventory File...", command=self.open_inventory_file).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Auto-select Inventory", command=self.auto_select_inventory).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Open Market File...", command=self.open_market_file).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_all).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Analyze Matches", command=self.analyze_matches).pack(side="left", padx=4)
        
        ttk.Checkbutton(btn_frame, text="Standardize Inventory", variable=self.standardize_inventory_flag, command=self.on_standardize_toggled).pack(side="left", padx=8)
        ttk.Checkbutton(btn_frame, text="Standardize Market", variable=self.standardize_market_flag, command=self.on_standardize_toggled).pack(side="left", padx=8)

        # Paned lists
        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=8, pady=8)

        inv_frame = ttk.Labelframe(panes, text="Inventory")
        mkt_frame = ttk.Labelframe(panes, text="Market")
        panes.add(inv_frame, weight=1)
        panes.add(mkt_frame, weight=1)

        # Inventory listbox and scrollbar
        self.inv_list = tk.Listbox(inv_frame, activestyle="none")
        inv_scroll = ttk.Scrollbar(inv_frame, orient="vertical", command=self.inv_list.yview)
        self.inv_list.configure(yscrollcommand=inv_scroll.set)
        self.inv_list.pack(side="left", fill="both", expand=True)
        inv_scroll.pack(side="right", fill="y")

        # Market listbox and scrollbar
        self.mkt_list = tk.Listbox(mkt_frame, activestyle="none")
        mkt_scroll = ttk.Scrollbar(mkt_frame, orient="vertical", command=self.mkt_list.yview)
        self.mkt_list.configure(yscrollcommand=mkt_scroll.set)
        self.mkt_list.pack(side="left", fill="both", expand=True)
        mkt_scroll.pack(side="right", fill="y")

        # Search area
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(search_frame, text="Search item_id:").pack(side="left", padx=(0, 6))
        self.search_entry = ttk.Entry(search_frame, width=12)
        self.search_entry.pack(side="left")
        ttk.Button(search_frame, text="Find", command=self.search_item).pack(side="left", padx=6)

        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, anchor="w").pack(fill="x", padx=8, pady=(0, 8))


    def format_item(self, item: Dict[str, Any]) -> str:
        # Format a record into a readable string for listbox display.
        if not isinstance(item, dict):
            return str(item)
        keys = ("item_id", "item_name", "quantity", "selling_price", "location")
        parts = [f"{k}: {item.get(k)}" for k in keys if k in item]
        return " | ".join(parts) if parts else str(item)
    

    def _load_inventory_in_thread(self, path: Path) -> None:
        # Load inventory file in a background threadto keep UI responsive.
        def load():
            try:
                p = Path(path)
                load_path = self._prepare_cleaned_data_file(p, "inventory")

                load_inventory_data(load_path)
                self.inventory_file = load_path
                if self.standardize_inventory_flag.get():
                    self.apply_inventory_standardization()
                self.after(0, self.refresh_inventory_list)
                self.after(0, lambda: self.status.set(f"Loaded inventory: {load_path.name}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Load Error", f"Failed to load inventory:\n{e}"))
                self.after(0, lambda: self.status.set("Failed to load inventory"))
                
        thread = threading.Thread(target=load, daemon=True)
        thread.start()


    def _load_market_in_thread(self, path: Path, suppress_error: bool = False) -> None:
        # Load market file in a background thread to keep UI responsive.
        def load():
            try:
                p = Path(path)
                load_path = self._prepare_cleaned_data_file(p, "market")

                load_market_data(load_path)
                self.market_file = load_path
                if self.standardize_market_flag.get():
                    self.apply_market_standardization()
                self.after(0, self.refresh_market_list)
                self.after(0, lambda: self.status.set(f"Loaded market: {load_path.name}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Load Error", f"Failed to load market:\n{e}"))
                self.after(0, lambda: self.status.set("Failed to load market"))

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def open_inventory_file(self) -> None:
        # Prompt the user to choose an inventory file and start loading it.
        path = filedialog.askopenfilename(
            title="Select Inventory File",
            initialdir=self.DATA_DIR,
            filetypes=[("JSON/CSV/Lua", "*.json;*.csv;*.lua"), ("All files", "*.*")]
        )
        if not path:
            return
        
        try:
            input_path = Path(path)
            cleaned_path = input_path

            self.status.set("Loading inventory...")
            self._load_inventory_in_thread(cleaned_path)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load inventory:\n{e}")
            self.status.set("Failed to load inventory")


    def auto_select_inventory(self) -> None:
        # Let the user pick an inventory file from the default data directory.
        inventory_files = sorted(
            [p for p in self.DATA_DIR.glob("inventory*.*") if p.suffix.lower() in [".json", ".csv", ".lua"]]
        )

        if not inventory_files:
            messagebox.showwarning("Auto-select Inventory", "No inventory files found.")
            return

        options = "\n".join(
            f"{index}. {path.name}" for index, path in enumerate(inventory_files, start=1)
        )
        selection = simpledialog.askinteger(
            "Auto-select Inventory",
            f"Select inventory file number:\n\n{options}",
            parent=self,
            minvalue=1,
            maxvalue=len(inventory_files),
        )

        if selection is None:
            return
        
        selected_path = inventory_files[selection - 1]
        self.status.set("Loading inventory...")
        self._load_inventory_in_thread(selected_path)


    def open_market_file(self) -> None:
        # Prompt the user to choose a market file and load it asynchronously.
        path = filedialog.askopenfilename(
            title="Select Market File",
            initialdir=self.DATA_DIR,
            filetypes=[("JSON/CSV/Lua", "*.json;*.csv;*.lua"), ("All files", "*.*")]
        )
        if not path:
            return
        
        try:
            input_path = Path(path)
            self.status.set("Loading market...")
            self._load_market_in_thread(input_path)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load market:\n{e}")
            self.status.set("Failed to load market")


    def apply_inventory_standardization(self) -> None:
        # Standardize the loaded inventory records and refresh the display.
        try:
            inv = get_inventory_data() or []
            standardized = standardize_inventory_data(inv)
            di.inventory_data = standardized
            self.status.set("Inventory standardized")
            self.refresh_inventory_list()
        except Exception as e:
            messagebox.showwarning("Standardize Error", f"Failed to standardize inventory: {e}")


    def apply_market_standardization(self) -> None:
        # Standardize the loaded market records and refresh the display.
        try:
            mkt = get_market_data() or []
            standardized = standardize_market_data(mkt)
            di.market_data = standardized
            self.status.set("Market standardized")
            self.refresh_market_list()
        except Exception as e:
            messagebox.showwarning("Standardize Error", f"Failed to standardize market: {e}")


    def on_standardize_toggled(self) -> None:
        # Apply or remove standardization based on flags
        if self.standardize_inventory_flag.get():
            self.apply_inventory_standardization()
        else:
            # Reload original file if available to undo standardization
            def reload():
                try:
                    load_inventory_data(self.inventory_file)
                    self.after(0, self.refresh_inventory_list)
                    self.after(0, lambda: self.status.set("Inventory reloaded (standaridize off)"))
                except Exception:
                    pass
            thread = threading.Thread(target=reload, daemon=True)
            thread.start()

        if self.standardize_market_flag.get():
            self.apply_market_standardization()
        else:
            if self.market_file and self.market_file.exists():
                def reload():
                    try:
                        load_market_data(self.market_file)
                        self.after(0, self.refresh_market_list)
                        self.after(0, lambda: self.status.set("Market reloaded (standardize off)"))
                    except Exception:
                        pass
                thread = threading.Thread(target=reload, daemon=True)
                thread.start()

    def refresh_inventory_list(self) -> None:
        # Refresh the inventory listbox with the currently loaded inventory records.
        items = get_inventory_data() or []
        self.inv_list.delete(0, tk.END)
        for it in items[:500]:
            self.inv_list.insert(tk.END, self.format_item(it))
        self.status.set(f"Inventory: {len(items)} items")


    def refresh_market_list(self) -> None:
        # Refresh the market listbox with the currently loaded market records.
        items = get_market_data() or []
        self.mkt_list.delete(0, tk.END)
        for it in items[:500]:
            self.mkt_list.insert(tk.END, self.format_item(it))


    def refresh_all(self) -> None:
        # Reload market data from disk if available, then refresh both lists.
        if self.market_file and self.market_file.exists():
            def load():
                try:
                    load_market_data(self.market_file)
                    self.after(0, self.refresh_market_list)
                except Exception:
                    pass
                thread = threading.Thread(target=load, daemon=True)
                thread.start()
        self.refresh_inventory_list()
        self.refresh_market_list()


    def search_item(self) -> None:
        # Search inventory and market data for a given item_id and show results.
        raw = self.search_entry.get().strip()
        if not raw:
            messagebox.showinfo("Search", "Enter item_id")
            return
        try:
            item_id = int(float(raw))
        except Exception:
            messagebox.showerror("Search", "item_id must be a number")
            return
        
        inv_match = find_item_in_inventory(item_id)
        mkt_match = find_item_in_market(item_id)
        parts=[]
        if inv_match:
            parts.append("Inventory:\n" + self.format_item(inv_match))
        else:
            parts.append("Inventory: (no match)")
        if mkt_match:
            parts.append("Market:\n" + self.format_item(mkt_match))
        else:
            parts.append("Market: (no match)")

        messagebox.showinfo("Search Results", "\n\n".join(parts))


def run_app() -> None:
    app = MarketApp()
    app.mainloop()

if __name__ == "__main__":
    run_app()