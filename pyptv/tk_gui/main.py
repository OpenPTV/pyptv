#!/usr/bin/env python3
"""
A minimal Tk/ttk main window wired to the Experiment/ParameterManager model.

Goals:
- No TraitsUI/Enable/Chaco dependencies
- Demonstrate core flows: open experiment dir/YAML, list paramsets, set active,
  edit a few core parameters, save back to YAML
"""

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from pyptv.experiment import Experiment
from pyptv.parameter_manager import ParameterManager


class TkMainApp(ttk.Frame):
    def __init__(self, master=None, experiment: Experiment | None = None):
        super().__init__(master)
        self.master = master
        self.master.title("PyPTV (Tk/ttk)")
        self.pack(fill="both", expand=True)

        self.experiment = experiment or Experiment()

        # Top bar: open, save, active paramset
        toolbar = ttk.Frame(self)
        toolbar.pack(side="top", fill="x", padx=6, pady=6)

        self.btn_open = ttk.Button(toolbar, text="Open", command=self.on_open)
        self.btn_open.pack(side="left")

        self.btn_save = ttk.Button(toolbar, text="Save", command=self.on_save)
        self.btn_save.pack(side="left", padx=(6, 0))

        ttk.Label(toolbar, text="Active:").pack(side="left", padx=(12, 4))
        self.active_var = tk.StringVar()
        self.combo_active = ttk.Combobox(toolbar, textvariable=self.active_var, state="readonly")
        self.combo_active.pack(side="left", fill="x", expand=True)
        self.combo_active.bind("<<ComboboxSelected>>", self.on_change_active)

        # Main split: paramsets list and editor panel
        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=6, pady=6)

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=1)
        main.add(right, weight=3)

        # Paramsets tree
        self.tree = ttk.Treeview(left, show="tree")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Simple editor for a subset of PTV parameters
        form = ttk.Frame(right)
        form.pack(fill="both", expand=True)

        row = 0
        ttk.Label(form, text="num_cams").grid(row=row, column=0, sticky="e", padx=4, pady=4)
        self.num_cams_var = tk.IntVar(value=0)
        ttk.Entry(form, textvariable=self.num_cams_var, width=8).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(form, text="imx").grid(row=row, column=0, sticky="e", padx=4, pady=4)
        self.imx_var = tk.IntVar(value=0)
        ttk.Entry(form, textvariable=self.imx_var, width=8).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(form, text="imy").grid(row=row, column=0, sticky="e", padx=4, pady=4)
        self.imy_var = tk.IntVar(value=0)
        ttk.Entry(form, textvariable=self.imy_var, width=8).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(form, text="splitter").grid(row=row, column=0, sticky="e", padx=4, pady=4)
        self.splitter_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, variable=self.splitter_var).grid(row=row, column=1, sticky="w")

        form.grid_columnconfigure(2, weight=1)

        btns = ttk.Frame(right)
        btns.pack(anchor="w", padx=2, pady=6)
        ttk.Button(btns, text="Apply to model", command=self.on_apply).pack(side="left")

        # Init view
        self.refresh_from_model()

    # ------------- Model<->View plumbing -------------

    def refresh_from_model(self):
        # Populate combo
        names = [ps.name for ps in getattr(self.experiment, "paramsets", [])]
        self.combo_active["values"] = names
        if self.experiment.active_params:
            self.active_var.set(self.experiment.active_params.name)
        else:
            self.active_var.set("")

        # Populate tree with paramset nodes
        self.tree.delete(*self.tree.get_children())
        root = self.tree.insert("", "end", text="Experiment", open=True)
        params_node = self.tree.insert(root, "end", text="Parameters", open=True)
        for ps in self.experiment.paramsets:
            self.tree.insert(params_node, "end", text=ps.name, values=(ps.yaml_path,))

        # Load param fields
        try:
            pm = self.experiment.pm
            self.num_cams_var.set(pm.get_n_cam())
            ptv = pm.get_parameter("ptv")
            self.imx_var.set(ptv.get("imx", 0))
            self.imy_var.set(ptv.get("imy", 0))
            self.splitter_var.set(bool(ptv.get("splitter", False)))
        except Exception:
            # Model may not yet be initialized
            self.num_cams_var.set(0)
            self.imx_var.set(0)
            self.imy_var.set(0)
            self.splitter_var.set(False)

    def on_apply(self):
        # Push form values back into the model
        pm = self.experiment.pm
        pm.parameters["num_cams"] = int(self.num_cams_var.get())
        if "ptv" not in pm.parameters:
            pm.parameters["ptv"] = {}
        ptv = pm.parameters["ptv"]
        ptv["imx"] = int(self.imx_var.get())
        ptv["imy"] = int(self.imy_var.get())
        ptv["splitter"] = bool(self.splitter_var.get())

        # Persist to YAML via Experiment
        self.experiment.save_parameters()
        messagebox.showinfo("Saved", "Parameters saved to YAML")

    def on_open(self):
        # Allow selecting either a YAML file or a folder
        path = filedialog.askopenfilename(
            title="Open parameters.yaml",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if path:
            p = Path(path)
            if p.suffix.lower() in {".yaml", ".yml"}:
                pm = ParameterManager()
                pm.from_yaml(p)
                self.experiment = Experiment(pm=pm)
                self.experiment.populate_runs(p.parent)
                # Make sure the one we opened is the active set
                for idx, ps in enumerate(self.experiment.paramsets):
                    if ps.yaml_path.resolve() == p.resolve():
                        self.experiment.set_active(idx)
                        break
            else:
                messagebox.showerror("Error", "Please select a YAML file")
                return
        else:
            # Try selecting a directory instead
            d = filedialog.askdirectory(title="Open experiment folder")
            if d:
                dpath = Path(d)
                self.experiment = Experiment()
                self.experiment.populate_runs(dpath)
            else:
                return

        self.refresh_from_model()

    def on_save(self):
        self.on_apply()

    def on_tree_select(self, event=None):
        # When a paramset is selected in the tree, set it active
        sel = self.tree.selection()
        if not sel:
            return
        text = self.tree.item(sel[0], "text")
        try:
            idx = [ps.name for ps in self.experiment.paramsets].index(text)
        except ValueError:
            return
        self.experiment.set_active(idx)
        self.refresh_from_model()

    def on_change_active(self, event=None):
        name = self.active_var.get()
        for idx, ps in enumerate(self.experiment.paramsets):
            if ps.name == name:
                self.experiment.set_active(idx)
                self.refresh_from_model()
                break


def main():
    root = tk.Tk()
    app = TkMainApp(master=root)
    root.geometry("900x600")
    root.mainloop()


if __name__ == "__main__":
    main()