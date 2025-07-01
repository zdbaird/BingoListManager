import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
import json
import os
import subprocess
import sys

# Try to import pyperclip, handle if missing
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

class EntryManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Entry Manager")
        self.entries = []
        self.entry_vars = {}
        self.filtered_entries = []
        self.sort_ascending = True
        self.current_file = None
        self.selected_entry = None

        self.lists_folder = self.get_lists_folder()
        self.setup_ui()
        self.setup_shortcuts()

        if not HAS_PYPERCLIP:
            messagebox.showwarning(
                "Missing Dependency",
                "pyperclip is not installed. Clipboard features will be disabled."
            )

    def get_lists_folder(self):
        # Try to read lists_folder.txt from the app directory
        app_dir = os.path.dirname(sys.argv[0])
        config_path = os.path.join(app_dir, "lists_folder.txt")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                folder = f.read().strip()
                if folder and os.path.isdir(folder):
                    return folder
        # Fallback: use current working directory
        return os.getcwd()

    def setup_ui(self):
        # Remove the menu bar
        # self.menu = tk.Menu(self.root)
        # ...file_menu and menu setup removed...

        # Main layout
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.left_frame = tk.Frame(main_frame)
        self.right_frame = tk.Frame(main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Sorting, Toggle All, and Clear All buttons above the list
        top_left_controls = tk.Frame(self.left_frame)
        top_left_controls.pack(fill=tk.X, pady=(0, 2))
        self.sort_button = tk.Button(
            top_left_controls,
            text="Sort ⬆️" if self.sort_ascending else "Sort ⬇️",
            command=self.toggle_sort
        )
        self.sort_button.pack(side=tk.LEFT, padx=2)
        self.toggle_all_state = True  # True = select all, False = unselect all
        self.toggle_all_button = tk.Button(
            top_left_controls,
            text="Toggle All",
            command=self.toggle_all_entries
        )
        self.toggle_all_button.pack(side=tk.LEFT, padx=2)
        tk.Button(top_left_controls, text="Clear All", command=self.clear_entries).pack(side=tk.LEFT, padx=2)

        self.setup_entry_list()

        # Save List As button at the bottom
        save_frame = tk.Frame(self.left_frame)
        save_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)
        tk.Button(save_frame, text="Save List As", command=self.save_list_as).pack(side=tk.LEFT, padx=5, pady=5)

        # JSON display and controls on the right
        self.setup_json_display()

    def setup_shortcuts(self):
        self.root.bind('<Control-s>', lambda e: self.save_list())
        self.root.bind('<Control-S>', lambda e: self.save_list_as())
        self.root.bind('<Control-o>', lambda e: self.load_list())
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        self.root.bind('<Control-n>', lambda e: self.add_entry())

    def focus_search(self):
        self.search_entry.focus_set()

    def setup_entry_list(self):
        # Treeview for entries
        columns = ("enabled", "name")
        list_frame = tk.Frame(self.left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse", height=20)
        self.tree.heading("enabled", text="")
        self.tree.heading("name", text="Entry Name")
        self.tree.column("enabled", width=30, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Vertical scrollbar (now between the list and the buttons)
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.LEFT, fill=tk.Y)

        # Mousewheel scrolling
        def _on_mousewheel(event):
            self.tree.yview_scroll(int(-1*(event.delta/120)), "units")
        self.tree.bind("<Enter>", lambda e: self.tree.bind_all("<MouseWheel>", _on_mousewheel))
        self.tree.bind("<Leave>", lambda e: self.tree.unbind_all("<MouseWheel>"))

        # Bindings for selection and renaming
        self.tree.bind("<Double-1>", self.rename_entry_inline)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Button-1>", self.on_tree_click)

        # Import/Open List/Add/Remove buttons
        button_frame = tk.Frame(self.left_frame)
        button_frame.pack(fill=tk.X, pady=2)
        tk.Button(button_frame, text="Open List", command=self.load_list).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Import CSV", command=self.import_csv).pack(side=tk.LEFT, padx=2)

        below_frame = tk.Frame(self.left_frame)
        below_frame.pack(fill=tk.X, pady=2)
        tk.Button(below_frame, text="Add Entry", command=self.add_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(below_frame, text="Remove Entry", command=self.remove_selected_entry).pack(side=tk.LEFT, padx=2)

    def setup_json_display(self):
        tk.Label(self.right_frame, text="Enabled Entries (JSON):").pack(anchor="w")
        self.json_text = tk.Text(self.right_frame, height=25)
        self.json_text.pack(fill=tk.BOTH, expand=True)
        self.json_text.configure(state='disabled')
        btn_frame = tk.Frame(self.right_frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Copy JSON", command=self.copy_json).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Export JSON", command=self.export_json).pack(side=tk.LEFT, padx=2)  # <-- Add export button
        tk.Button(btn_frame, text="Open Bingosync", command=self.open_bingosync).pack(side=tk.LEFT, padx=2)

    def export_json(self):
        enabled = [{"name": n} for n, _ in self.entries if self.entry_vars[n].get()]
        # Default to /lists directory in the root of the drive/project
        root_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        default_dir = os.path.join(root_dir, "..", "lists")
        default_dir = os.path.abspath(default_dir)
        os.makedirs(default_dir, exist_ok=True)
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir=default_dir,
            title="Export Enabled Entries as JSON"
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(enabled, f, indent=4)
                messagebox.showinfo("Exported", f"Enabled entries exported to {path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export JSON:\n{e}")

    # --- Treeview-based entry management ---
    def add_entry_widget(self, name, enabled=True):
        var = tk.BooleanVar(value=enabled)
        self.entry_vars[name] = var
        # Insert the new entry into self.entries in ascending order
        self.entries.append((name, ""))  # "" placeholder for iid
        self.entries.sort(key=lambda x: x[0].lower())  # Always ascending order

        # Rebuild treeview to reflect the new order
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, (n, _) in enumerate(self.entries):
            iid = self.tree.insert("", "end", values=("[x]" if self.entry_vars[n].get() else "[ ]", n))
            self.entries[idx] = (n, iid)
        self.update_json()

    def add_entry(self):
        new_name = simpledialog.askstring("Add Entry", "Enter new entry:")
        if new_name and new_name not in self.entry_vars:
            self.add_entry_widget(new_name)

    def remove_selected_entry(self):
        selected = self.tree.selection()
        if selected:
            name = self.tree.item(selected[0], "values")[1]
            self.remove_entry(name)

    def remove_entry(self, name):
        # Find the iid for the given name
        iid = None
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[1] == name:
                iid = item
                break
        if iid:
            self.tree.delete(iid)
        # Remove from entries and entry_vars
        self.entries = [(n, i) for n, i in self.entries if n != name]
        if name in self.entry_vars:
            del self.entry_vars[name]
        self.update_json()

    def clear_entries(self):
        for _, iid in self.entries:
            self.tree.delete(iid)
        self.entries.clear()
        self.entry_vars.clear()
        self.update_json()

    def on_tree_select(self, event):
        # Highlight selection (Treeview handles this by default)
        pass

    def rename_entry_inline(self, event):
        # Inline rename on double-click
        item = self.tree.identify_row(event.y)
        if not item:
            return
        old_name = self.tree.item(item, "values")[1]
        entry = tk.Entry(self.tree)
        entry.insert(0, old_name)
        entry.place(x=event.x, y=event.y)
        entry.focus()

        def confirm(event=None):
            new_name = entry.get().strip()
            if not new_name or new_name in self.entry_vars:
                messagebox.showerror("Invalid name", "Name is empty or already exists.")
                entry.destroy()
                return
            # Update entry_vars and entries
            self.entry_vars[new_name] = self.entry_vars.pop(old_name)
            for i, (n, iid) in enumerate(self.entries):
                if n == old_name:
                    self.entries[i] = (new_name, iid)
                    break
            # Re-sort entries alphabetically
            self.entries.sort(key=lambda x: x[0].lower())
            # Rebuild treeview to reflect new order
            for item_id in self.tree.get_children():
                self.tree.delete(item_id)
            for idx, (n, _) in enumerate(self.entries):
                iid = self.tree.insert("", "end", values=("[x]" if self.entry_vars[n].get() else "[ ]", n))
                self.entries[idx] = (n, iid)
            entry.destroy()
            self.update_json()

        def cancel(event=None):
            entry.destroy()

        entry.bind("<Return>", confirm)
        entry.bind("<FocusOut>", confirm)
        entry.bind("<Escape>", cancel)

    def update_json(self):
        enabled = [{"name": n} for n, _ in self.entries if self.entry_vars[n].get()]
        self.json_text.configure(state='normal')
        self.json_text.delete("1.0", tk.END)
        self.json_text.insert(tk.END, json.dumps(enabled, indent=4))
        self.json_text.configure(state='disabled')

    def copy_json(self):
        enabled = [{"name": n} for n, _ in self.entries if self.entry_vars[n].get()]
        if not HAS_PYPERCLIP:
            messagebox.showerror("Clipboard Error", "pyperclip is not installed. Cannot copy to clipboard.")
            return
        try:
            pyperclip.copy(json.dumps(enabled, indent=4))
            messagebox.showinfo("Copied", "JSON copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Clipboard Error", f"Could not copy to clipboard:\n{e}")

    def load_list(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            initialdir=self.lists_folder
        )
        if path:
            self.load_list_from_file(path)
            self.current_file = path

    def import_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")],
            initialdir=self.lists_folder
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    if name and name not in self.entry_vars:
                        self.add_entry_widget(name)
        except Exception as e:
            messagebox.showerror("Error Importing CSV", str(e))

    def load_list_from_file(self, path):
        try:
            with open(path, 'r') as f:
                raw = json.load(f)
                self.clear_entries()
                for item in raw:
                    if isinstance(item, dict):
                        self.add_entry_widget(item["name"], item.get("enabled", True))
                    elif isinstance(item, str):
                        self.add_entry_widget(item, True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_list(self):
        if self.current_file:
            self.save_list_to_file(self.current_file)
        else:
            self.save_list_as()

    def save_list_as(self):
        # Save to /lists in the root directory
        root_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        default_dir = os.path.join(root_dir, "..", "lists")
        default_dir = os.path.abspath(default_dir)
        os.makedirs(default_dir, exist_ok=True)
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir=default_dir
        )
        if path:
            self.current_file = path
            self.save_list_to_file(path)

    def save_list_to_file(self, path):
        try:
            data = [{"name": n, "enabled": self.entry_vars[n].get()} for n, _ in self.entries]
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Saved", f"List saved to {path}")
        except Exception as e:
            messagebox.showerror("Error Saving File", str(e))

    def open_lists_folder(self):
        folder = os.getcwd()
        try:
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")

    # Add this method to EntryManagerApp:
    def open_bingosync(self):
        import webbrowser
        webbrowser.open("https://bingosync.com/")

    def toggle_sort(self):
        self.sort_ascending = not self.sort_ascending
        # Update button text
        if hasattr(self, "sort_button"):
            self.sort_button.config(text="Sort ⬆️" if self.sort_ascending else "Sort ⬇️")
        # Sort entries by name
        self.entries.sort(key=lambda x: x[0], reverse=not self.sort_ascending)
        # Remove all items from the tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Re-insert sorted items
        for name, iid in self.entries:
            enabled = self.entry_vars[name]
            self.tree.insert("", "end", values=("[x]" if enabled.get() else "[ ]", name))

    def toggle_all_entries(self):
        # Toggle all entries to selected/unselected based on self.toggle_all_state
        for name in self.entry_vars:
            self.entry_vars[name].set(self.toggle_all_state)
        # Rebuild the treeview and update self.entries with new iids
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, (n, _) in enumerate(self.entries):
            iid = self.tree.insert("", "end", values=("[x]" if self.entry_vars[n].get() else "[ ]", n))
            self.entries[idx] = (n, iid)
        self.toggle_all_state = not self.toggle_all_state  # Flip for next click
        self.update_json()

    def on_tree_click(self, event):
        # Identify the region and column
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        if col != "#1":  # Only toggle if clicking the first column (checkbox)
            return
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        name = self.tree.item(row_id, "values")[1]
        var = self.entry_vars[name]
        var.set(not var.get())
        self.tree.item(row_id, values=("[x]" if var.get() else "[ ]", name))
        self.update_json()

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap("BingoListManager.ico")  # Path to your .ico file
    app = EntryManagerApp(root)
    root.mainloop()
