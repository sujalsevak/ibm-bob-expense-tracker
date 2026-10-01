"""
Smart Expense Tracker & Budget Analyzer
Dark / Light theme toggle + embedded matplotlib financial chart.
All data (salary + expenses) persisted in expenses.json.
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import matplotlib 
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ── Persistence ───────────────────────────────────────────────────────────────

DATA_FILE = "expenses.json"


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"salary": 0.0, "expenses": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            return {"salary": 0.0, "expenses": raw}
        if isinstance(raw, dict):
            return {
                "salary": float(raw.get("salary", 0.0)),
                "expenses": (raw["expenses"]
                             if isinstance(raw.get("expenses"), list)
                             else []),
            }
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return {"salary": 0.0, "expenses": []}


def save_data(salary: float, expenses: list) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"salary": salary, "expenses": expenses},
                  f, indent=2, ensure_ascii=False)


# ── Colour palettes ───────────────────────────────────────────────────────────

DARK: dict[str, str] = {
    "bg":        "#0f172a",
    "surface":   "#1e293b",
    "surface2":  "#273549",
    "border":    "#334155",
    "text":      "#f1f5f9",
    "muted":     "#94a3b8",
    "accent":    "#6366f1",
    "accent_h":  "#4f46e5",
    "success":   "#22c55e",
    "warning":   "#f59e0b",
    "danger":    "#ef4444",
    "danger_h":  "#dc2626",
    "row_odd":   "#1a2942",
    "row_even":  "#1e293b",
    "sel":       "#6366f1",
    "chart_bg":  "#1e293b",
    "chart_fg":  "#94a3b8",
    "chart_grid":"#334155",
}

LIGHT: dict[str, str] = {
    "bg":        "#f8fafc",
    "surface":   "#ffffff",
    "surface2":  "#f1f5f9",
    "border":    "#e2e8f0",
    "text":      "#0f172a",
    "muted":     "#64748b",
    "accent":    "#6366f1",
    "accent_h":  "#4f46e5",
    "success":   "#16a34a",
    "warning":   "#d97706",
    "danger":    "#dc2626",
    "danger_h":  "#b91c1c",
    "row_odd":   "#f8fafc",
    "row_even":  "#ffffff",
    "sel":       "#6366f1",
    "chart_bg":  "#ffffff",
    "chart_fg":  "#64748b",
    "chart_grid":"#e2e8f0",
}

# Active palette — mutable dict updated on theme switch
C: dict[str, str] = dict(DARK)

CATEGORIES: list[str] = [
    "Food", "Transport", "Housing", "Health",
    "Entertainment", "Shopping", "Utilities", "Education", "Other",
]

FF = "Segoe UI"

# Chart bar colours (same in both themes)
BAR_SALARY   = "#38bdf8"
BAR_EXPENSED = "#f87171"
BAR_SAVED    = "#4ade80"


# ── Widget factories ──────────────────────────────────────────────────────────

def make_btn(parent: tk.Widget, text: str, cmd,
             color: str = "", hover: str = "",
             fg: str = "", font_size: int = 10, pady: int = 9) -> tk.Button:
    bg   = color or C["accent"]
    hov  = hover or C["accent_h"]
    fgc  = fg    or C["text"]
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fgc, activebackground=hov, activeforeground=fgc,
        font=(FF, font_size, "bold"), relief="flat", bd=0,
        cursor="hand2", padx=16, pady=pady,
    )
    b.bind("<Enter>", lambda _: b.config(bg=hov))
    b.bind("<Leave>", lambda _: b.config(bg=bg))
    return b


def make_entry(parent: tk.Widget, textvariable: tk.StringVar,
               width: int = 20) -> tk.Entry:
    return tk.Entry(
        parent, textvariable=textvariable, width=width,
        bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
        relief="flat", font=(FF, 10),
        highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["accent"],
    )


def make_label(parent: tk.Widget, text: str, role: str = "muted") -> tk.Label:
    return tk.Label(parent, text=text,
                    bg=C["surface"], fg=C[role], font=(FF, 9))


def make_hdiv(parent: tk.Widget, pady: tuple = (0, 0)) -> tk.Frame:
    f = tk.Frame(parent, bg=C["border"], height=1)
    f.pack(fill="x", pady=pady)
    return f


# ── Main application ──────────────────────────────────────────────────────────

class App(tk.Tk):

    LOW_BALANCE_THRESHOLD = 100.0

    def __init__(self) -> None:
        super().__init__()
        self.title("Smart Expense Tracker & Budget Analyzer")
        self.geometry("1060x780")
        self.minsize(860, 680)
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self._center()

        data = load_data()
        self._salary: float = data["salary"]
        self._expenses: list[dict] = data["expenses"]
        self._alert_shown: bool = False
        self._is_dark: bool = True        # current theme flag

        # Forward-declared widget references
        self._kpi_salary:  tk.Label
        self._kpi_spent:   tk.Label
        self._kpi_balance: tk.Label

        # Collected for theme repaint
        self._themeable: list[tk.Widget] = []

        self._build_ui()
        self._refresh_kpis()
        self._refresh_table()
        self._refresh_chart()

    # ── Centering ─────────────────────────────────────────────────────────────

    def _center(self) -> None:
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1060x780+{(sw-1060)//2}+{(sh-780)//2}")

    # ── Top-level build ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()
        self._build_kpi_row()
        self._build_middle()     # form (left) + table (right)
        self._build_chart_row()  # full-width chart strip below

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        self._hdr_frame = tk.Frame(self, bg=C["bg"], height=64)
        self._hdr_frame.pack(fill="x", side="top")
        self._hdr_frame.pack_propagate(False)

        # App title
        self._hdr_title = tk.Label(
            self._hdr_frame, text="💸  Smart Expense Tracker",
            bg=C["bg"], fg=C["text"], font=(FF, 15, "bold"))
        self._hdr_title.pack(side="left", padx=24, pady=18)

        # Right-side controls area
        ctrl = tk.Frame(self._hdr_frame, bg=C["bg"])
        ctrl.pack(side="right", padx=24, pady=12)

        # Theme toggle button
        self._btn_theme = tk.Button(
            ctrl, text="☀️  Light Mode",
            command=self._toggle_theme,
            bg=C["surface2"], fg=C["text"],
            activebackground=C["border"], activeforeground=C["text"],
            font=(FF, 9, "bold"), relief="flat", bd=0,
            cursor="hand2", padx=12, pady=5,
        )
        self._btn_theme.pack(side="left", padx=(0, 12))

        # Salary label + entry + button
        self._hdr_sal_lbl = tk.Label(ctrl, text="Monthly Salary ($)",
                                     bg=C["bg"], fg=C["muted"], font=(FF, 9))
        self._hdr_sal_lbl.pack(side="left", padx=(0, 6))

        self._var_salary = tk.StringVar(
            value=f"{self._salary:.2f}" if self._salary else "")
        self._salary_entry = tk.Entry(
            ctrl, textvariable=self._var_salary, width=12,
            bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
            relief="flat", font=(FF, 10),
            highlightthickness=1,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
        )
        self._salary_entry.pack(side="left", padx=(0, 8))

        self._btn_salary = make_btn(ctrl, "Set Salary", self._on_set_salary,
                                    color=C["accent"], hover=C["accent_h"],
                                    font_size=9, pady=5)
        self._btn_salary.pack(side="left")

        # Bottom divider
        self._hdr_div = tk.Frame(self, bg=C["border"], height=1)
        self._hdr_div.pack(fill="x", side="top")

    # ── KPI cards ─────────────────────────────────────────────────────────────

    def _build_kpi_row(self) -> None:
        self._kpi_row_frame = tk.Frame(self, bg=C["bg"])
        self._kpi_row_frame.pack(fill="x", padx=20, pady=(16, 0))
        self._kpi_row_frame.columnconfigure((0, 1, 2), weight=1, uniform="kpi")

        card_cfg = [
            ("Total Salary",      "$0.00", C["accent"],  "_kpi_salary"),
            ("Total Spent",       "$0.00", C["warning"], "_kpi_spent"),
            ("Remaining Balance", "$0.00", C["success"], "_kpi_balance"),
        ]
        self._kpi_cards: list[tk.Frame] = []
        self._kpi_title_labels: list[tk.Label] = []

        for col, (title, default, color, attr) in enumerate(card_cfg):
            card = tk.Frame(self._kpi_row_frame, bg=C["surface"],
                            padx=20, pady=14)
            card.grid(row=0, column=col,
                      padx=(0 if col == 0 else 8, 0), sticky="ew")
            self._kpi_cards.append(card)

            title_lbl = tk.Label(card, text=title, bg=C["surface"],
                                 fg=C["muted"], font=(FF, 9, "bold"))
            title_lbl.pack(anchor="w")
            self._kpi_title_labels.append(title_lbl)

            val_lbl = tk.Label(card, text=default, bg=C["surface"],
                               fg=color, font=(FF, 20, "bold"))
            val_lbl.pack(anchor="w", pady=(4, 0))
            setattr(self, attr, val_lbl)

    # ── Middle: form + table ──────────────────────────────────────────────────

    def _build_middle(self) -> None:
        self._mid_frame = tk.Frame(self, bg=C["bg"])
        self._mid_frame.pack(fill="both", expand=True, padx=20, pady=16)
        self._mid_frame.columnconfigure(1, weight=1)
        self._mid_frame.rowconfigure(0, weight=1)

        self._build_form(self._mid_frame)
        self._build_table(self._mid_frame)

    # ── Form panel ────────────────────────────────────────────────────────────

    def _build_form(self, parent: tk.Widget) -> None:
        self._form_panel = tk.Frame(parent, bg=C["surface"], width=240)
        self._form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._form_panel.grid_propagate(False)
        self._form_panel.columnconfigure(0, weight=1)

        self._form_title = tk.Label(
            self._form_panel, text="Add Expense",
            bg=C["surface"], fg=C["text"], font=(FF, 11, "bold"))
        self._form_title.pack(anchor="w", padx=16, pady=(16, 4))

        self._form_div = make_hdiv(self._form_panel, pady=(0, 12))

        inner = tk.Frame(self._form_panel, bg=C["surface"])
        inner.pack(fill="x", padx=16)
        inner.columnconfigure(0, weight=1)
        self._form_inner = inner

        # Item
        self._lbl_item = tk.Label(inner, text="Item Description",
                                  bg=C["surface"], fg=C["muted"], font=(FF, 9))
        self._lbl_item.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self._var_item = tk.StringVar()
        self._entry_item = tk.Entry(
            inner, textvariable=self._var_item, width=20,
            bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
            relief="flat", font=(FF, 10),
            highlightthickness=1, highlightbackground=C["border"],
            highlightcolor=C["accent"])
        self._entry_item.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Category
        self._lbl_cat = tk.Label(inner, text="Category",
                                 bg=C["surface"], fg=C["muted"], font=(FF, 9))
        self._lbl_cat.grid(row=2, column=0, sticky="w", pady=(0, 2))
        self._var_cat = tk.StringVar(value=CATEGORIES[0])
        self._style = ttk.Style(self)
        self._style.theme_use("clam")
        self._apply_combobox_style()
        self._combo = ttk.Combobox(inner, textvariable=self._var_cat,
                                   values=CATEGORIES, state="readonly",
                                   font=(FF, 10), style="App.TCombobox")
        self._combo.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # Amount
        self._lbl_amt = tk.Label(inner, text="Amount ($)",
                                 bg=C["surface"], fg=C["muted"], font=(FF, 9))
        self._lbl_amt.grid(row=4, column=0, sticky="w", pady=(0, 2))
        self._var_amount = tk.StringVar()
        self._entry_amt = tk.Entry(
            inner, textvariable=self._var_amount, width=20,
            bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
            relief="flat", font=(FF, 10),
            highlightthickness=1, highlightbackground=C["border"],
            highlightcolor=C["accent"])
        self._entry_amt.grid(row=5, column=0, sticky="ew", pady=(0, 20))

        # Buttons
        self._btn_add = make_btn(inner, "＋  Add Expense", self._on_add)
        self._btn_add.grid(row=6, column=0, sticky="ew", pady=(0, 8))

        self._btn_del = make_btn(inner, "✕  Delete Selected", self._on_delete,
                                 color=C["danger"], hover=C["danger_h"])
        self._btn_del.grid(row=7, column=0, sticky="ew", pady=(0, 8))

        self._btn_clr = make_btn(inner, "↺  Clear Fields", self._clear_form,
                                 color=C["border"], hover=C["surface2"],
                                 fg=C["muted"])
        self._btn_clr.grid(row=8, column=0, sticky="ew")

        self._lbl_status = tk.Label(
            self._form_panel, text="", bg=C["surface"],
            fg=C["success"], font=(FF, 9), wraplength=210, justify="center")
        self._lbl_status.pack(pady=(12, 8), padx=16)

    # ── Table panel ───────────────────────────────────────────────────────────

    def _build_table(self, parent: tk.Widget) -> None:
        self._tbl_panel = tk.Frame(parent, bg=C["surface"])
        self._tbl_panel.grid(row=0, column=1, sticky="nsew")
        self._tbl_panel.columnconfigure(0, weight=1)
        self._tbl_panel.rowconfigure(1, weight=1)

        # Panel header
        hdr = tk.Frame(self._tbl_panel, bg=C["surface"])
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        hdr.columnconfigure(1, weight=1)
        self._tbl_title = tk.Label(hdr, text="All Expenses",
                                   bg=C["surface"], fg=C["text"],
                                   font=(FF, 11, "bold"))
        self._tbl_title.grid(row=0, column=0, sticky="w")
        self._lbl_count = tk.Label(hdr, text="", bg=C["surface"],
                                   fg=C["muted"], font=(FF, 9))
        self._lbl_count.grid(row=0, column=1, sticky="e")

        # Treeview style
        self._apply_treeview_style()

        tf = tk.Frame(self._tbl_panel, bg=C["surface"])
        tf.grid(row=1, column=0, sticky="nsew", padx=16)
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)
        self._tf = tf

        cols = ("id", "date", "category", "item", "amount")
        self._tree = ttk.Treeview(tf, columns=cols, show="headings",
                                  style="App.Treeview", selectmode="browse")

        col_defs: list[tuple[str, str]] = [
            ("id",       "#"),
            ("date",     "Date"),
            ("category", "Category"),
            ("item",     "Description"),
            ("amount",   "Amount"),
        ]
        for cid, heading_text in col_defs:
            self._tree.heading(cid, text=heading_text, anchor="center",
                               command=lambda c=cid: self._sort_by(c))
            self._tree.column(cid, width=120, minwidth=60,
                              anchor="center", stretch=True)

        self._tree.tag_configure("odd",  background=C["row_odd"])
        self._tree.tag_configure("even", background=C["row_even"])

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self._tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Footer total bar
        self._footer = tk.Frame(self._tbl_panel, bg=C["bg"], height=46)
        self._footer.grid(row=2, column=0, sticky="ew")
        self._footer.grid_propagate(False)
        self._footer.columnconfigure(1, weight=1)
        self._footer_lbl = tk.Label(
            self._footer, text="  TOTAL SPENDING",
            bg=C["bg"], fg=C["muted"], font=(FF, 9, "bold"))
        self._footer_lbl.grid(row=0, column=0, sticky="w", padx=16, pady=14)
        self._lbl_footer_total = tk.Label(
            self._footer, text="$0.00",
            bg=C["bg"], fg=C["warning"], font=(FF, 14, "bold"))
        self._lbl_footer_total.grid(row=0, column=1, sticky="e", padx=20)

    # ── Chart row ─────────────────────────────────────────────────────────────

    def _build_chart_row(self) -> None:
        self._chart_frame = tk.Frame(self, bg=C["bg"], height=220)
        self._chart_frame.pack(fill="x", padx=20, pady=(0, 16))
        self._chart_frame.pack_propagate(False)

        self._fig = Figure(figsize=(1, 1), dpi=96)
        self._fig.patch.set_facecolor(C["chart_bg"])

        self._ax = self._fig.add_subplot(111)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self._chart_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Style helpers (called on build + theme switch) ────────────────────────

    def _apply_combobox_style(self) -> None:
        self._style.configure(
            "App.TCombobox",
            fieldbackground=C["surface2"],
            background=C["surface2"],
            foreground=C["text"],
            arrowcolor=C["muted"],
            bordercolor=C["border"],
            lightcolor=C["border"],
            darkcolor=C["border"],
            selectbackground=C["accent"],
            selectforeground=C["text"],
        )
        self._style.map(
            "App.TCombobox",
            fieldbackground=[("readonly", C["surface2"])],
            foreground=[("readonly", C["text"])],
            selectbackground=[("readonly", C["accent"])],
            selectforeground=[("readonly", C["text"])],
        )

    def _apply_treeview_style(self) -> None:
        self._style.configure(
            "App.Treeview",
            background=C["surface"],
            foreground=C["text"],
            fieldbackground=C["surface"],
            rowheight=32,
            borderwidth=0,
            font=(FF, 10),
        )
        self._style.configure(
            "App.Treeview.Heading",
            background=C["border"],
            foreground=C["muted"],
            font=(FF, 9, "bold"),
            relief="flat",
        )
        self._style.map(
            "App.Treeview",
            background=[("selected", C["sel"])],
            foreground=[("selected", C["text"])],
        )
        self._style.map(
            "App.Treeview.Heading",
            background=[("active", C["accent"])],
        )

    # ── Theme toggle ──────────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        self._is_dark = not self._is_dark
        palette = DARK if self._is_dark else LIGHT
        C.update(palette)

        # Update toggle button label and colours
        if self._is_dark:
            self._btn_theme.config(
                text="☀️  Light Mode",
                bg=C["surface2"], fg=C["text"],
                activebackground=C["border"])
        else:
            self._btn_theme.config(
                text="🌙  Dark Mode",
                bg=C["surface2"], fg=C["text"],
                activebackground=C["border"])
        self._btn_theme.bind("<Enter>",
                             lambda _: self._btn_theme.config(bg=C["border"]))
        self._btn_theme.bind("<Leave>",
                             lambda _: self._btn_theme.config(bg=C["surface2"]))

        # Root and major frames
        self.configure(bg=C["bg"])
        for w in (self._hdr_frame, self._hdr_div, self._kpi_row_frame,
                  self._mid_frame, self._chart_frame):
            w.configure(bg=C["bg"])

        # Header widgets
        self._hdr_title.configure(bg=C["bg"], fg=C["text"])
        self._hdr_sal_lbl.configure(bg=C["bg"], fg=C["muted"])
        self._salary_entry.configure(
            bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
            highlightbackground=C["border"])

        # KPI cards
        for card, title_lbl in zip(self._kpi_cards, self._kpi_title_labels):
            card.configure(bg=C["surface"])
            title_lbl.configure(bg=C["surface"], fg=C["muted"])
        # KPI value labels keep their semantic colour; only bg changes
        for attr in ("_kpi_salary", "_kpi_spent", "_kpi_balance"):
            lbl: tk.Label = getattr(self, attr)
            lbl.configure(bg=C["surface"])

        # Form panel
        self._form_panel.configure(bg=C["surface"])
        self._form_title.configure(bg=C["surface"], fg=C["text"])
        self._form_div.configure(bg=C["border"])
        self._form_inner.configure(bg=C["surface"])
        self._lbl_status.configure(bg=C["surface"])
        for lbl in (self._lbl_item, self._lbl_cat, self._lbl_amt):
            lbl.configure(bg=C["surface"], fg=C["muted"])
        for entry in (self._entry_item, self._entry_amt):
            entry.configure(bg=C["surface2"], fg=C["text"],
                            insertbackground=C["text"],
                            highlightbackground=C["border"])
        self._apply_combobox_style()

        # Action buttons
        self._btn_add.configure(
            bg=C["accent"], fg=C["text"],
            activebackground=C["accent_h"])
        self._btn_add.bind("<Enter>",
                           lambda _: self._btn_add.config(bg=C["accent_h"]))
        self._btn_add.bind("<Leave>",
                           lambda _: self._btn_add.config(bg=C["accent"]))

        self._btn_del.configure(
            bg=C["danger"], fg=C["text"],
            activebackground=C["danger_h"])
        self._btn_del.bind("<Enter>",
                           lambda _: self._btn_del.config(bg=C["danger_h"]))
        self._btn_del.bind("<Leave>",
                           lambda _: self._btn_del.config(bg=C["danger"]))

        self._btn_clr.configure(
            bg=C["border"], fg=C["muted"],
            activebackground=C["surface2"])
        self._btn_clr.bind("<Enter>",
                           lambda _: self._btn_clr.config(bg=C["surface2"]))
        self._btn_clr.bind("<Leave>",
                           lambda _: self._btn_clr.config(bg=C["border"]))

        self._btn_salary.configure(
            bg=C["accent"], fg=C["text"],
            activebackground=C["accent_h"])

        # Table panel
        self._tbl_panel.configure(bg=C["surface"])
        self._tbl_title.configure(bg=C["surface"], fg=C["text"])
        self._lbl_count.configure(bg=C["surface"], fg=C["muted"])
        self._tf.configure(bg=C["surface"])
        self._footer.configure(bg=C["bg"])
        self._footer_lbl.configure(bg=C["bg"], fg=C["muted"])
        self._lbl_footer_total.configure(bg=C["bg"])

        # Treeview style + row tags
        self._apply_treeview_style()
        self._tree.tag_configure("odd",  background=C["row_odd"])
        self._tree.tag_configure("even", background=C["row_even"])

        # Chart
        self._refresh_chart()

    # ── Sorting ───────────────────────────────────────────────────────────────

    _sort_rev: dict[str, bool] = {}

    def _sort_by(self, col: str) -> None:
        rev = not self._sort_rev.get(col, False)
        self._sort_rev[col] = rev
        self._expenses.sort(key=lambda e: e.get(col, ""), reverse=rev)
        self._refresh_table()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_set_salary(self) -> None:
        raw = self._var_salary.get().strip()
        try:
            value = float(raw)
            if value < 0:
                raise ValueError
        except ValueError:
            self._set_status("Enter a valid non-negative salary.", error=True)
            return
        self._salary = round(value, 2)
        save_data(self._salary, self._expenses)
        self._alert_shown = False
        self._refresh_kpis()
        self._refresh_chart()
        self._set_status(f"Salary set to ${self._salary:,.2f}")

    def _on_add(self) -> None:
        item = self._var_item.get().strip()
        category = self._var_cat.get().strip()
        raw = self._var_amount.get().strip()

        if not item:
            self._set_status("Item description is required.", error=True)
            return
        try:
            amount = float(raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            self._set_status("Amount must be a positive number.", error=True)
            return

        entry = {
            "id": len(self._expenses) + 1,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "item": item,
            "category": category.title(),
            "amount": round(amount, 2),
        }
        self._expenses.append(entry)
        save_data(self._salary, self._expenses)
        self._refresh_table()
        self._refresh_kpis()
        self._refresh_chart()
        self._clear_form()
        self._set_status(f"Added: {entry['item']} (${entry['amount']:.2f})")
        children = self._tree.get_children()
        if children:
            self._tree.see(children[-1])
            self._tree.selection_set(children[-1])

    def _on_delete(self) -> None:
        sel = self._tree.selection()
        if not sel:
            self._set_status("Select a row to delete first.", error=True)
            return
        vals = self._tree.item(sel[0])["values"]
        row_id, name = vals[0], vals[3]
        if not messagebox.askyesno(
                "Confirm Delete",
                f'Delete expense #{row_id} — "{name}"?',
                parent=self):
            return
        self._expenses = [e for e in self._expenses if e["id"] != row_id]
        for i, e in enumerate(self._expenses, 1):
            e["id"] = i
        save_data(self._salary, self._expenses)
        self._refresh_table()
        self._refresh_kpis()
        self._refresh_chart()
        self._set_status(f"Expense #{row_id} deleted.")

    def _on_row_select(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self._tree.selection()
        if not sel:
            return
        vals = self._tree.item(sel[0])["values"]
        self._var_item.set(vals[3])
        self._var_cat.set(vals[2])
        self._var_amount.set(str(vals[4]).replace("$", "").strip())

    def _clear_form(self) -> None:
        self._var_item.set("")
        self._var_cat.set(CATEGORIES[0])
        self._var_amount.set("")
        self._tree.selection_remove(self._tree.selection())

    def _set_status(self, msg: str, error: bool = False) -> None:
        self._lbl_status.config(
            text=msg, fg=C["danger"] if error else C["success"])
        self.after(4000, lambda: self._lbl_status.config(text=""))

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for i, e in enumerate(self._expenses):
            tag = "odd" if i % 2 else "even"
            self._tree.insert(
                "", "end", iid=f"r{e['id']}",
                values=(e["id"], e["date"], e["category"],
                        e["item"], f"${e['amount']:.2f}"),
                tags=(tag,))
        n = len(self._expenses)
        self._lbl_count.config(text=f"{n} record{'s' if n != 1 else ''}")
        total = round(sum(e["amount"] for e in self._expenses), 2)
        self._lbl_footer_total.config(text=f"${total:,.2f}")

    def _refresh_kpis(self) -> None:
        total_spent = round(sum(e["amount"] for e in self._expenses), 2)
        remaining   = round(self._salary - total_spent, 2)

        self._kpi_salary.config(text=f"${self._salary:,.2f}")
        self._kpi_spent.config(text=f"${total_spent:,.2f}")

        bal_color = C["danger"] if remaining <= self.LOW_BALANCE_THRESHOLD \
            else C["success"]
        self._kpi_balance.config(text=f"${remaining:,.2f}", fg=bal_color)

        if (remaining <= self.LOW_BALANCE_THRESHOLD
                and not self._alert_shown and self._salary > 0):
            self._alert_shown = True
            self.after(100, self._show_low_balance_alert)

    def _refresh_chart(self) -> None:
        """Redraw the financial overview bar chart using current theme colours."""
        total_spent = round(sum(e["amount"] for e in self._expenses), 2)
        remaining   = max(0.0, round(self._salary - total_spent, 2))

        self._ax.clear()
        self._fig.patch.set_facecolor(C["chart_bg"])
        self._ax.set_facecolor(C["chart_bg"])

        labels  = ["Total Salary", "Total Expensed", "Saved / Remaining"]
        values  = [self._salary, total_spent, remaining]
        colours = [BAR_SALARY, BAR_EXPENSED, BAR_SAVED]

        bars = self._ax.bar(labels, values, color=colours,
                            width=0.45, zorder=3)

        # Value labels on top of each bar
        for bar, val in zip(bars, values):
            if val > 0:
                self._ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + (max(values) * 0.015 if max(values) else 1),
                    f"${val:,.0f}",
                    ha="center", va="bottom",
                    color=C["text"], fontsize=9,
                    fontfamily=FF,
                )

        # Axes cosmetics
        self._ax.set_title("Financial Overview",
                           color=C["text"], fontsize=11,
                           fontweight="bold", pad=10, fontfamily=FF)
        self._ax.tick_params(colors=C["chart_fg"], labelsize=9)
        for spine in self._ax.spines.values():
            spine.set_edgecolor(C["chart_grid"])
        self._ax.yaxis.grid(True, color=C["chart_grid"],
                            linestyle="--", linewidth=0.6, zorder=0)
        self._ax.set_axisbelow(True)
        self._ax.tick_params(axis="x", colors=C["text"])
        self._ax.tick_params(axis="y", colors=C["chart_fg"])

        # Y-axis label
        self._ax.set_ylabel("Amount ($)", color=C["chart_fg"],
                            fontsize=9, fontfamily=FF)

        # Format y-axis ticks with $ sign
        self._ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(
                lambda x, _: f"${x:,.0f}"))

        self._fig.tight_layout(pad=1.2)
        self._canvas.draw()

    def _show_low_balance_alert(self) -> None:
        remaining = round(
            self._salary - sum(e["amount"] for e in self._expenses), 2)
        messagebox.showwarning(
            "⚠️  Low Balance Alert",
            f"Your remaining balance is ${remaining:,.2f}.\n\n"
            "You have reached or fallen below the $100 threshold.\n"
            "Consider reviewing your expenses.",
            parent=self,
        )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
