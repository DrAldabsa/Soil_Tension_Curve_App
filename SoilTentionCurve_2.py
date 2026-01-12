# -*- coding: utf-8 -*-
"""
Soil Tension Curve Calculator
Refactored but preserving your original Arabic GUI layout and design.

Dependencies:
    - numpy
    - pandas
    - matplotlib
    - scipy

Icons must be in ./icons:
    Van Genghten.png
    Campbell.png
    BC Model.png

Manual must be:
    Manual.pdf
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.ttk import Combobox
import os, time, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import t

basedir = os.path.dirname(__file__)


# ---------------------------- Model Functions ----------------------------- #

def VG(x, qs, qr, alpha, n):
    """Van Genuchten Model"""
    se = 1. / ((1 + (alpha * x) ** n) ** (1 - 1.0 / n))
    return se * (qs - qr) + qr


def Campbell(x, qs, he, b):
    """Campbell Model"""
    return np.where(x <= he, qs, qs * (x / he) ** (-1.0 / b))


def BC(x, qs, qr, lamda, sib):
    """Brook & Corey Model"""
    return np.where(
        x <= sib,
        qs,
        qr + (qs - qr) * (x / sib) ** (-lamda)
    )


def sig_symbol(p):
    """Return significance symbol for p-value."""
    if p > 0.05:
        return "ns"
    elif p > 0.01:
        return "*"
    elif p > 0.001:
        return "**"
    else:
        return "***"


# ---------------------------- GUI Class ----------------------------- #

class SoilTensionCalculator:
    """Soil Tension Curve Calculator Application"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title(" Soil Tension Curve Calculator")
        self.in_file = tk.StringVar()
        self.in_file_data = []
        self.input_delimiter_str = tk.StringVar(value='","')
        self.output_delimiter_str = tk.StringVar(value='","')

        # Model Initial values
        self.qs = tk.StringVar(value="0.5")
        self.qr = tk.StringVar(value="0.2")
        self.alpha = tk.StringVar(value="0.01")
        self.n = tk.StringVar(value="2")
        self.lamda = tk.StringVar(value="1")
        self.sib = tk.StringVar(value="15")
        self.he = tk.StringVar(value="1")
        self.Campbell_b = tk.StringVar(value="4")

        self.water_content_col = []
        self.tention_col = []
        self.ModelName = [
            "Van Genuchten Model",
            "Camopbell Model",
            "Brook and Corey Model"
        ]
        self.output_formats = [".csv", ".txt"]

        self._build_ui()

    # ---------------------------- Build UI ----------------------------- #

    def _build_ui(self):
        pad = 5

        # -------- File Selection --------
        self.station_labelframe = tk.LabelFrame(self.window, text="أختيار الملف", labelanchor="ne")
        self.station_labelframe.grid(row=0, column=0, padx=pad, pady=pad, sticky=tk.E)

        self.file_select_frame = tk.Frame(self.station_labelframe)
        self.file_select_frame.grid(row=0, column=0, padx=pad, pady=pad, sticky=tk.E)
        tk.Label(self.file_select_frame, text="ملف (.csv or .txt)     ").grid(row=0, column=2, padx=pad, pady=pad)
        ttk.Entry(self.file_select_frame, textvariable=self.in_file,
                  justify="right", width=49).grid(row=0, column=1, padx=pad, pady=pad)
        ttk.Button(self.file_select_frame, text="...", width=4,
                   command=self.choose_file).grid(row=0, column=0, padx=pad + 4, pady=pad)

        # delimiter
        tk.Label(self.station_labelframe, text="الفاصلة بين البيانات      ").grid(
            row=1, column=0, padx=pad, pady=pad, sticky="w")
        ttk.Entry(self.station_labelframe, textvariable=self.input_delimiter_str,
                  justify="right", width=9).grid(row=1, column=1, padx=pad, pady=pad)

        # columns
        tk.Label(self.station_labelframe, text="المحتوى الرطوبي              ").grid(
            row=2, column=0, padx=pad, pady=pad, sticky="w")
        self.sand_select_combo = Combobox(self.station_labelframe, state="readonly", width=46)
        self.sand_select_combo.grid(row=2, column=1, padx=pad, pady=pad)

        tk.Label(self.station_labelframe, text="قياس الجهد                       ").grid(
            row=3, column=0, padx=pad, pady=pad, sticky="w")
        self.silt_select_combo = Combobox(self.station_labelframe, state="readonly", width=46)
        self.silt_select_combo.grid(row=3, column=1, padx=pad, pady=pad)

        # model select
        tk.Label(self.station_labelframe, text="النموذج الرياضي               ").grid(
            row=4, column=0, padx=pad, pady=pad, sticky="w")
        self.model_select_combo = Combobox(
            self.station_labelframe,
            state="readonly",
            values=self.ModelName,
            width=46
        )
        self.model_select_combo.grid(row=4, column=1, padx=pad, pady=pad)

        # output format
        tk.Label(self.station_labelframe, text="صيغة الملف النهائي              ").grid(
            row=5, column=0, padx=pad, pady=pad, sticky="w")
        self.output_format_combo = Combobox(
            self.station_labelframe, state="readonly",
            values=self.output_formats, width=7
        )
        self.output_format_combo.grid(row=5, column=1, padx=pad, pady=pad, sticky="w")
        self.output_delimiter_entry = ttk.Entry(
            self.station_labelframe, textvariable=self.output_delimiter_str,
            justify="right", width=10
        )
        self.output_delimiter_entry.grid(row=5, column=2, padx=pad, pady=pad)

        # -------- Parameters --------
        self.intial_labelframe = tk.LabelFrame(self.window, text="القيم الاولية", labelanchor="ne")
        self.intial_labelframe.grid(row=1, column=0, padx=pad, pady=pad, sticky=tk.E)

        # Van Genuchten
        tk.Label(self.intial_labelframe, text="Van Genuchten Model").grid(row=0, column=0, padx=pad)
        self._add_param("qs", 1, 0)
        self._add_param("qr", 2, 0)
        self._add_param("alpha", 3, 0)
        self._add_param("n", 4, 0)

        # Campbell
        tk.Label(self.intial_labelframe, text="Campbell Model").grid(row=0, column=1, padx=pad)
        self._add_param("qs", 1, 1)
        self._add_param("he", 2, 1)
        self._add_param("Campbell_b", 3, 1)

        # Brook & Corey
        tk.Label(self.intial_labelframe, text="Brook and Corey Model").grid(row=0, column=2, padx=pad)
        self._add_param("qs", 1, 2)
        self._add_param("qr", 2, 2)
        self._add_param("lamda", 3, 2)
        self._add_param("sib", 4, 2)

        # -------- Commands --------
        self.command_labelframe = tk.LabelFrame(self.window, text="الاوامر", labelanchor="ne")
        self.command_labelframe.grid(row=2, column=0, padx=pad, pady=pad, sticky=tk.E)
        ttk.Button(self.command_labelframe, text="المساعدة", command=self.open_help).grid(
            row=0, column=0, padx=2)
        ttk.Button(self.command_labelframe, text="فتح الملف", command=self.open_file).grid(
            row=0, column=1, padx=2)
        ttk.Button(self.command_labelframe, text="تنفيذ", command=self.curve, width=13).grid(
            row=0, column=2, padx=2)

        # -------- Images --------
        self.labelframe2 = tk.LabelFrame(
            self.window, text="معادلات منحنى الوصف الرطوبي", labelanchor='n'
        )
        self.labelframe2.grid(row=0, column=1, padx=10, rowspan = 2)

        self._load_icon("VanGenghten.png", 1, "Van Genghten Model")
        self._load_icon("Campbell.png", 3, "Campbell Model")
        self._load_icon("BCModel.png", 5, "Brook and Corey Model")

        # resize and reposition window
        ws = self.window.winfo_screenwidth()
        hs = self.window.winfo_screenheight()
        x = int((ws / 2) - 251)
        y = int((hs / 2) - 211)
        self.window.geometry(f"832x600+{x}+{y}")
        for i in range(0, 4):
            self.window.grid_rowconfigure(i, weight=1)
        for i in range(0, 5):
            self.window.grid_columnconfigure(i, weight=1)

        self.window.mainloop()

    def _add_param(self, name, r, c):
        """helper for adding parameter entries"""
        val = getattr(self, name)
        tk.Label(self.intial_labelframe, text=name).grid(row=r, column=c * 2, padx=5)
        ttk.Entry(self.intial_labelframe, textvariable=val, width=5).grid(
            row=r, column=c * 2 + 1, padx=5
        )

    def _load_icon(self, filename, row, label):
        """helper to load and display icons"""
        tk.Label(self.labelframe2, text=label).grid(row=row - 1, column=0)
        path = os.path.join(basedir, "icons", filename)
        try:
            img = tk.PhotoImage(file=path)
            ttk.Label(self.labelframe2, image=img).grid(row=row, column=0)
            # keep reference
            setattr(self, filename.replace(" ", "_"), img)
        except Exception:
            ttk.Label(self.labelframe2, text=f"{filename} not found").grid(row=row, column=0)

    # ---------------------------- File I/O ----------------------------- #

    def choose_file(self):
        f = filedialog.askopenfilename(
            parent=self.window,
            title="Select file",
            filetypes=(("CSV files", "*.csv"), ("Text files", "*.txt"), ("all files", "*.*"))
        )
        if f:
            self.load_file(f)

    def load_file(self, filename):
        try:
            with open(filename, 'r') as file:
                self.in_file_data = [
                    row.strip().split(self.input_delimiter_str.get()[1:-1])
                    for row in file.readlines()
                ]
            headers = self.in_file_data[0]
            self.in_file.set(filename)
            self.sand_select_combo.config(values=headers)
            self.silt_select_combo.config(values=headers)
        except Exception as e:
            messagebox.showwarning(" Error", str(e))

    def open_help(self):
        path = os.path.join(basedir, "Manual.pdf")
        try:
            os.startfile(path)
        except:
            messagebox.showwarning(" Error", "Manual not found")

    def open_file(self):
        try:
            os.startfile(self.in_file.get())
        except:
            messagebox.showwarning(" Error", "Cannot open file")

    def return_column(self, col):
        idx = self.in_file_data[0].index(col)
        return np.array([
            float(row[idx]) for row in self.in_file_data[1:]
            if row[idx].replace('.', '', 1).isdigit()
        ])

    # ---------------------------- Run Curve ----------------------------- #

    def curve(self):
        if not self.in_file_data:
            messagebox.showwarning(" Warning", "Please choose a file")
            return

        water = self.return_column(self.sand_select_combo.get())
        tension = self.return_column(self.silt_select_combo.get())

        model = self.model_select_combo.get()
        if not model:
            messagebox.showwarning(" Warning", "Please select a model")
            return

        try:
            # set initial params
            if model == "Van Genuchten Model":
                popt, pcov = curve_fit(
                    VG, tension, water, p0=[
                        float(self.qs.get()), float(self.qr.get()),
                        float(self.alpha.get()), float(self.n.get())
                    ]
                )
            elif model == "Camopbell Model":
                popt, pcov = curve_fit(
                    Campbell, tension, water, p0=[
                        float(self.qs.get()), float(self.he.get()),
                        float(self.Campbell_b.get())
                    ]
                )
            else:
                popt, pcov = curve_fit(
                    BC, tension, water, p0=[
                        float(self.qs.get()), float(self.qr.get()),
                        float(self.lamda.get()), float(self.sib.get())
                    ]
                )
        except Exception as e:
            messagebox.showwarning(" Fit Error", str(e))
            return

        # save results
        file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if file_path:
            with open(file_path, 'w') as fout:
                fout.write(f"Fitted Params: {popt}\nCovariance:\n{pcov}\n")

        # plot
        sim = np.linspace(min(tension), max(tension), 500)
        plt.plot(tension, water, "*", label="Data")
        if model == "Van Genuchten Model":
            plt.plot(sim, VG(sim, *popt), "--", label=model)
        elif model == "Camopbell Model":
            plt.plot(sim, Campbell(sim, *popt), "--", label=model)
        else:
            plt.plot(sim, BC(sim, *popt), "--", label=model)

        plt.xlabel("Soil water potential")
        plt.ylabel("Volumetric water content")
        plt.xscale("log")
        plt.legend()
        plt.show()


# ---------------------------- Main ----------------------------- #

def main():
    SoilTensionCalculator()


if __name__ == '__main__':
    main()

