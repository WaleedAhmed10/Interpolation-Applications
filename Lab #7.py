import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from math import factorial

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


BLUE_DARK = "#0b3d91"
BLUE_MID = "#1565c0"
BLUE_LIGHT = "#bbdefb"
BLUE_PALE = "#e3f2fd"
WHITE = "#ffffff"

DEFAULT_Y = [0, 2, 4, 6, 8, 10]
DEFAULT_X = [0.0, 1.1, 1.8, 2.4, 2.0, 1.3]


class Interpolator:
    def __init__(self, y, x):
        self.y = np.array(y, dtype=float)
        self.x = np.array(x, dtype=float)
        self.n = len(self.x)
        self.h = self.y[1] - self.y[0]


        self.diff = [self.x.copy()]
        while len(self.diff[-1]) > 1:
            self.diff.append(np.diff(self.diff[-1]))

        span = self.y[-1] - self.y[0]
        self.low = self.y[0] + 0.4 * span
        self.high = self.y[0] + 0.6 * span

    def forward(self, value):
        n, y, h, x, diff = self.n, self.y, self.h, self.x, self.diff
        origin = max(0, min(int((value - y[0]) / h), n - 1))
        p = (value - y[origin]) / h
        result = x[origin]
        product = 1.0
        for k in range(1, n - origin):
            product *= p - k + 1
            result += product * diff[k][origin] / factorial(k)
        return result

    def backward(self, value):
        n, y, h, x, diff = self.n, self.y, self.h, self.x, self.diff
        origin = max(0, min(int(np.ceil((value - y[0]) / h)), n - 1))
        p = (value - y[origin]) / h
        result = x[origin]
        product = 1.0
        for k in range(1, origin + 1):
            product *= p + k - 1
            result += product * diff[k][origin - k] / factorial(k)
        return result

    def stirling(self, value):
        n, y, h, x, diff = self.n, self.y, self.h, self.x, self.diff
        origin = int(round((value - y[0]) / h))
        origin = max(1, min(origin, n - 2))
        p = (value - y[origin]) / h
        result = x[origin]

        for order in range(1, n):
            if order % 2 == 1:
                r = (order - 1) // 2
                left = origin - r - 1
                right = origin - r
                if left < 0 or right + order > n - 1:
                    break
                product = p
                for j in range(1, r + 1):
                    product *= p * p - j * j
                average = (diff[order][left] + diff[order][right]) / 2
                result += product * average / factorial(order)
            else:
                r = order // 2
                index = origin - r
                if index < 0 or index + order >= n:
                    break
                product = p * p
                for j in range(1, r):
                    product *= p * p - j * j
                result += product * diff[order][index] / factorial(order)
        return result

    def method_for(self, value):
        if value < self.low:
            return "Newton Forward"
        if value > self.high:
            return "Newton Backward"
        return "Stirling Central"

    def evaluate(self, value):
        m = self.method_for(value)
        if m == "Newton Forward":
            return self.forward(value)
        if m == "Newton Backward":
            return self.backward(value)
        return self.stirling(value)


class FaceOutlineApp:
    def __init__(self, root):
        self.root = root
        root.title("Lab 7 - Symmetrical Face Outline (Numerical Interpolation)")
        root.geometry("1180x720")
        root.configure(bg=BLUE_PALE)

        self.rows = []
        self.interp = None
        self.y_left = None
        self.x_left = None
        self.stage = 0

        self._style()
        self._build_header()
        self._build_body()
        for yv, xv in zip(DEFAULT_Y, DEFAULT_X):
            self._add_row(yv, xv)
        self._draw()


    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TFrame", background=BLUE_PALE)
        s.configure("Card.TLabelframe", background=BLUE_PALE, bordercolor=BLUE_MID)
        s.configure("Card.TLabelframe.Label", background=BLUE_PALE,
                    foreground=BLUE_DARK, font=("Segoe UI", 10, "bold"))
        s.configure("TLabel", background=BLUE_PALE, foreground=BLUE_DARK, font=("Segoe UI", 10))
        s.configure("Blue.TButton", background=BLUE_MID, foreground=WHITE,
                    font=("Segoe UI", 10, "bold"), padding=7, borderwidth=0)
        s.map("Blue.TButton", background=[("active", BLUE_DARK), ("pressed", BLUE_DARK)])
        s.configure("Light.TButton", background=BLUE_LIGHT, foreground=BLUE_DARK,
                    font=("Segoe UI", 9, "bold"), padding=4, borderwidth=0)
        s.map("Light.TButton", background=[("active", "#90caf9")])
        s.configure("TEntry", fieldbackground=WHITE, foreground=BLUE_DARK)

    def _build_header(self):
        header = tk.Frame(self.root, bg=BLUE_DARK)
        header.pack(fill="x")
        tk.Label(header, text="Symmetrical Face Outline Reconstruction",
                 bg=BLUE_DARK, fg=WHITE, font=("Segoe UI", 17, "bold")).pack(pady=(10, 0))
        tk.Label(header, text="Numerical Interpolation - Newton Forward / Backward & Stirling",
                 bg=BLUE_DARK, fg=BLUE_LIGHT, font=("Segoe UI", 10)).pack(pady=(0, 10))

    def _build_body(self):
        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=10, pady=10)


        left = ttk.Frame(body)
        left.pack(side="left", fill="y", padx=(0, 10))

        data_box = ttk.LabelFrame(left, text="Half-outline data (left side)", style="Card.TLabelframe")
        data_box.pack(fill="x", pady=(0, 8))
        self.table = ttk.Frame(data_box)
        self.table.pack(padx=8, pady=6)
        ttk.Label(self.table, text="y (height)").grid(row=0, column=0, padx=3)
        ttk.Label(self.table, text="x (distance)").grid(row=0, column=1, padx=3)

        btns = ttk.Frame(data_box)
        btns.pack(pady=(0, 8))
        ttk.Button(btns, text="+ Row", style="Light.TButton", command=self._add_row).pack(side="left", padx=3)
        ttk.Button(btns, text="- Row", style="Light.TButton", command=self._remove_row).pack(side="left", padx=3)
        ttk.Button(btns, text="Defaults", style="Light.TButton", command=self._defaults).pack(side="left", padx=3)

        opt_box = ttk.LabelFrame(left, text="Settings", style="Card.TLabelframe")
        opt_box.pack(fill="x", pady=(0, 8))
        r = ttk.Frame(opt_box)
        r.pack(padx=8, pady=6, fill="x")
        ttk.Label(r, text="Interpolated points:").pack(side="left")
        self.points_var = tk.StringVar(value="201")
        ttk.Entry(r, textvariable=self.points_var, width=7).pack(side="left", padx=6)
        self.show_data_var = tk.BooleanVar(value=True)
        self.show_data_var.trace_add("write", lambda *a: self._draw())
        tk.Checkbutton(opt_box, text="Show data points", variable=self.show_data_var,
                       bg=BLUE_PALE, fg=BLUE_DARK, activebackground=BLUE_PALE,
                       selectcolor=WHITE, font=("Segoe UI", 10)).pack(anchor="w", padx=8, pady=(0, 6))

        step_box = ttk.LabelFrame(left, text="Steps", style="Card.TLabelframe")
        step_box.pack(fill="x", pady=(0, 8))
        for text, cmd in [("1. Reconstruct Left Half", self.step_left),
                          ("2. Mirror Right Half", self.step_right),
                          ("3. Plot Complete Outline", self.step_full)]:
            ttk.Button(step_box, text=text, style="Blue.TButton", command=cmd).pack(fill="x", padx=8, pady=4)
        ttk.Button(step_box, text="Reset Plot", style="Light.TButton",
                   command=self.reset).pack(fill="x", padx=8, pady=(2, 8))

        q_box = ttk.LabelFrame(left, text="Estimate x at a given y", style="Card.TLabelframe")
        q_box.pack(fill="x")
        q = ttk.Frame(q_box)
        q.pack(padx=8, pady=6, fill="x")
        ttk.Label(q, text="y =").pack(side="left")
        self.query_var = tk.StringVar(value="5")
        ttk.Entry(q, textvariable=self.query_var, width=8).pack(side="left", padx=6)
        ttk.Button(q, text="Estimate", style="Light.TButton", command=self.estimate).pack(side="left")
        self.result_var = tk.StringVar(value="")
        ttk.Label(q_box, textvariable=self.result_var, wraplength=250).pack(padx=8, pady=(0, 8), anchor="w")


        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        self.fig = Figure(figsize=(6.5, 7), dpi=100, facecolor=BLUE_PALE)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        bar = NavigationToolbar2Tk(self.canvas, right)
        bar.config(background=BLUE_LIGHT)
        bar.update()
        ttk.Button(right, text="Save Plot as PNG", style="Blue.TButton",
                   command=self.save).pack(pady=(6, 0))

        self.status = tk.StringVar(value="Ready. Enter data and follow steps 1 to 3.")
        tk.Label(self.root, textvariable=self.status, bg=BLUE_MID, fg=WHITE,
                 anchor="w", padx=10, font=("Segoe UI", 9)).pack(fill="x", side="bottom")


    def _add_row(self, yv="", xv=""):
        i = len(self.rows) + 1
        ye = ttk.Entry(self.table, width=9, justify="center")
        xe = ttk.Entry(self.table, width=9, justify="center")
        ye.grid(row=i, column=0, padx=3, pady=2)
        xe.grid(row=i, column=1, padx=3, pady=2)
        ye.insert(0, str(yv))
        xe.insert(0, str(xv))
        self.rows.append((ye, xe))

    def _remove_row(self):
        if len(self.rows) <= 4:
            messagebox.showwarning("Rows", "At least 4 data points are required.")
            return
        ye, xe = self.rows.pop()
        ye.destroy()
        xe.destroy()

    def _defaults(self):
        while self.rows:
            self._remove_row_force()
        for yv, xv in zip(DEFAULT_Y, DEFAULT_X):
            self._add_row(yv, xv)
        self.reset()

    def _remove_row_force(self):
        ye, xe = self.rows.pop()
        ye.destroy()
        xe.destroy()

    def _read_data(self):
        try:
            y = [float(r[0].get()) for r in self.rows]
            x = [float(r[1].get()) for r in self.rows]
        except ValueError:
            raise ValueError("All table entries must be numbers.")
        steps = np.diff(y)
        if np.any(steps <= 0):
            raise ValueError("y values must be strictly increasing.")
        if not np.allclose(steps, steps[0]):
            raise ValueError("y values must be equally spaced.")
        try:
            pts = int(self.points_var.get())
            if pts < 10:
                raise ValueError
        except ValueError:
            raise ValueError("Interpolated points must be an integer of at least 10.")
        return y, x, pts


    def step_left(self):
        try:
            y, x, pts = self._read_data()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return
        self.interp = Interpolator(y, x)
        self.y_left = np.linspace(y[0], y[-1], pts)
        self.x_left = np.array([self.interp.evaluate(v) for v in self.y_left])
        self.stage = 1
        self.status.set(f"Left half reconstructed with {pts} points "
                        f"(Forward < {self.interp.low:g}, Stirling {self.interp.low:g}-{self.interp.high:g}, "
                        f"Backward > {self.interp.high:g}).")
        self._draw()

    def step_right(self):
        if self.stage < 1:
            self.step_left()
            if self.stage < 1:
                return
        self.stage = 2
        self.status.set("Right half generated by mirroring across the vertical midline (x -> -x).")
        self._draw()

    def step_full(self):
        if self.stage < 2:
            self.step_right()
            if self.stage < 2:
                return
        self.stage = 3
        self.status.set("Complete symmetrical face outline plotted.")
        self._draw()

    def reset(self):
        self.stage = 0
        self.status.set("Plot reset.")
        self._draw()

    def estimate(self):
        try:
            y, x, _ = self._read_data()
            v = float(self.query_var.get())
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return
        it = Interpolator(y, x)
        if not (y[0] <= v <= y[-1]):
            self.result_var.set(f"y must be between {y[0]:g} and {y[-1]:g}.")
            return
        self.result_var.set(f"x({v:g}) = {it.evaluate(v):.4f}   [{it.method_for(v)}]")


    def _draw(self):
        ax = self.ax
        ax.clear()
        ax.set_facecolor(WHITE)


        data_ok = True
        try:
            y = np.array([float(r[0].get()) for r in self.rows])
            x = np.array([float(r[1].get()) for r in self.rows])
        except ValueError:
            data_ok = False

        if self.show_data_var.get() and data_ok:
            ax.scatter(-x, y, color="#d32f2f", zorder=5, label="Left data points")
            if self.stage >= 2:
                ax.scatter(x, y, color="#2e7d32", zorder=5, label="Mirrored data points")

        if self.stage >= 1:
            if self.stage == 1:
                ax.plot(-self.x_left, self.y_left, color=BLUE_MID, lw=2.2,
                        label="Interpolated left outline")
            elif self.stage == 2:
                ax.plot(-self.x_left, self.y_left, color=BLUE_MID, lw=2.2,
                        label="Interpolated left outline")
                ax.plot(self.x_left, self.y_left, color="#00897b", lw=2.2, ls="--",
                        label="Mirrored right outline")
            else:
                x_full = np.concatenate((-self.x_left[::-1], self.x_left[1:]))
                y_full = np.concatenate((self.y_left[::-1], self.y_left[1:]))
                ax.plot(x_full, y_full, color=BLUE_DARK, lw=2.6, label="Interpolated face outline")
                ax.fill(x_full, y_full, color=BLUE_LIGHT, alpha=0.45)

        ax.axvline(0, color="gray", ls="--", label="Vertical midline")
        ax.set_xlabel("Horizontal distance (x)", color=BLUE_DARK)
        ax.set_ylabel("Vertical position (y)", color=BLUE_DARK)
        titles = {0: "Face Outline Data", 1: "Reconstructed Left Half",
                  2: "Left Half and Mirrored Right Half", 3: "Complete Symmetrical Face Outline"}
        ax.set_title(titles[self.stage], color=BLUE_DARK, fontweight="bold")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, color=BLUE_LIGHT)
        ax.legend(loc="upper right", fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG image", "*.png")])
        if path:
            self.fig.savefig(path, dpi=200, facecolor=self.fig.get_facecolor())
            self.status.set(f"Saved plot to {path}")


if __name__ == "__main__":
    root = tk.Tk()
    FaceOutlineApp(root)
    root.mainloop()