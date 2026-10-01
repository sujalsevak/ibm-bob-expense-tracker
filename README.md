# Smart Expense Tracker & Budget Analyzer

A modern dark-theme desktop application built entirely with Python's **built-in `tkinter`** library — zero third-party dependencies. Set your monthly salary, log expenses, watch real-time KPI cards update, and receive an automatic low-balance warning when funds run low.

--- 

## UI Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│  💸 Smart Expense Tracker          Monthly Salary ($) [________] [Set]   │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐ │
│  │  Total Salary   │  │  Total Spent    │  │  Remaining Balance       │ │
│  │  $3,000.00      │  │  $450.00        │  │  $2,550.00  ← green      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────────────────┘ │
├────────────────┬─────────────────────────────────────────────────────────┤
│  Add Expense   │  All Expenses                              12 records   │
│  ──────────── │  ┌────┬────────────┬────────────┬─────────────┬───────┐ │
│  Item: [    ] │  │ #  │ Date       │ Category   │ Description │  Amt  │ │
│  Cat:  [▼   ] │  ├────┼────────────┼────────────┼─────────────┼───────┤ │
│  Amt:  [    ] │  │  1 │ 2025-07-15 │ Food       │ Lunch       │$12.50 │ │
│               │  │  2 │ 2025-07-15 │ Transport  │ Bus pass    │$45.00 │ │
│  [+ Add    ]  │  └────┴────────────┴────────────┴─────────────┴───────┘ │
│  [✕ Delete ]  │                                                          │
│  [↺ Clear  ]  │  TOTAL SPENDING                              $450.00     │
└────────────────┴─────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Details |
|---|---|
| **Salary / Budget Setup** | Enter a monthly salary in the header and click **Set Salary** — KPIs update instantly |
| **KPI Summary Cards** | Three live cards: Total Salary (indigo), Total Spent (amber), Remaining Balance (green → red) |
| **Low Balance Alert** | Balance card turns **red** and a warning popup fires when remaining ≤ $100 |
| **Add Expenses** | Item description, category dropdown (9 presets), positive amount |
| **Delete Expenses** | Select any row → **✕ Delete Selected** → confirm dialog → IDs renumbered |
| **Sortable Table** | Click any column header to sort ascending / descending |
| **Click-to-fill** | Clicking a row fills the form fields for quick review |
| **Persistent Storage** | Everything (salary + expenses) saved to `expenses.json` after every change |
| **Input Validation** | Inline status messages for empty fields, bad amounts, negative salary |

---

## Requirements

- Python **3.10** or later
- **No third-party packages** — only `tkinter`, `json`, `os`, `datetime`, `typing` from the standard library

> `tkinter` ships with the official Python Windows and macOS installers.  
> On Debian/Ubuntu Linux: `sudo apt install python3-tk`

---

## Getting Started

```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker
python app.py
```

The window opens at **1060 × 660 px**, centred on screen, and is fully resizable.

---

## How to Use

### 1. Set your salary
Type your monthly salary in the **top-right header field** and click **Set Salary**. The Total Salary KPI card updates immediately and the low-balance alert is re-armed.

### 2. Add an expense
1. Fill in **Item Description**.
2. Pick a **Category** from the dropdown.
3. Enter a positive **Amount ($)**.
4. Click **＋ Add Expense** — the row appears in the table and all KPIs recalculate.

### 3. Delete an expense
1. Click a row in the table to select it.
2. Click **✕ Delete Selected** and confirm the dialog.

### 4. Low Balance Alert
When `Remaining Balance ≤ $100`:
- The **Remaining Balance** card text turns **red**.
- A **warning popup** appears once per session (re-arms when you set a new salary).

---

## Project Structure

```
expense-tracker/
├── app.py          # Full application (~430 lines, no external deps)
├── expenses.json   # Auto-created data store (salary + expenses)
└── README.md       # This file
```

### Key symbols in [`app.py`](app.py)

| Symbol | Responsibility |
|---|---|
| `load_data()` / `save_data()` | Read/write `expenses.json`; handles legacy list format |
| `btn()` / `dark_entry()` / `field_label()` | Themed widget factory helpers |
| `App` | Main `tk.Tk` subclass — owns all state |
| `App._build_header()` | Top bar with title + salary input |
| `App._build_kpi_row()` | Three summary cards |
| `App._build_form()` | Left panel: inputs + action buttons |
| `App._build_table()` | Right panel: sortable Treeview + total footer |
| `App._refresh_kpis()` | Recalculates totals, updates card colours, triggers alert |
| `App._show_low_balance_alert()` | Warning popup (fires via `after(100,…)` to avoid blocking startup) |

---

## Data Format

`expenses.json` stores both salary and expenses in a single object:

```json
{
  "salary": 3000.00,
  "expenses": [
    {
      "id": 1,
      "date": "2025-07-15",
      "item": "Lunch",
      "category": "Food",
      "amount": 12.50
    }
  ]
}
```

> **Legacy support:** If the file contains a bare JSON array (old format), it is loaded as expenses with salary defaulting to `$0.00`.

---

## Colour Palette

| Role | Token | Hex |
|---|---|---|
| App background | `bg` | `#0f172a` |
| Card surface | `surface` | `#1e293b` |
| Input background | `surface2` | `#273549` |
| Accent (indigo) | `accent` | `#6366f1` |
| Success / balance | `success` | `#22c55e` |
| Warning / spent | `warning` | `#f59e0b` |
| Danger / low balance | `danger` | `#ef4444` |
| Primary text | `text` | `#f1f5f9` |
| Secondary text | `muted` | `#94a3b8` |

---

## License

MIT — free to use and modify.
