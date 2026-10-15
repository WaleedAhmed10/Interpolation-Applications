import tkinter as tk
from tkinter import ttk, messagebox
from math import factorial, comb

TOL = 1e-10

BG_COLOR = "#1e56a0"
FG_COLOR = "#ffffff"
ENTRY_BG = "#e8f1fb"
OUTPUT_BG = "#d6e6f7"
OUTPUT_FG = "#0b2545"
BUTTON_BG = "#0d3b78"
BUTTON_ACTIVE = "#2f6fc4"

def difference_table(y):
    table = [y[:]]

    while len(table[-1]) > 1:
        previous = table[-1]
        current = [
            previous[i + 1] - previous[i]
            for i in range(len(previous) - 1)
        ]
        table.append(current)

    return table


def table_to_text(x, table):
    lines = ["Difference table (forward differences)"]
    header = f"{'x':>10}"
    for k in range(len(table)):
        header += f"{'f(x)' if k == 0 else f'D{k}f':>12}"
    lines.append(header)

    for i in range(len(x)):
        row = f"{x[i]:>10g}"
        for column in table:
            if i < len(column):
                row += f"{column[i]:>12g}"
            else:
                row += f"{'':>12}"
        lines.append(row)

    return "\n".join(lines)


def interpolate(x, table, query):
    n = len(x)
    h = x[1] - x[0]

    for i in range(n):
        if abs(query - x[i]) < TOL:
            return "TABULATED VALUE", x[i], 0.0, table[0][i]

    interval = next(
        i for i in range(n - 1)
        if x[i] <= query <= x[i + 1]
    )

    if interval < (n - 1) / 2:
        method = "NEWTON FORWARD"
        origin = interval
        x0 = x[origin]
        p = (query - x0) / h
        result = table[0][origin]
        product = 1.0

        for k in range(1, n - origin):
            d = table[k][origin]
            product *= p - (k - 1)
            result += product * d / factorial(k)

            if abs(d) < TOL:
                break

    else:
        method = "NEWTON BACKWARD"
        origin = interval + 1
        x0 = x[origin]
        p = (query - x0) / h
        result = table[0][origin]
        product = 1.0

        for k in range(1, origin + 1):
            d = table[k][origin - k]
            product *= p + (k - 1)
            result += product * d / factorial(k)

            if abs(d) < TOL:
                break

    return method, x0, p, result


def generate_polynomial(x, table):
    h = x[1] - x[0]
    x0 = x[0]
    degree = len(table) - 1
    p_coeff = [0.0] * (degree + 1)
    falling = [1.0]

    for k in range(degree + 1):
        coefficient = table[k][0] / factorial(k)

        for j in range(len(falling)):
            p_coeff[j] += coefficient * falling[j]

        new_falling = [0.0] * (len(falling) + 1)

        for j in range(len(falling)):
            new_falling[j] -= k * falling[j]
            new_falling[j + 1] += falling[j]

        falling = new_falling

    a = 1 / h
    b = -x0 / h
    x_coeff = [0.0] * (degree + 1)

    for k in range(degree + 1):
        for j in range(k + 1):
            x_coeff[j] += (
                p_coeff[k]
                * comb(k, j)
                * a ** j
                * b ** (k - j)
            )

    for i in range(len(x_coeff)):
        if abs(x_coeff[i]) < TOL:
            x_coeff[i] = 0.0

    return degree, x_coeff


def format_polynomial(coefficients):
    terms = []

    for power in range(len(coefficients) - 1, -1, -1):
        c = coefficients[power]

        if abs(c) < TOL:
            continue

        sign = "+" if c > 0 else "-"
        value = abs(c)

        if power == 0:
            term = f"{value:.6f}"
        elif power == 1:
            term = "x" if abs(value - 1) < TOL else f"{value:.6f}x"
        else:
            term = (
                f"x^{power}"
                if abs(value - 1) < TOL
                else f"{value:.6f}x^{power}"
            )

        if not terms:
            terms.append(("-" if c < 0 else "") + term)
        else:
            terms.append(f" {sign} {term}")

    return "P(x) = " + "".join(terms) if terms else "P(x) = 0"


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, highlightthickness=0, bg=BG_COLOR)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)

        self.vbar.pack(side="right", fill="y")
        self.hbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)


        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _on_inner_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):

        needed = self.inner.winfo_reqwidth()
        self.canvas.itemconfig(self.window_id, width=max(event.width, needed))

    def _bind_wheel(self, _event):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shift_wheel)
        self.canvas.bind_all("<Button-4>", self._on_wheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_wheel_linux)

    def _unbind_wheel(self, _event):
        for seq in ("<MouseWheel>", "<Shift-MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(seq)

    def _on_wheel(self, event):
        step = -1 * (event.delta // 120) if abs(event.delta) >= 120 else -1 * event.delta
        self.canvas.yview_scroll(step, "units")

    def _on_shift_wheel(self, event):
        step = -1 * (event.delta // 120) if abs(event.delta) >= 120 else -1 * event.delta
        self.canvas.xview_scroll(step, "units")

    def _on_wheel_linux(self, event):
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")


class App:
    def __init__(self, root):
        self.root = root
        root.title("Newton Forward / Backward Interpolation")
        root.configure(bg=BG_COLOR)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR)
        style.configure("TLabelframe", background=BG_COLOR, bordercolor=FG_COLOR)
        style.configure(
            "TLabelframe.Label", background=BG_COLOR, foreground=FG_COLOR
        )
        style.configure(
            "TEntry", fieldbackground=ENTRY_BG, foreground="#000000"
        )
        style.configure(
            "TButton", background=BUTTON_BG, foreground=FG_COLOR, padding=5
        )
        style.map(
            "TButton",
            background=[("active", BUTTON_ACTIVE), ("disabled", "#5a7fae")],
            foreground=[("disabled", "#c8d6e8")],
        )
        style.configure("TScrollbar", background=BUTTON_BG, troughcolor=BG_COLOR)
        root.geometry("900x700")
        root.minsize(500, 400)

        self.x = None
        self.table = None

        scroll = ScrollableFrame(root)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner
        body.columnconfigure(0, weight=1)

        pad = {"padx": 10, "pady": 5}

        ttk.Label(
            body,
            text="AUTOMATIC NEWTON FORWARD / BACKWARD INTERPOLATION",
            font=("TkDefaultFont", 13, "bold"),
        ).grid(row=0, column=0, sticky="w", **pad)


        data_box = ttk.LabelFrame(body, text="Data")
        data_box.grid(row=1, column=0, sticky="ew", **pad)
        data_box.columnconfigure(1, weight=1)

        ttk.Label(data_box, text="Number of data points:").grid(row=0, column=0, sticky="w", **pad)
        self.n_var = tk.StringVar()
        ttk.Entry(data_box, textvariable=self.n_var, width=10).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(data_box, text="x values (space separated):").grid(row=1, column=0, sticky="w", **pad)
        self.x_var = tk.StringVar()
        ttk.Entry(data_box, textvariable=self.x_var).grid(row=1, column=1, sticky="ew", **pad)

        ttk.Label(data_box, text="f(x) values (space separated):").grid(row=2, column=0, sticky="w", **pad)
        self.y_var = tk.StringVar()
        ttk.Entry(data_box, textvariable=self.y_var).grid(row=2, column=1, sticky="ew", **pad)

        ttk.Button(
            data_box, text="Build Table & Polynomial", command=self.build_table
        ).grid(row=3, column=0, columnspan=2, sticky="w", **pad)


        query_box = ttk.LabelFrame(body, text="Interpolation queries")
        query_box.grid(row=2, column=0, sticky="ew", **pad)

        ttk.Label(query_box, text="Query x:").grid(row=0, column=0, sticky="w", **pad)
        self.q_var = tk.StringVar()
        self.q_entry = ttk.Entry(query_box, textvariable=self.q_var, width=20, state="disabled")
        self.q_entry.grid(row=0, column=1, sticky="w", **pad)
        self.q_entry.bind("<Return>", lambda _e: self.run_query())

        self.q_button = ttk.Button(
            query_box, text="Interpolate", command=self.run_query, state="disabled"
        )
        self.q_button.grid(row=0, column=2, sticky="w", **pad)

        ttk.Button(query_box, text="Clear Output", command=self.clear_output).grid(
            row=0, column=3, sticky="w", **pad
        )


        out_box = ttk.LabelFrame(body, text="Output")
        out_box.grid(row=3, column=0, sticky="nsew", **pad)
        out_box.columnconfigure(0, weight=1)
        out_box.rowconfigure(0, weight=1)
        body.rowconfigure(3, weight=1)

        self.output = tk.Text(
            out_box,
            height=22,
            width=90,
            wrap="none",
            font=("Courier", 10),
            bg=OUTPUT_BG,
            fg=OUTPUT_FG,
        )
        ybar = ttk.Scrollbar(out_box, orient="vertical", command=self.output.yview)
        xbar = ttk.Scrollbar(out_box, orient="horizontal", command=self.output.xview)
        self.output.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set, state="disabled")

        self.output.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")


        self.output.bind("<Enter>", lambda _e: scroll._unbind_wheel(None))
        self.output.bind("<Leave>", lambda _e: scroll._bind_wheel(None))


    def write(self, text=""):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")


    def build_table(self):
        try:
            n = int(self.n_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Number of data points must be an integer.")
            return

        if n < 2:
            messagebox.showerror("Error", "At least 2 data points are required.")
            return

        try:
            x = list(map(float, self.x_var.get().split()))
            y = list(map(float, self.y_var.get().split()))
        except ValueError:
            messagebox.showerror("Error", "x and f(x) values must be numbers.")
            return

        if len(x) != n or len(y) != n:
            messagebox.showerror(
                "Error", "Number of x and f(x) values must be equal to n."
            )
            return

        h = x[1] - x[0]
        if h <= 0:
            messagebox.showerror("Error", "x values must be in increasing order.")
            return

        for i in range(1, n - 1):
            if abs((x[i + 1] - x[i]) - h) > TOL:
                messagebox.showerror("Error", "x values must be equally spaced.")
                return

        self.x = x
        self.table = difference_table(y)

        self.clear_output()
        self.write("=" * 70)
        self.write(table_to_text(x, self.table))

        degree, coefficients = generate_polynomial(x, self.table)
        self.write()
        self.write(f"Maximum degree under the given data : {degree}")
        self.write(format_polynomial(coefficients))
        self.write("=" * 70)
        self.write("Enter a query x and press Interpolate (or Enter).")

        self.q_entry.configure(state="normal")
        self.q_button.configure(state="normal")
        self.q_entry.focus_set()

    def run_query(self):
        if self.x is None:
            return

        raw = self.q_var.get()
        if not raw.strip():
            return

        try:
            query = float(raw)
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Enter a numerical value.")
            return

        x, table, n = self.x, self.table, len(self.x)

        if query < x[0] - TOL or query > x[-1] + TOL:
            self.write(f"\nQuery {query:g} is outside the tabulated range.")
            return

        method, x0, p, result = interpolate(x, table, query)
        self.write()

        if method == "TABULATED VALUE":
            self.write("method : TABULATED VALUE")
            self.write(f"f({query:g}) = {result:g}")
        else:
            interval = next(
                i for i in range(n - 1) if x[i] <= query <= x[i + 1]
            )
            h = x[1] - x[0]
            self.write(
                f"target lies in [{x[interval]:g}, {x[interval + 1]:g}]"
                f" -> method : {method}"
            )
            self.write(f"origin x0 = {x0:g}, h = {h:g}, p = {p:g}")
            self.write(f"f({query:g}) = {result:.10g}")

        self.q_var.set("")
        self.q_entry.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()