import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import List, Dict, Any

from data_input import (
    get_inventory_data,
    get_market_data,
    find_item_in_inventory,
    find_item_in_market,
    load_inventory_data,
    load_market_data,
    validate_file_format,
)

class MarketApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Creeper's Market")
        self.geometry("900x600")
        self.DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "test"
        self.inventory_file = None
        self.market_file = self.DATA_DIR / "market_test_data.json"

        self.create_widgets()
        self.refresh_inventory_list()
        self.refresh_market_list()

    def create_widgets(self) -> None:
        header = ttk.Label(self, text="Creeper's Market", font=("Arial", 18, "bold"))
        header.pack(pady=10)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=12)

        self.load_inventory_button = ttk.Button(
            button_frame,
            text="Load Market File...",
            command=self.load_market_file,
        )
        self.load_inventory_button.pack(side="left", padx=4)

        self.refresh_button = ttk.Button(
            button_frame,
            text="Refresh Data",
            command=self.refresh_all,
        )
        self.refresh_button.pack(side="left", padx=4)

        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=12, pady=10)

        inventory_frame = ttk.Labelframe(panes, text="Inventory")
        market_frame = ttk.Labelframe(panes, text="Market")
        panes.add(inventory_frame, weight=1)
        panes.add(market_frame, weight=1)

        self.inventory_listbox = tk.Listbox(inventory_frame, activestyle="none")
        inv_scroll = ttk.Scrollbar(inventory_frame, orient="vertical", command=self.inventory_listbox.yview)
        self.inventory_listbox.configure(yscrollcommand=inv_scroll.set)
        self.inventory_listbox.pack(side="left", fill="both", expand=True)
        inv_scroll.pack(side="right", fill="y")

        self.market_listbox = tk.Listbox(market_frame, activestyle="none")
        mkt_scroll = ttk.Scrollbar(market_frame, orient="vertical", command=self.market_listbox.yview)
        self.market_listbox.configure(yscrollcommand=mkt_scroll.set)
        self.market_listbox.pack(side="left", fill="both", expand=True)
        mkt_scroll.pack(side="right", fill="y")

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=12, pady=(0, 10))

        ttk.Label(search_frame, text="Search item_id:").pack(side="left", padx=(0, 8))
        self.search_entry = ttk.Entry(search_frame, width=12)
        self.search_entry.pack(side="left")
        self.search_button = ttk.Button(search_frame, text="Find", command=self.search_item)
        self.search_button.pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="Load an inventory file, then inspect the data.")
        self.status_label = ttk.Label(self, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill="x", padx=12)

    def format_item(self, item: Dict[str, Any]) -> str:
        if not isinstance(item, dict):
            return str(item)
        keys = ("item_id", "item_name", "quantity", "selling_price", "location")
        parts = [f"{key}: {item.get(key)}" for key in keys if key in item]
        return " | ".join(parts) if parts else str(item)
    
    def load_inventory_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select inventory file",
            initialdir=self.DATA_DIR,
            filetypes=[("JSON/SCV inventory files", "*.json *.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            load_inventory_data(file_path)
            if validate_file_format(file_path):
                self.inventory_file = Path(file_path)
                self.status_var.set(f"Loaded inventory: {self.inventory_file.name}")
            self.refresh_inventory_list()
        except Exception as exc:
            messagebox.showerror("Inventory Load Error", str(exc))
            self.status_var.set("Failed to load inventory file.")

    def load_market_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select market file",
            initialdir=self.DATA_DIR,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return
        
        try:
            load_market_data(file_path)
            if validate_file_format(file_path):
                self.market_file = Path(file_path)
                self.status_var.set(f"Loaded market:: {self.market_file.name}")
            self.refresh_market_list()
        except Exception as exc:
            messagebox.showerror("Market Load Error", str(exc))
            self.status_var.set("Failed to load market file.")

    def refresh_inventory_list(self) -> None:
        items = get_inventory_data() or []
        self.inventory_listbox.delete(0, tk.END)
        for item in items[:250]:
            self.inventory_listbox.insert(tk.END, self.format_item(item))

    def refresh_market_list(self) -> None:
        items = get_market_data() or []
        self.market_listbox.delete(0, tk.END)
        for item in items[:250]:
            self.market_listbox.insert(tk.END, self.format_item(item))

    def refresh_all(self) -> None:
        if self.market_file.exists():
            try:
                load_market_data(self.market_file)
                self.status_var.set(f"Refreshed market file: {self.market_file.name}")
            except Exception as exc:
                messagebox.showwarning("Refresh Warning", f"Market refresh failed: {exc}")
        self.refresh_inventory_list()
        self.refresh_market_list()

    def search_item(self) -> None:
        raw_value = self.search_entry.get().strip()
        if not raw_value:
            messagebox.showinfo("Search Error", "Enter an item_id to search.")
            return
        
        try:
            item_id = int(float(raw_value))
        except ValueError:
            messagebox.showerror("Search Error", "item_id must be a number.")
            return
        
        inv_item = find_item_in_inventory(item_id)
        market_item = find_item_in_market(item_id)
        results = []

        if inv_item:
            results.append("Inventory match:\n" + self.format_item(inv_item))
        else:
            results.append("No inventory match found.")

        if market_item:
            results.append("Market match:\n" + self.format_item(inv_item))
        else:
            results.append("No market match found.")

        messagebox.showinfo("Search Results", "\n\n".join(results))

    def run(self) -> None:
        self.mainloop()

if __name__ == "__main__":
    MarketApp().run()