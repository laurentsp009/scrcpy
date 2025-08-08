#!/usr/bin/env python3
"""Graphical interface for scrcpy on macOS.

This script parses the scrcpy manpage to expose all command line options
through a Tk interface. Options that expect values are represented by text
inputs, while simple flags are represented by checkboxes.

The script requires scrcpy to be installed and available in $PATH.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

MANPAGE = Path(__file__).resolve().parent.parent / "app" / "scrcpy.1"


def parse_options():
    """Parse scrcpy options from the manpage.

    Returns a list of dictionaries with keys 'name' and 'has_value'.
    """
    options = []
    if not MANPAGE.exists():
        return options

    mantext = MANPAGE.read_text(encoding="utf-8")
    for line in mantext.splitlines():
        match = re.match(r"\.(B|BI)\s+(.*)", line)
        if not match:
            continue
        kind, content = match.groups()
        content = content.replace("\\-", "-").strip()
        if kind == "B":
            content = content.strip('"')
            parts = [p.strip() for p in content.split(',')]
            long_opts = [p.split()[0] for p in parts if p.startswith('--')]
            if long_opts:
                options.append({"name": long_opts[0], "has_value": False})
            elif parts:
                options.append({"name": parts[0].split()[0], "has_value": False})
        elif kind == "BI":
            m = re.match(r'"([^\"]+)"', content)
            if not m:
                continue
            optpart = m.group(1).replace("\\-", "-")
            parts = [p.strip() for p in optpart.split(',')]
            long_opts = [p for p in parts if p.startswith('--')]
            target = long_opts[0] if long_opts else parts[0]
            options.append({"name": target, "has_value": True})
    return options


def build_gui(options):
    root = tk.Tk()
    root.title("scrcpy GUI")

    canvas = tk.Canvas(root)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable = ttk.Frame(canvas)

    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    widgets = {}
    row = 0
    for opt in options:
        if opt["has_value"]:
            label = ttk.Label(scrollable, text=opt["name"])
            label.grid(row=row, column=0, sticky="w", padx=2, pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(scrollable, textvariable=var, width=20)
            entry.grid(row=row, column=1, sticky="ew", padx=2, pady=2)
            widgets[opt["name"]] = var
        else:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(scrollable, text=opt["name"], variable=var)
            chk.grid(row=row, column=0, columnspan=2, sticky="w", padx=2, pady=2)
            widgets[opt["name"]] = var
        row += 1

    def run_scrcpy():
        cmd = ["scrcpy"]
        for name, var in widgets.items():
            if isinstance(var, tk.BooleanVar):
                if var.get():
                    cmd.append(name)
            else:
                value = var.get().strip()
                if value:
                    cmd.extend([name, value])
        try:
            subprocess.run(cmd, check=False)
        except FileNotFoundError:
            messagebox.showerror("scrcpy", "scrcpy executable not found in PATH")

    button = ttk.Button(root, text="Run", command=run_scrcpy)
    button.pack(fill="x")

    root.mainloop()


def main():
    opts = parse_options()
    if not opts:
        print("Could not parse scrcpy options from manpage", file=sys.stderr)
        sys.exit(1)
    build_gui(opts)


if __name__ == "__main__":
    main()
