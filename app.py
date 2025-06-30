import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
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

        # Determine lists folder
        self.lists_folder = self.get_lists_folder()

        self.setup_ui()
        self.setup_shortcuts()
        # self.load_initial_list()  # Removed: No default list loaded

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
        # Menu bar
        self.menu = tk.Menu(self.root)
        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Open List", command=self.load_list, accelerator="Ctrl+O")
        file_menu.add_command(label="Import CSV", command=self.import_csv)
        file_menu.add_command(label="Save", command=self.save_list, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_list_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Open Lists Folder", command=self.open_lists_folder)
        self.menu.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=self.menu)

        # Top controls
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_entries())
        tk.Label(top_frame, text="Search:").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(top_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(top_frame, text="Sort A-Z/Z-A", command=self.toggle_sort).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Batch Remove", command=self.batch_remove_dialog).pack(side=tk.LEFT, padx=5)

        # Main layout
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.left_frame = tk.Frame(main_frame)
        self.right_frame = tk.Frame(main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.setup_entry_list()
        self.setup_json_display()

    def setup_shortcuts(self):
        self.root.bind('<Control-s>', lambda e: self.save_list())
        self.root.bind('<Control-S>', lambda e: self.save_list_as())
        self.root.bind('<Control-o>', lambda e: self.load_list())
        self.root.bind('<Control-f>', lambda e: self.focus_search())

    def focus_search(self):
        self.search_entry.focus_set()

    def setup_entry_list(self):
        control_frame = tk.Frame(self.left_frame)
        control_frame.pack(fill=tk.X)

        self.select_all_var = tk.BooleanVar()
        tk.Checkbutton(control_frame, text="Select All", variable=self.select_all_var, command=self.toggle_all).pack(anchor="w")

        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=2)
        tk.Button(button_frame, text="Add Entry", command=self.add_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Remove Entry", command=self.remove_selected_entry).pack(side=tk.LEFT, padx=2)

        self.scroll_canvas = tk.Canvas(self.left_frame)
        self.scroll_frame = tk.Frame(self.scroll_canvas)
        self.scrollbar = tk.Scrollbar(self.left_frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        self.scroll_canvas.create_window((0, 0), window=self.scroll_frame, anchor='nw')
        self.scroll_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))

    def setup_json_display(self):
        tk.Label(self.right_frame, text="Enabled Entries (JSON):").pack(anchor="w")
        self.json_text = tk.Text(self.right_frame, height=25)
        self.json_text.pack(fill=tk.BOTH, expand=True)
        self.json_text.configure(state='disabled')
        tk.Button(self.right_frame, text="Copy JSON", command=self.copy_json).pack(pady=5)

    def add_entry_widget(self, name, enabled=True):
        frame = tk.Frame(self.scroll_frame)
        var = tk.BooleanVar(value=enabled)
        cb = tk.Checkbutton(frame, variable=var, command=self.update_json)
        cb.pack(side=tk.LEFT)
        label = tk.Label(frame, text=name, anchor="w", justify="left", wraplength=250)
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        label.bind("<Double-Button-1>", lambda e, l=label: self.rename_entry_inline(l))
        label.bind("<Button-3>", lambda e, l=label: self.show_context_menu(e, l))
        frame.pack(fill=tk.X, pady=1)

        self.entries.append((name, frame))
        self.entry_vars[name] = var
        self.filter_entries()
        self.update_json()

    def rename_entry_inline(self, label):
        current_text = label.cget("text")
        entry = tk.Entry(label.master)
        entry.insert(0, current_text)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        label.pack_forget()

        def confirm():
            new_name = entry.get().strip()
            if not new_name or new_name in self.entry_vars:
                messagebox.showerror("Invalid name", "Name is empty or already exists.")
                entry.destroy()
                label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                return
            self.entry_vars[new_name] = self.entry_vars.pop(current_text)
            for i, (n, f) in enumerate(self.entries):
                if n == current_text:
                    self.entries[i] = (new_name, f)
                    break
            label.config(text=new_name)
            entry.destroy()
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.update_json()

        entry.bind("<Return>", lambda e: confirm())
        entry.bind("<FocusOut>", lambda e: confirm())
        entry.focus()

    def show_context_menu(self, event, label):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Rename", command=lambda: self.rename_entry_inline(label))
        menu.add_command(label="Remove", command=lambda: self.remove_entry(label.cget("text")))
        menu.add_command(label="Toggle Enabled", command=lambda: self.toggle_enabled(label.cget("text")))
        menu.tk_popup(event.x_root, event.y_root)

    def toggle_all(self):
        for name in self.entry_vars:
            self.entry_vars[name].set(self.select_all_var.get())
        self.update_json()

    def toggle_enabled(self, name):
        self.entry_vars[name].set(not self.entry_vars[name].get())
        self.update_json()

    def add_entry(self):
        new_name = simpledialog.askstring("Add Entry", "Enter new entry:")
        if new_name and new_name not in self.entry_vars:
            self.add_entry_widget(new_name)

    def remove_entry(self, name):
        if name in self.entry_vars:
            # Confirmation dialog before removal
            if not messagebox.askyesno("Confirm Removal", f"Remove entry '{name}'?"):
                return
            frame = next((f for n, f in self.entries if n == name), None)
            if frame:
                frame.destroy()
            self.entries = [(n, f) for n, f in self.entries if n != name]
            del self.entry_vars[name]
            self.update_json()

    def remove_selected_entry(self):
        selected = simpledialog.askstring("Remove Entry", "Enter entry to remove:")
        if selected:
            self.remove_entry(selected)

    def batch_remove_dialog(self):
        # Dialog for multi-select removal
        dialog = tk.Toplevel(self.root)
        dialog.title("Batch Remove Entries")
        dialog.geometry("300x400")
        tk.Label(dialog, text="Select entries to remove:").pack(anchor="w", padx=10, pady=5)
        vars = {}
        for name, _ in self.entries:
            var = tk.BooleanVar()
            tk.Checkbutton(dialog, text=name, variable=var).pack(anchor="w", padx=10)
            vars[name] = var

        def confirm():
            to_remove = [name for name, var in vars.items() if var.get()]
            if to_remove and messagebox.askyesno("Confirm Batch Removal", f"Remove {len(to_remove)} entries?"):
                for name in to_remove:
                    self.remove_entry(name)
            dialog.destroy()

        tk.Button(dialog, text="Remove Selected", command=confirm).pack(pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

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
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir=self.lists_folder
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

    def clear_entries(self):
        for _, frame in self.entries:
            frame.destroy()
        self.entries.clear()
        self.entry_vars.clear()

    def filter_entries(self):
        search = self.search_var.get().lower()
        for name, frame in self.entries:
            frame.pack_forget()
            if search in name.lower():
                frame.pack(fill=tk.X, pady=1)

    def toggle_sort(self):
        self.entries.sort(key=lambda x: x[0], reverse=not self.sort_ascending)
        self.sort_ascending = not self.sort_ascending
        for _, frame in self.entries:
            frame.pack_forget()
        self.filter_entries()

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

if __name__ == "__main__":
    root = tk.Tk()
    app = EntryManagerApp(root)
    root.mainloop()
