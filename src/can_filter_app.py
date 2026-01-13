import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cantools
import os
from filter_calculator import calculate_mask_filter, calculate_multiple_masks_filters, format_hex_bin

class CanFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN Mask/Filter Calculator")
        self.root.geometry("1200x1000")
        
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
        self.search_var.trace_add("write", self.filter_list)
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30, font=('Segoe UI', 10))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.insert(0, "Search ID or Name...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "Search ID or Name..." else None)
        
        # Middle Frame: Listbox with Checkboxes
        mid_frame = ttk.Frame(self.root, padding="10")
        mid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label
        ttk.Label(mid_frame, text="Select CAN IDs (Click checkbox to toggle):", font=('Segoe UI', 11)).pack(anchor=tk.W)
        
        # Treeview for multi-column list
        columns = ("Select", "ID", "Name", "CycleTime", "Freq", "BytesPerSec")
        self.tree = ttk.Treeview(mid_frame, columns=columns, show="headings", selectmode="none")
        
        self.tree.heading("Select", text="[ ]", command=self.toggle_all)
        self.tree.heading("ID", text="ID (Hex)")
        self.tree.heading("Name", text="Name")
        self.tree.heading("CycleTime", text="Cycle (ms)")
        self.tree.heading("Freq", text="Freq (Hz)")
        self.tree.heading("BytesPerSec", text="Bytes/s")
        
        self.tree.column("Select", width=60, anchor="center")
        self.tree.column("ID", width=80)
        self.tree.column("Name", width=300)
        self.tree.column("CycleTime", width=80, anchor="center")
        self.tree.column("Freq", width=80, anchor="center")
        self.tree.column("BytesPerSec", width=80, anchor="center")
        
        # Configure tags
        self.tree.tag_configure('checked', background='#e6ffe6') # Light green
        self.tree.tag_configure('node_row', background='#f0f0f0', font=('Segoe UI', 10, 'bold')) # Distinct style for Nodes
        
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
        self.auto_filters_var = tk.BooleanVar(value=True)

        # Control Panel Container
        control_panel = ttk.Frame(bottom_frame)
        control_panel.pack(fill=tk.X, pady=(0, 5))

        # Configuration Frame
        config_frame = ttk.LabelFrame(control_panel, text="Configuration", padding="5")
        config_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
        
        ttk.Label(config_frame, text="Max Filters:").pack(side=tk.LEFT, padx=5)
        self.max_filters_spin = ttk.Spinbox(config_frame, from_=1, to=20, textvariable=self.max_filters_var, width=5)
        self.max_filters_spin.pack(side=tk.LEFT, padx=5)
        
        self.auto_check = ttk.Checkbutton(config_frame, text="Auto", variable=self.auto_filters_var, command=self.toggle_max_filters)
        self.auto_check.pack(side=tk.LEFT, padx=5)

        # Actions Frame
        actions_frame = ttk.LabelFrame(control_panel, text="Actions", padding="5")
        actions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

        self.calc_btn = ttk.Button(actions_frame, text="Calculate Mask & Filter", command=self.calculate)
        self.calc_btn.grid(row=0, column=0, columnspan=2, padx=5, pady=2, sticky="ew")

        self.rate_btn = ttk.Button(actions_frame, text="Calculate Data Rate", command=self.calculate_data_rate)
        self.rate_btn.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

        self.gen_header_btn = ttk.Button(actions_frame, text="Generate .h", command=self.generate_header)
        self.gen_header_btn.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Initialize state based on default value
        self.toggle_max_filters()
        
        # Result Display
        self.result_frame = ttk.LabelFrame(bottom_frame, text="Results", padding="10")
        self.result_frame.pack(fill=tk.X, pady=10)
        
        self.result_text = tk.Text(self.result_frame, font=("Consolas", 10), height=10, state=tk.DISABLED)
        self.result_scroll = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=self.result_scroll.set)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.set_result_text("Load a DBC file and select IDs to calculate.")
        
        self.checked_ids = set() # Keep track of checked IDs
        self.node_structure = {} # {NodeName: [msg_obj, ...]}

    def toggle_max_filters(self):
        if self.auto_filters_var.get():
            self.max_filters_spin.configure(state=tk.DISABLED)
        else:
            self.max_filters_spin.configure(state=tk.NORMAL)

    def load_dbc(self):
        file_path = filedialog.askopenfilename(filetypes=[("DBC Files", "*.dbc"), ("All Files", "*.*")])
        if not file_path:
            return
            
        try:
            self.db = cantools.database.load_file(file_path)
            self.all_messages = []
            self.node_structure = {}
            
            # Group by Node
            # We need to look at senders. cantools msg.senders is a list.
            for msg in self.db.messages:
                self.all_messages.append(msg)
                
                senders = msg.senders
                if not senders:
                    senders = ["Vector__XXX"] # or "No Sender"
                
                for sender in senders:
                    if sender not in self.node_structure:
                        self.node_structure[sender] = []
                    self.node_structure[sender].append(msg)
            
            # Sort messages within nodes by ID
            for node in self.node_structure:
                self.node_structure[node].sort(key=lambda x: x.frame_id)
                
            self.checked_ids.clear()
            self.update_list(self.node_structure)
            
            # Check availability of GenMsgCycleTime or msg.cycle_time for Data Rate button
            has_cycle_info = False
            for msg in self.all_messages:
                # Check safe access to attributes
                has_attr_cycle = False
                if hasattr(msg, 'attributes') and msg.attributes and 'GenMsgCycleTime' in msg.attributes:
                    has_attr_cycle = True
                
                if (hasattr(msg, 'cycle_time') and msg.cycle_time) or has_attr_cycle:
                    has_cycle_info = True
                    break
            
            if has_cycle_info:
                self.rate_btn.configure(state=tk.NORMAL)
            else:
                self.rate_btn.configure(state=tk.DISABLED)

            messagebox.showinfo("Success", f"Loaded {len(self.all_messages)} messages in {len(self.node_structure)} nodes.")
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
        self.search_var.set("Search ID or Name...")
        self.update_list(self.node_structure)

    def filter_list(self, *args):
        query = self.search_var.get().lower()
        if query == "search id or name...":
            return
            
        if not query:
            self.update_list(self.node_structure)
            return
            
        # For filtering, we might flatten or keep structure only if node matches or child matches
        filtered_structure = {}
        
        for node, msgs in self.node_structure.items():
            node_matches = query in node.lower()
            matching_msgs = []
            for msg in msgs:
                if node_matches or (query in hex(msg.frame_id).lower()) or (query in msg.name.lower()):
                    matching_msgs.append(msg)
            
            if matching_msgs:
                filtered_structure[node] = matching_msgs
                
        self.update_list(filtered_structure)

    def update_list(self, structure):
        # Clear current
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Sort nodes by name
        sorted_nodes = sorted(structure.keys())
        
        for node_name in sorted_nodes:
            msgs = structure[node_name]
            
            # Calculate Node Totals
            node_bytes_per_sec = 0.0
            node_total_freq = 0.0 # Just for reference, bytes is more important
            
            node_children_ids = []
            
            for msg in msgs:
                node_children_ids.append(msg.frame_id)
                
                # Cycle Time and Freq
                cycle_time = 0
                if msg.cycle_time:
                    cycle_time = msg.cycle_time
                elif hasattr(msg, 'attributes') and msg.attributes and 'GenMsgCycleTime' in msg.attributes:
                     # cantools might put it in .attributes dictionary depending on parsing
                     try:
                         cycle_time = int(msg.attributes['GenMsgCycleTime'])
                     except:
                         pass
                
                freq = 0.0
                if cycle_time > 0:
                    freq = 1000.0 / cycle_time
                    
                bytes_s = freq * msg.length
                node_bytes_per_sec += bytes_s
            
            # Determine Node Check State
            all_checked = all(mid in self.checked_ids for mid in node_children_ids)
            any_checked = any(mid in self.checked_ids for mid in node_children_ids)
            
            node_check = "☐"
            if all_checked and msgs:
                node_check = "☑"
            elif any_checked:
                node_check = "☒" # Mixed state representation
                
            # Insert Node Row
            # We use a custom ID prefix for nodes to distinguish them
            node_iid = f"NODE_{node_name}"
            
            # Format numbers
            node_s_str = f"{node_bytes_per_sec:.1f}" if node_bytes_per_sec > 0 else "-"
            
            self.tree.insert("", tk.END, iid=node_iid, values=(node_check, "", f"Node: {node_name} ({len(msgs)} msgs)", "", "", node_s_str), open=True, tags=('node_row',))
            
            # Insert Messages
            for msg in msgs:
                mid = msg.frame_id
                
                cycle_time = "0"
                if msg.cycle_time:
                    cycle_time = str(msg.cycle_time)
                elif hasattr(msg, 'attributes') and msg.attributes and 'GenMsgCycleTime' in msg.attributes:
                     cycle_time = str(msg.attributes['GenMsgCycleTime'])

                freq_str = "-"
                bytes_str = "-"
                
                try:
                    c_val = int(cycle_time)
                    if c_val > 0:
                        f_val = 1000.0 / c_val
                        freq_str = f"{f_val:.1f}"
                        b_val = f_val * msg.length
                        bytes_str = f"{b_val:.1f}"
                except:
                    pass
                
                is_checked = mid in self.checked_ids
                check_mark = "☑" if is_checked else "☐"
                tags = ('checked',) if is_checked else ()
                
                self.tree.insert(node_iid, tk.END, iid=str(mid), values=(check_mark, f"0x{mid:X}", msg.name, cycle_time, freq_str, bytes_str), tags=tags)

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            col = self.tree.identify_column(event.x)
            if col == "#1":
                self.toggle_all()
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
            
        # Toggle Logic
        self.toggle_item(item_id)

    def toggle_item(self, item_id):
        if item_id.startswith("NODE_"):
            # Node Clicked - Toggle All Children
            node_val = self.tree.item(item_id, "values")
            current_mark = node_val[0]
            
            # If currently checked or mixed -> Uncheck all
            # If unchecked -> Check all
            should_check = (current_mark == "☐")
            
            children = self.tree.get_children(item_id)
            for child_id in children:
                mid = int(child_id)
                if should_check:
                    self.checked_ids.add(mid)
                else:
                    if mid in self.checked_ids:
                        self.checked_ids.remove(mid)
            
            # Refresh this node's visual state
            self.refresh_node_visuals(item_id)
            
        else:
            # Message Clicked
            mid = int(item_id)
            if mid in self.checked_ids:
                self.checked_ids.remove(mid)
            else:
                self.checked_ids.add(mid)
                
            # Update this row
            self.refresh_row_visuals(str(mid))
            
            # Update Parent Node
            parent_id = self.tree.parent(item_id)
            if parent_id:
                self.refresh_node_visuals(parent_id)

    def refresh_row_visuals(self, item_id):
        if item_id.startswith("NODE_"):
            return 
        mid = int(item_id)
        is_checked = mid in self.checked_ids
        check_mark = "☑" if is_checked else "☐"
        tags = ('checked',) if is_checked else ()
        
        # Preserve other values
        current = self.tree.item(item_id, "values")
        new_vals = [check_mark] + list(current)[1:]
        self.tree.item(item_id, values=new_vals, tags=tags)

    def refresh_node_visuals(self, node_id):
        children = self.tree.get_children(node_id)
        if not children:
            return
            
        child_mids = [int(c) for c in children]
        all_checked = all(mid in self.checked_ids for mid in child_mids)
        any_checked = any(mid in self.checked_ids for mid in child_mids)
        
        node_check = "☐"
        if all_checked:
            node_check = "☑"
        elif any_checked:
            node_check = "☒"
            
        current = self.tree.item(node_id, "values")
        new_vals = [node_check] + list(current)[1:]
        self.tree.item(node_id, values=new_vals)
        
        # Also refresh all children visuals to ensure consistency
        for child in children:
            self.refresh_row_visuals(child)

    def toggle_all(self):
        # Determine target state based on global selection
        # If any visible item is unchecked -> check all
        # Else -> uncheck all
        
        all_visible_nodes = self.tree.get_children() # Root level items (Nodes)
        all_child_mids = []
        for node in all_visible_nodes:
            # Add node's children
            children = self.tree.get_children(node)
            for c in children:
                all_child_mids.append(int(c))
                
        if not all_child_mids:
            return

        all_checked = all(mid in self.checked_ids for mid in all_child_mids)
        should_check = not all_checked
        
        for mid in all_child_mids:
            if should_check:
                self.checked_ids.add(mid)
            else:
                if mid in self.checked_ids:
                    self.checked_ids.remove(mid)
                    
        # Refresh all nodes
        for node in all_visible_nodes:
            self.refresh_node_visuals(node)

    def generate_header(self):
        if not self.db:
             messagebox.showerror("Error", "No DBC loaded.")
             return

        # Prompt for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".h",
            filetypes=[("Header Files", "*.h"), ("All Files", "*.*")],
            initialfile="can_id_list.h"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                # File Header
                f.write("/*\n")
                f.write(" * can_id_list.h\n")
                f.write(" */\n\n")
                
                f.write("#ifndef INC_CAN_ID_LIST_H_\n")
                f.write("#define INC_CAN_ID_LIST_H_\n\n")
                
                # Optional: Add standard IDs if needed, or leave blank as requested
                f.write("#define SAFE_STATE_ID \t0\n")
                f.write("#define ERROR_MSG_ID\t1\n\n")

                # Sort nodes
                sorted_nodes = sorted(self.node_structure.keys())
                
                for node_name in sorted_nodes:
                    f.write(f"/*\n * {node_name}\n */\n\n")
                    
                    msgs = self.node_structure[node_name]
                    # Sort messages by ID
                    msgs.sort(key=lambda x: x.frame_id)
                    
                    for msg in msgs:
                        # Construct Macro Name
                        # [ModuleName]_[ShortMessageName]_ID
                        
                        n_str = node_name.upper().replace(" ", "_")
                        m_str = msg.name.upper().replace(" ", "_")
                        
                        # Heuristic to avoid duplication (e.g. RCD_RCD_Error -> RCD_ERROR)
                        if m_str.startswith(n_str + "_"):
                            base_name = m_str
                        elif m_str == n_str: # Unusual but possible
                            base_name = m_str
                        else:
                            base_name = f"{n_str}_{m_str}"
                            
                        macro_name = f"{base_name}_ID"
                        
                        # Sanitize
                        macro_name = "".join(c if c.isalnum() or c == '_' else '_' for c in macro_name)
                        
                        # ID in Hex
                        hex_id = f"0x{msg.frame_id:X}"
                        
                        f.write(f"#define {macro_name} {hex_id}\n")
                    
                    f.write("\n")
                
                f.write("#endif /* INC_CAN_ID_LIST_H_ */\n")
            
            messagebox.showinfo("Success", f"File saved to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def calculate_data_rate(self):
        if not self.checked_ids:
            self.set_result_text("Please select at least one ID.")
            return

        if not self.db:
             self.set_result_text("No DBC loaded.")
             return

        total_bytes_sec = 0.0
        total_frames_sec = 0.0
        total_bits_sec = 0.0
        
        sorted_ids = sorted(list(self.checked_ids))
        
        for mid in sorted_ids:
            try:
                msg = self.db.get_message_by_frame_id(mid)
            except:
                continue
                
            cycle_time = 0
            if msg.cycle_time:
                cycle_time = msg.cycle_time
            elif hasattr(msg, 'attributes') and msg.attributes and 'GenMsgCycleTime' in msg.attributes:
                 try:
                     cycle_time = int(msg.attributes['GenMsgCycleTime'])
                 except:
                     pass
            
            if cycle_time > 0:
                freq = 1000.0 / cycle_time
                bytes_s = freq * msg.length
                
                # Estimate bits on bus (Standard CAN 11-bit)
                # Overhead approx 47 bits + data (8 * length)
                # Does not strictly account for bit stuffing (which adds ~20%)
                bits_per_frame = 47 + (8 * msg.length)
                bits_s = freq * bits_per_frame
                
                total_bytes_sec += bytes_s
                total_frames_sec += freq
                total_bits_sec += bits_s

        # Bus Load Calculation (500 kbps)
        baud_rate = 500000.0
        bus_load_percent = (total_bits_sec / baud_rate) * 100.0
        
        # Determine Status
        status_msg = ""
        if bus_load_percent <= 30:
            status_msg = "OK (Low Load)"
        elif bus_load_percent <= 50:
            status_msg = "Standard Load"
        elif bus_load_percent <= 70:
            status_msg = "Warning: Load is getting high"
        else:
            status_msg = "CRITICAL: Bus overload likely!"

        res_text = f"Data Rate Calculation for {len(sorted_ids)} selected IDs:\n\n"
        res_text += f"Total Data Rate:  {total_bytes_sec:.2f} B/s ({total_bytes_sec/1024:.2f} kB/s)\n"
        res_text += f"Total Frame Rate: {total_frames_sec:.2f} frames/s\n\n"
        
        res_text += f"Bus Load (approx. @ 500kbps):\n"
        res_text += f"  Load:   {bus_load_percent:.2f} %\n"
        res_text += f"  Status: {status_msg}\n"
        
        res_text += "\nNote: Bus load estimation uses 47 bits overhead per frame."
        res_text += "\nBit stuffing is not calculated (add ~20% for worst case)."
        
        self.set_result_text(res_text)

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
            if self.auto_filters_var.get():
                # In Auto mode, we allow as many filters as needed to avoid collisions
                # We simply pass a large number (e.g. number of selected IDs or a high hardware limit like 20)
                # If the algorithm finds 0-collision merges, it takes them. 
                # If it hits a wall where merging causes collisions, it stops if we are under max_filters.
                max_filters = 20 # Common hardware limit, or could be len(selected_ids)
            else:
                max_filters = int(self.max_filters_var.get())
        except:
            max_filters = 1
            
        results, collisions = calculate_multiple_masks_filters(selected_ids, unselected_ids, max_filters)
        
        mode_str = "Auto" if self.auto_filters_var.get() else str(max_filters)
        res_text = f"Selected IDs: {len(selected_ids)} | Max Filters: {mode_str} | Used: {len(results)}\n\n"
        
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
