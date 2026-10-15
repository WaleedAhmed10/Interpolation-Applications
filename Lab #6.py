import math
import re
import tkinter as tk
from tkinter import ttk, messagebox

SPACING_TOL = 1e-8

BG = "#e8f1fb"
DARK = "#0b3d91"
MID = "#1e6fd9"
LIGHT = "#cfe3fa"
HIGHLIGHT = "#a9cdf5"


def difference_table(y):
    table = [list(y)]
    while len(table[-1]) > 1:
        prev = table[-1]
        table.append([prev[i + 1] - prev[i] for i in range(len(prev) - 1)])
    return table


def central_table_text(x, table):
    n = len(x)
    headers = ["x", "f(x)"] + [f"δ{k}f" for k in range(1, len(table))]
    lines = ["".join(f"{h:>12}" for h in headers)]

    for line in range(2 * n - 1):
        cells = []
        cells.append(f"{x[line // 2]:>12.6g}" if line % 2 == 0 else " " * 12)
        for k in range(len(table)):
            idx = (line - k) // 2
            if (line - k) % 2 == 0 and 0 <= idx < len(table[k]):
                cells.append(f"{table[k][idx]:>12.6g}")
            else:
                cells.append(" " * 12)
        lines.append("".join(cells))
    return "\n".join(lines)


def get(table, k, row):
    if 0 <= row < len(table[k]):
        return table[k][row]
    return None


def prod(p, lo, hi):
    result = 1.0
    for j in range(lo, hi + 1):
        result *= (p - j)
    return result


def sq_prod(p, lo, hi):
    result = 1.0
    for j in range(lo, hi + 1):
        result *= (p * p - j * j)
    return result


def stirling(table, m, p):
    result = table[0][m]
    for k in range(1, len(table)):
        r = k // 2
        if k % 2 == 1:
            d1, d2 = get(table, k, m - r - 1), get(table, k, m - r)
            if d1 is None or d2 is None:
                break
            coeff = p * sq_prod(p, 1, r)
            result += coeff * (d1 + d2) / 2 / math.factorial(k)
        else:
            d = get(table, k, m - r)
            if d is None:
                break
            coeff = p * p * sq_prod(p, 1, r - 1)
            result += coeff * d / math.factorial(k)
    return result


def bessel(table, m, p):
    result = table[0][m]
    for k in range(1, len(table)):
        r = k // 2
        if k == 1:
            d = get(table, 1, m)
            if d is None:
                break
            result += p * d
        elif k % 2 == 0:
            d1, d2 = get(table, k, m - r), get(table, k, m + 1 - r)
            if d1 is None or d2 is None:
                break
            coeff = prod(p, -(r - 1), r)
            result += coeff * (d1 + d2) / 2 / math.factorial(k)
        else:
            d = get(table, k, m - r)
            if d is None:
                break
            coeff = prod(p, -(r - 1), r) * (p - 0.5)
            result += coeff * d / math.factorial(k)
    return result


def everett(table, m, p):
    q = 1 - p
    result = q * table[0][m] + p * table[0][m + 1]
    for k in range(2, len(table), 2):
        r = k // 2
        d0, d1 = get(table, k, m - r), get(table, k, m + 1 - r)
        if d0 is None or d1 is None:
            break
        cq = q * sq_prod(q, 1, r)
        cp = p * sq_prod(p, 1, r)
        result += (cq * d0 + cp * d1) / math.factorial(k + 1)
    return result


def gauss_forward(table, m, p):
    result = table[0][m]
    for k in range(1, len(table)):
        r = k // 2
        d = get(table, k, m - r)
        if d is None:
            break
        if k % 2 == 1:
            coeff = prod(p, -r, r)
        else:
            coeff = prod(p, -(r - 1), r)
        result += coeff * d / math.factorial(k)
    return result


def gauss_backward(table, m, p):
    result = table[0][m]
    for k in range(1, len(table)):
        r = k // 2
        if k % 2 == 1:
            d = get(table, k, m - 1 - r)
            coeff = prod(p, -r, r)
        else:
            d = get(table, k, m - r)
            coeff = prod(p, -r, r - 1)
        if d is None:
            break
        result += coeff * d / math.factorial(k)
    return result


FORMULAE = {
    "Stirling": stirling,
    "Bessel": bessel,
    "Everett": everett,
    "Gauss Forward": gauss_forward,
    "Gauss Backward": gauss_backward,
}


def choose_centre(name, pos, n):
    if name == "Stirling":
        return min(max(int(math.floor(pos + 0.5)), 0), n - 1)
    if name == "Gauss Backward":
        return min(max(int(math.ceil(pos - 1e-9)), 1), n - 1)
    return min(max(int(math.floor(pos + 1e-9)), 0), n - 2)


def note_for(name, p):
    if name == "Stirling" and abs(p) > 0.25:
        return "p outside (-0.25, 0.25): less accurate"
    if name == "Bessel" and not (0.25 <= p <= 0.75):
        return "p not near 0.5: less accurate"
    return ""


def interpolate_all(x, y, query):
    n = len(x)
    h = x[1] - x[0]
    table = difference_table(y)
    rows = []
    for name, func in FORMULAE.items():
        m = choose_centre(name, (query - x[0]) / h, n)
        p = (query - x[m]) / h
        rows.append({
            "name": name,
            "x0": x[m],
            "p": p,
            "value": func(table, m, p),
            "note": note_for(name, p),
        })
    return table, h, rows


def parse_numbers(text, label):
    parts = [s for s in re.split(r"[,\s]+", text.strip()) if s]
    try:
        return [float(s) for s in parts]
    except ValueError:
        raise ValueError(f"{label}: please enter numbers only.")


def validate(x, y):
    if len(x) != len(y):
        raise ValueError(f"Number of x values ({len(x)}) and f(x) values ({len(y)}) must be equal.")
    if len(x) < 3:
        raise ValueError("At least 3 data points are required.")
    h = x[1] - x[0]
    if h <= 0:
        raise ValueError("x values must be in increasing order.")
    for i in range(1, len(x) - 1):
        if abs((x[i + 1] - x[i]) - h) > SPACING_TOL * max(1.0, abs(h)):
            raise ValueError("x values must be equally spaced.")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lab 6 - Interpolation with Central Differences")
        self.geometry("900x760")
        self.configure(bg=BG)
        self.apply_theme()
        self.build_inputs()
        self.build_outputs()

    def apply_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=DARK, font=("Arial", 10))
        style.configure("TLabelframe", background=BG, bordercolor=MID)
        style.configure("TLabelframe.Label", background=BG, foreground=DARK,
                        font=("Arial", 10, "bold"))
        style.configure("TButton", background=MID, foreground="white",
                        padding=6, borderwidth=0, font=("Arial", 10, "bold"))
        style.map("TButton", background=[("active", DARK), ("pressed", DARK)])
        style.configure("TEntry", fieldbackground="white", foreground="black",
                        bordercolor=MID)
        style.configure("TCombobox", fieldbackground="white", background=MID,
                        foreground="black", bordercolor=MID, arrowcolor="white")
        style.map("TCombobox", fieldbackground=[("readonly", "white")],
                  foreground=[("readonly", "black")])
        style.configure("Treeview", background="white", fieldbackground="white",
                        foreground="black", bordercolor=MID, rowheight=24)
        style.configure("Treeview.Heading", background=MID, foreground="white",
                        font=("Arial", 10, "bold"), relief="flat")
        style.map("Treeview.Heading", background=[("active", DARK)])
        style.configure("Vertical.TScrollbar", background=MID, troughcolor=LIGHT,
                        arrowcolor="white")
        style.configure("Horizontal.TScrollbar", background=MID, troughcolor=LIGHT,
                        arrowcolor="white")

    def build_inputs(self):
        box = ttk.LabelFrame(self, text=" Input ", padding=8)
        box.pack(fill="x", padx=10, pady=(10, 4))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="x values:").grid(row=0, column=0, sticky="w", pady=2)
        self.x_entry = ttk.Entry(box)
        self.x_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=2)

        ttk.Label(box, text="f(x) values:").grid(row=1, column=0, sticky="w", pady=2)
        self.y_entry = ttk.Entry(box)
        self.y_entry.grid(row=1, column=1, columnspan=3, sticky="ew", pady=2)

        ttk.Label(box, text="Interpolate at x =").grid(row=2, column=0, sticky="w", pady=2)
        self.q_entry = ttk.Entry(box, width=16)
        self.q_entry.grid(row=2, column=1, sticky="w", pady=2)

        ttk.Label(box, text="Actual f(x) (optional):").grid(row=2, column=2, sticky="e", padx=(10, 4))
        self.actual_entry = ttk.Entry(box, width=16)
        self.actual_entry.grid(row=2, column=3, sticky="w")

        ttk.Label(box, text="Formula:").grid(row=3, column=0, sticky="w", pady=2)
        self.formula_box = ttk.Combobox(box, values=list(FORMULAE), state="readonly", width=18)
        self.formula_box.current(1)
        self.formula_box.grid(row=3, column=1, sticky="w", pady=2)

        ttk.Label(box, text="Separate numbers with spaces or commas.",
                  foreground=MID).grid(row=3, column=2, columnspan=2, sticky="e")

        buttons = ttk.Frame(box)
        buttons.grid(row=4, column=0, columnspan=4, pady=(8, 0))
        ttk.Button(buttons, text="Calculate", command=self.calculate).pack(side="left", padx=4)
        ttk.Button(buttons, text="Load Example", command=self.load_example).pack(side="left", padx=4)
        ttk.Button(buttons, text="Clear", command=self.clear).pack(side="left", padx=4)

    def build_outputs(self):
        t_box = ttk.LabelFrame(self, text=" Difference Table (central layout) ", padding=4)
        t_box.pack(fill="both", expand=True, padx=10, pady=4)
        self.table_text = tk.Text(t_box, height=12, font=("Courier New", 10), wrap="none",
                                  bg="white", fg=DARK, relief="flat",
                                  highlightthickness=1, highlightbackground=MID,
                                  highlightcolor=MID)
        sy = ttk.Scrollbar(t_box, orient="vertical", command=self.table_text.yview)
        sx = ttk.Scrollbar(t_box, orient="horizontal", command=self.table_text.xview)
        self.table_text.configure(yscrollcommand=sy.set, xscrollcommand=sx.set, state="disabled")
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.table_text.pack(fill="both", expand=True)

        sel_box = ttk.LabelFrame(self, text=" Selected Formula ", padding=8)
        sel_box.pack(fill="x", padx=10, pady=4)
        self.selected_label = ttk.Label(sel_box, text="-", font=("Arial", 12, "bold"))
        self.selected_label.pack(anchor="w")

        r_box = ttk.LabelFrame(self, text=" Comparison of All Formulae ", padding=4)
        r_box.pack(fill="both", expand=True, padx=10, pady=4)
        cols = ("formula", "x0", "p", "value", "error", "note")
        self.tree = ttk.Treeview(r_box, columns=cols, show="headings", height=6)
        for col, title, width in [
            ("formula", "Formula", 130), ("x0", "x0 used", 80), ("p", "p", 80),
            ("value", "f(x)", 130), ("error", "|Error|", 110), ("note", "Note", 300),
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("selected", background=HIGHLIGHT)

        self.summary_label = ttk.Label(self, text="", font=("Arial", 10, "bold"))
        self.summary_label.pack(anchor="w", padx=12, pady=(2, 10))

    def set_table_text(self, text):
        self.table_text.configure(state="normal")
        self.table_text.delete("1.0", "end")
        self.table_text.insert("1.0", text)
        self.table_text.configure(state="disabled")

    def load_example(self):
        self.clear()
        self.x_entry.insert(0, "30 35 40 45 50 55 60")
        self.y_entry.insert(0, "0.5000 0.5736 0.6428 0.7071 0.7660 0.8192 0.8660")
        self.q_entry.insert(0, "42")
        self.actual_entry.insert(0, "0.669131")

    def clear(self):
        for entry in (self.x_entry, self.y_entry, self.q_entry, self.actual_entry):
            entry.delete(0, "end")
        self.set_table_text("")
        self.tree.delete(*self.tree.get_children())
        self.selected_label.config(text="-")
        self.summary_label.config(text="")

    def calculate(self):
        try:
            x = parse_numbers(self.x_entry.get(), "x values")
            y = parse_numbers(self.y_entry.get(), "f(x) values")
            validate(x, y)

            q_text = self.q_entry.get().strip()
            if not q_text:
                raise ValueError("Enter the x value at which to interpolate.")
            query = float(q_text)
            if query < x[0] or query > x[-1]:
                raise ValueError("The x value is outside the tabulated range.")

            actual = None
            if self.actual_entry.get().strip():
                actual = float(self.actual_entry.get())
        except ValueError as err:
            messagebox.showerror("Input error", str(err))
            return

        table, h, rows = interpolate_all(x, y, query)

        self.set_table_text(central_table_text(x, table))

        selected = self.formula_box.get()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            error = f"{abs(row['value'] - actual):.3e}" if actual is not None else "-"
            tag = ("selected",) if row["name"] == selected else ()
            self.tree.insert("", "end", tags=tag, values=(
                row["name"], f"{row['x0']:g}", f"{row['p']:.4f}",
                f"{row['value']:.8f}", error, row["note"]))

        chosen = next(r for r in rows if r["name"] == selected)
        self.selected_label.config(
            text=f"{selected}:  f({query:g}) = {chosen['value']:.8f}     (h = {h:g}, p = {chosen['p']:.4f})")

        values = [r["value"] for r in rows]
        average = sum(values) / len(values)
        spread = max(values) - min(values)
        text = f"Average of all formulae = {average:.8f}     Spread (max - min) = {spread:.3e}"
        if actual is not None:
            best = min(rows, key=lambda r: abs(r["value"] - actual))
            text += f"     Most accurate: {best['name']}"
        self.summary_label.config(text=text)


if __name__ == "__main__":
    App().mainloop()