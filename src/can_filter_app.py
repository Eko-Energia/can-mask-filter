import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cantools
import os
from filter_calculator import calculate_mask_filter, calculate_multiple_masks_filters, format_hex_bin

class CanFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN Mask/Filter Calculator")
        self.root.geometry("800x800")
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", font=('Segoe UI', 10), rowheight=25)
        self.style.configure("Treeview.Heading", font=('Segoe UI', 10))
        
        # Data
        self.db = None
        self.all_messages = [] # List of (id, name)
        self.displayed_messages = [] # Filtered list
        
        # Layout
        self.create_widgets()
        
    def create_widgets(self):
        # Top Frame: Load and Search
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        self.load_btn = ttk.Button(top_frame, text="Load DBC File", command=self.load_dbc)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(top_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list)
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30, font=('Segoe UI', 10))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.insert(0, "Search ID or Name...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "Search ID or Name..." else None)
        
        # Middle Frame: Listbox with Checkboxes
        mid_frame = ttk.Frame(self.root, padding="10")
        mid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label
        ttk.Label(mid_frame, text="Select CAN IDs (Click checkbox to toggle):", font=('Segoe UI', 11)).pack(anchor=tk.W)
        
        # Treeview for multi-column list (Select, ID, Name)
        columns = ("Select", "ID", "Name")
        self.tree = ttk.Treeview(mid_frame, columns=columns, show="headings", selectmode="none")
        
        self.tree.heading("Select", text="[ ]", command=self.toggle_all)
        self.tree.heading("ID", text="ID (Hex)")
        self.tree.heading("Name", text="Name")
        
        self.tree.column("Select", width=60, anchor="center")
        self.tree.column("ID", width=120)
        self.tree.column("Name", width=400)
        
        # Configure tag for checked rows
        self.tree.tag_configure('checked', background='#e6ffe6') # Light green
        
        # Bind click for checkbox
        self.tree.bind("<Button-1>", self.on_tree_click)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom Frame: Actions and Results
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        # Max Filters Config
        self.max_filters_var = tk.IntVar(value=3)
        ttk.Label(bottom_frame, text="Max Filters:").pack(side=tk.LEFT, padx=5)
        self.max_filters_spin = ttk.Spinbox(bottom_frame, from_=1, to=20, textvariable=self.max_filters_var, width=5)
        self.max_filters_spin.pack(side=tk.LEFT, padx=5)

        self.calc_btn = ttk.Button(bottom_frame, text="Calculate Mask & Filter", command=self.calculate)
        self.calc_btn.pack(side=tk.LEFT, padx=20)
        
        # Result Display
        self.result_frame = ttk.LabelFrame(bottom_frame, text="Results", padding="10")
        self.result_frame.pack(fill=tk.X, pady=10)
        
        self.result_text = tk.Text(self.result_frame, font=("Consolas", 10), height=10, state=tk.DISABLED)
        self.result_scroll = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=self.result_scroll.set)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.set_result_text("Load a DBC file and select IDs to calculate.")
        
        self.checked_ids = set() # Keep track of checked IDs even when filtering

    def load_dbc(self):
        file_path = filedialog.askopenfilename(filetypes=[("DBC Files", "*.dbc"), ("All Files", "*.*")])
        if not file_path:
            return
            
        try:
            self.db = cantools.database.load_file(file_path)
            self.all_messages = []
            for msg in self.db.messages:
                self.all_messages.append((msg.frame_id, msg.name))
            
            # Sort by ID
            self.all_messages.sort(key=lambda x: x[0])
            self.checked_ids.clear()
            
            self.update_list(self.all_messages)
            messagebox.showinfo("Success", f"Loaded {len(self.all_messages)} messages.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DBC: {e}")

    def set_result_text(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
        
        # Update title if content is long
        num_lines = int(self.result_text.index('end-1c').split('.')[0])
        if num_lines > 10:
            self.result_frame.config(text="Results (Scroll to see all)")
        else:
            self.result_frame.config(text="Results")

    def clear_selection(self):
        self.checked_ids.clear()
        self.update_list(self.all_messages)

    def filter_list(self, *args):
        query = self.search_var.get().lower()
        if query == "search id or name...":
            return
            
        if not query:
            self.update_list(self.all_messages)
            return
            
        filtered = []
        for mid, name in self.all_messages:
            if query in hex(mid).lower() or query in name.lower():
                filtered.append((mid, name))
        self.update_list(filtered)

    def update_list(self, items):
        # Clear current
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for mid, name in items:
            # Check if this ID is in checked_ids
            is_checked = mid in self.checked_ids
            check_mark = "☑" if is_checked else "☐"
            tags = ('checked',) if is_checked else ()
            self.tree.insert("", tk.END, values=(check_mark, f"0x{mid:X}", name), iid=str(mid), tags=tags)

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            # Handle heading click if needed (e.g. sort), but we used it for toggle all
            col = self.tree.identify_column(event.x)
            if col == "#1":
                self.toggle_all()
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
            
        self.toggle_item(item_id)

    def toggle_item(self, item_id):
        # item_id is the CAN ID (string)
        mid = int(item_id)
        current_values = self.tree.item(item_id, "values")
        
        if mid in self.checked_ids:
            self.checked_ids.remove(mid)
            new_mark = "☐"
            self.tree.item(item_id, values=(new_mark, current_values[1], current_values[2]), tags=())
        else:
            self.checked_ids.add(mid)
            new_mark = "☑"
            self.tree.item(item_id, values=(new_mark, current_values[1], current_values[2]), tags=('checked',))

    def toggle_all(self):
        # Check if all currently visible are checked
        visible_ids = [int(item) for item in self.tree.get_children()]
        if not visible_ids:
            return
            
        all_checked = all(mid in self.checked_ids for mid in visible_ids)
        
        for mid in visible_ids:
            if all_checked:
                if mid in self.checked_ids:
                    self.checked_ids.remove(mid)
            else:
                self.checked_ids.add(mid)
        
        # Refresh view
        for item in self.tree.get_children():
            mid = int(item)
            is_checked = mid in self.checked_ids
            check_mark = "☑" if is_checked else "☐"
            tags = ('checked',) if is_checked else ()
            current_values = self.tree.item(item, "values")
            self.tree.item(item, values=(check_mark, current_values[1], current_values[2]), tags=tags)

    def calculate(self):
        if not self.checked_ids:
            self.set_result_text("Please select at least one ID.")
            return
            
        selected_ids = sorted(list(self.checked_ids))
        unselected_ids = []
        if self.db:
            for msg in self.db.messages:
                if msg.frame_id not in self.checked_ids:
                    unselected_ids.append(msg.frame_id)
        
        try:
            max_filters = int(self.max_filters_var.get())
        except:
            max_filters = 1
            
        results, collisions = calculate_multiple_masks_filters(selected_ids, unselected_ids, max_filters)
        
        res_text = f"Selected IDs: {len(selected_ids)} | Max Filters: {max_filters} | Used: {len(results)}\n\n"
        
        for i, (mask, filter_val) in enumerate(results):
            res_text += f"Set {i+1}:\n"
            res_text += f"  Mask:   {format_hex_bin(mask)}\n"
            res_text += f"  Filter: {format_hex_bin(filter_val)}\n"
            
        if collisions:
            res_text += f"\nWarning: This accept {len(collisions)} unselected IDs:\n"
            # Get names for collisions
            for col_id in collisions:
                name = "?"
                if self.db:
                    try:
                        name = self.db.get_message_by_frame_id(col_id).name
                    except:
                        pass
                res_text += f"  0x{col_id:X} ({name})\n"
        else:
            res_text += "\nPerfect match! No unselected IDs accepted."
            
        self.set_result_text(res_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = CanFilterApp(root)
    root.mainloop()
