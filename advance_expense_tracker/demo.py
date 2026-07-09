"""
Family Budget Calculator / Expense Tracker
--------------------------------------------
A desktop (Tkinter) recreation of the IDFC FIRST Bank "Budget Calculator" UI/UX:
    Step 1 -> Enter income (primary + other)
    Step 2 -> Enter EMIs, Expenses, Investments & Emergency fund
              (grouped into fun "Ministry" themed cards, live % of income shown)
    Step 3 -> Budget health analysis using the 50/30/20 rule
              (Debt & Needs / Lifestyle / Savings) with a pie chart,
              verdicts, and a "Retake test" option.

Run with:  python expense_tracker.py
Requires:  matplotlib  (pip install matplotlib)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ----------------------------------------------------------------------
#  THEME  (colors lifted from IDFC FIRST Bank's brand palette)
# ----------------------------------------------------------------------
MAROON = "#9D1D27"
MAROON_DARK = "#6E1219"
GOLD = "#D4A017"
BG = "#FAF7F2"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#2B2B2B"
TEXT_MUTED = "#7A7A7A"
GREEN = "#2E8B57"
AMBER = "#D98C00"
RED = "#C0392B"
BORDER = "#E7E0D8"

FONT_H1 = ("Segoe UI", 22, "bold")
FONT_H2 = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_BODY_B = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_BIG_NUM = ("Segoe UI", 20, "bold")

SAVE_FILE = os.path.join(os.path.expanduser("~"), ".budget_calc_history.json")


def fmt_inr(amount):
    """Format a number the Indian way: 1,00,000"""
    try:
        amount = int(round(amount))
    except (ValueError, TypeError):
        amount = 0
    neg = amount < 0
    amount = abs(amount)
    s = str(amount)
    if len(s) <= 3:
        out = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        out = ",".join(parts) + "," + last3
    return ("-" if neg else "") + "\u20b9" + out


class MoneyEntry(ttk.Frame):
    """A labeled ₹ currency input row, self-validating to digits only."""

    def __init__(self, parent, label_text, on_change=None, **kw):
        super().__init__(parent, style="Card.TFrame", **kw)
        self.var = tk.StringVar(value="")
        self.on_change = on_change

        lbl = ttk.Label(self, text=label_text, style="FieldLabel.TLabel")
        lbl.pack(anchor="w", pady=(2, 3))

        box = tk.Frame(
            self, bg="#FFFFFF", highlightbackground=BORDER, highlightthickness=1, bd=0
        )
        box.pack(fill="x")

        rupee = tk.Label(
            box, text="\u20b9", bg="#FFFFFF", fg=MAROON, font=("Segoe UI", 11, "bold")
        )
        rupee.pack(side="left", padx=(10, 2), pady=6)

        vcmd = (self.register(self._validate), "%P")
        entry = tk.Entry(
            box,
            textvariable=self.var,
            bd=0,
            bg="#FFFFFF",
            font=("Segoe UI", 11),
            fg=TEXT_DARK,
            validate="key",
            validatecommand=vcmd,
            insertbackground=MAROON,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=6)
        self.var.trace_add("write", self._changed)

    def _validate(self, proposed):
        return proposed == "" or proposed.isdigit()

    def _changed(self, *args):
        if self.on_change:
            self.on_change()

    def get(self):
        v = self.var.get().strip()
        return int(v) if v else 0

    def set(self, value):
        self.var.set(str(int(value)) if value else "")


class StepDots(tk.Frame):
    """Top step indicator: Step 1 / 2 / 3."""

    def __init__(self, parent, total=3):
        super().__init__(parent, bg=BG)
        self.total = total
        self.labels = []
        for i in range(total):
            wrap = tk.Frame(self, bg=BG)
            wrap.pack(side="left", padx=14)
            circ = tk.Canvas(wrap, width=30, height=30, bg=BG, highlightthickness=0)
            circ.pack()
            txt = tk.Label(
                wrap, text=f"Step {i+1}", bg=BG, fg=TEXT_MUTED, font=FONT_SMALL
            )
            txt.pack()
            self.labels.append((circ, txt))
        self.set_active(0)

    def set_active(self, idx):
        for i, (circ, txt) in enumerate(self.labels):
            circ.delete("all")
            if i < idx:
                fill, outline, num_color = GOLD, GOLD, "#FFFFFF"
            elif i == idx:
                fill, outline, num_color = MAROON, MAROON, "#FFFFFF"
            else:
                fill, outline, num_color = "#FFFFFF", BORDER, TEXT_MUTED
            circ.create_oval(2, 2, 28, 28, fill=fill, outline=outline, width=2)
            circ.create_text(
                15, 15, text=str(i + 1), fill=num_color, font=("Segoe UI", 10, "bold")
            )
            txt.configure(
                fg=MAROON if i == idx else TEXT_MUTED,
                font=(FONT_SMALL[0], FONT_SMALL[1], "bold" if i == idx else "normal"),
            )


class MinistryCard(ttk.Frame):
    """A card that groups related expense fields under a fun 'Ministry' theme,
    exactly mirroring the source site's structure, with a live % of income bar."""

    def __init__(
        self, parent, icon, ministry_name, title, field_defs, target_pct, on_change
    ):
        super().__init__(parent, style="Card.TFrame", padding=16)
        self.field_defs = field_defs
        self.target_pct = target_pct
        self.on_change = on_change
        self.entries = {}

        header = tk.Frame(self, bg=CARD_BG)
        header.pack(fill="x", pady=(0, 8))

        icon_lbl = tk.Label(header, text=icon, bg=CARD_BG, font=("Segoe UI", 20))
        icon_lbl.pack(side="left", padx=(0, 10))

        text_wrap = tk.Frame(header, bg=CARD_BG)
        text_wrap.pack(side="left", fill="x", expand=True)
        tk.Label(
            text_wrap,
            text=ministry_name,
            bg=CARD_BG,
            fg=GOLD,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(text_wrap, text=title, bg=CARD_BG, fg=TEXT_DARK, font=FONT_H2).pack(
            anchor="w"
        )

        for key, label in field_defs:
            e = MoneyEntry(self, label, on_change=self._changed)
            e.pack(fill="x", pady=5)
            self.entries[key] = e

        self.pct_lbl = tk.Label(
            self,
            text="",
            bg=CARD_BG,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
            wraplength=280,
            justify="left",
        )
        self.pct_lbl.pack(anchor="w", pady=(8, 0))

    def _changed(self):
        if self.on_change:
            self.on_change()

    def total(self):
        return sum(e.get() for e in self.entries.values())

    def refresh_pct(self, income):
        pct = (self.total() / income * 100) if income else 0
        self.pct_lbl.configure(
            text=f"{pct:.0f}% of your monthly income goes towards this"
        )

    def values(self):
        return {k: e.get() for k, e in self.entries.items()}

    def load(self, data):
        for k, e in self.entries.items():
            e.set(data.get(k, 0))


class BudgetCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Family Budget Calculator - Expense Tracker")
        self.geometry("980x760")
        self.minsize(880, 680)
        self.configure(bg=BG)

        self._setup_style()

        self.primary_income = MoneyEntry
        self.step = 0
        self.history = self._load_history()

        self._build_shell()
        self._build_step1()
        self._build_step2()
        self._build_step3()
        self._show_step(0)

    # ------------------------------------------------------------
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD_BG, relief="flat")
        style.configure(
            "FieldLabel.TLabel",
            background=CARD_BG,
            foreground=TEXT_DARK,
            font=FONT_BODY_B,
        )
        style.configure("Header.TFrame", background=MAROON)
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 11, "bold"),
            background=MAROON,
            foreground="white",
            padding=10,
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", MAROON_DARK), ("disabled", "#C9A9AC")],
        )
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 11, "bold"),
            background="white",
            foreground=MAROON,
            padding=10,
            borderwidth=1,
        )
        style.map("Secondary.TButton", background=[("active", "#F3E9E9")])
        style.configure(
            "TProgressbar", troughcolor=BORDER, background=MAROON, thickness=10
        )
        # Thicker, high-contrast scrollbar so the thumb is easy to grab and drag
        style.configure(
            "Thick.Vertical.TScrollbar",
            gripcount=0,
            background=MAROON,
            darkcolor=MAROON,
            lightcolor=MAROON,
            troughcolor="#EFE7E0",
            bordercolor="#EFE7E0",
            arrowcolor="white",
            relief="flat",
            arrowsize=16,
            width=16,
        )
        style.map(
            "Thick.Vertical.TScrollbar",
            background=[("active", MAROON_DARK), ("pressed", MAROON_DARK)],
        )

    # ------------------------------------------------------------
    def _build_shell(self):
        header = tk.Frame(self, bg=MAROON, height=92)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="\U0001f3e6", bg=MAROON, font=("Segoe UI", 26)).pack(
            side="left", padx=(24, 10), pady=10
        )
        title_wrap = tk.Frame(header, bg=MAROON)
        title_wrap.pack(side="left", pady=14)
        tk.Label(
            title_wrap,
            text=f"Family Budget Calculator for FY {self._fy_label()}",
            bg=MAROON,
            fg="white",
            font=FONT_H1,
        ).pack(anchor="w")
        tk.Label(
            title_wrap,
            text="Be the finance minister of your own home — track income, "
            "manage expenses, and stay ready for the unexpected.",
            bg=MAROON,
            fg="#F1D9DB",
            font=FONT_BODY,
        ).pack(anchor="w")

        self.steps_bar = StepDots(self)
        self.steps_bar.pack(pady=(16, 6))

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=24, pady=6)

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=24, pady=14)
        self.back_btn = ttk.Button(
            footer, text="\u2190 Back", style="Secondary.TButton", command=self._go_back
        )
        self.back_btn.pack(side="left")
        self.next_btn = ttk.Button(
            footer, text="Next \u2192", style="Primary.TButton", command=self._go_next
        )
        self.next_btn.pack(side="right")

        disclaimer = tk.Label(
            self,
            text="Disclaimer: For informational purposes only. "
            "This is a personal tool, not financial advice.",
            bg=BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        )
        disclaimer.pack(pady=(0, 6))

    def _bind_mousewheel(self, canvas):
        """Enable mouse-wheel scrolling only while the pointer is over this canvas
        (avoids the wheel scrolling the wrong step)."""

        def _wheel(event):
            delta = event.delta if event.delta else (120 if event.num == 4 else -120)
            canvas.yview_scroll(int(-1 * (delta / 120)), "units")

        def _enter(event):
            canvas.bind_all("<MouseWheel>", _wheel)  # Windows / macOS
            canvas.bind_all("<Button-4>", _wheel)  # Linux scroll up
            canvas.bind_all("<Button-5>", _wheel)  # Linux scroll down

        def _leave(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _enter)
        canvas.bind("<Leave>", _leave)

    @staticmethod
    def _fy_label():
        y = datetime.now().year
        m = datetime.now().month
        if m >= 4:
            return f"{y}-{str(y+1)[2:]}"
        return f"{y-1}-{str(y)[2:]}"

    # ------------------------------------------------------------
    # STEP 1 - Income
    # ------------------------------------------------------------
    def _build_step1(self):
        self.frame1 = tk.Frame(self.body, bg=BG)

        card = ttk.Frame(self.frame1, style="Card.TFrame", padding=28)
        card.pack(pady=10, padx=40, fill="x")

        tk.Label(
            card,
            text="\U0001f4b0  Start with your income",
            bg=CARD_BG,
            fg=TEXT_DARK,
            font=FONT_H2,
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            card,
            text="As the finance minister of your home, start by entering "
            "your total monthly income.",
            bg=CARD_BG,
            fg=TEXT_MUTED,
            font=FONT_BODY,
            wraplength=560,
            justify="left",
        ).pack(anchor="w", pady=(0, 16))

        self.primary_income_entry = MoneyEntry(
            card,
            "Primary monthly income (in-hand)",
            on_change=self._refresh_income_summary,
        )
        self.primary_income_entry.pack(fill="x", pady=6)

        self.other_income_entry = MoneyEntry(
            card,
            "Other income (rent, interest, profits, etc.)",
            on_change=self._refresh_income_summary,
        )
        self.other_income_entry.pack(fill="x", pady=6)

        sep = tk.Frame(card, bg=BORDER, height=1)
        sep.pack(fill="x", pady=16)

        totals = tk.Frame(card, bg=CARD_BG)
        totals.pack(fill="x")

        left = tk.Frame(totals, bg=CARD_BG)
        left.pack(side="left")
        tk.Label(
            left,
            text="Your total monthly income",
            bg=CARD_BG,
            fg=TEXT_MUTED,
            font=FONT_BODY,
        ).pack(anchor="w")
        self.total_income_lbl = tk.Label(
            left, text=fmt_inr(0), bg=CARD_BG, fg=MAROON, font=FONT_BIG_NUM
        )
        self.total_income_lbl.pack(anchor="w")

        right = tk.Frame(totals, bg=CARD_BG)
        right.pack(side="right")
        tk.Label(
            right, text="Your annual income", bg=CARD_BG, fg=TEXT_MUTED, font=FONT_BODY
        ).pack(anchor="e")
        self.annual_income_lbl = tk.Label(
            right,
            text=fmt_inr(0),
            bg=CARD_BG,
            fg=TEXT_DARK,
            font=("Segoe UI", 14, "bold"),
        )
        self.annual_income_lbl.pack(anchor="e")

    def _refresh_income_summary(self):
        total = self.primary_income_entry.get() + self.other_income_entry.get()
        self.total_income_lbl.configure(text=fmt_inr(total))
        self.annual_income_lbl.configure(text=fmt_inr(total * 12))
        # also refresh step2 ministry percentages live if built
        if hasattr(self, "cards"):
            self._refresh_step2_pcts()

    def total_income(self):
        return self.primary_income_entry.get() + self.other_income_entry.get()

    # ------------------------------------------------------------
    # STEP 2 - EMIs / Expenses / Investments / Emergency fund
    # ------------------------------------------------------------
    def _build_step2(self):
        self.frame2 = tk.Frame(self.body, bg=BG)

        canvas = tk.Canvas(self.frame2, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.frame2,
            orient="vertical",
            command=canvas.yview,
            style="Thick.Vertical.TScrollbar",
        )
        scroll_frame = tk.Frame(canvas, bg=BG)
        scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # keep the inner frame's width in sync with the canvas so content reflows on resize
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width)
        )

        self._bind_mousewheel(canvas)

        tk.Label(
            scroll_frame,
            text="\U0001f4cb  Enter your EMIs, Expenses & Investments",
            bg=BG,
            fg=TEXT_DARK,
            font=FONT_H2,
        ).pack(anchor="w", pady=(6, 12))

        grid = tk.Frame(scroll_frame, bg=BG)
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self.cards = {}

        self.cards["debt"] = MinistryCard(
            grid,
            "\U0001f3db\ufe0f",
            "MINISTRY OF DEBT REPAYMENT",
            "Your EMI commitments every month",
            [
                ("home_loan", "Home loan EMI"),
                ("credit_card", "Credit card bill"),
                ("other_loans", "Other loan EMIs"),
            ],
            target_pct=50,
            on_change=self._refresh_step2_pcts,
        )
        self.cards["debt"].grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.cards["household"] = MinistryCard(
            grid,
            "\U0001f3e0",
            "MINISTRY OF HOME AFFAIRS",
            "Your personal & household expenses",
            [
                ("utilities", "Utilities & groceries"),
                ("rent", "Rent"),
                ("other_expenses", "Other expenses"),
            ],
            target_pct=30,
            on_change=self._refresh_step2_pcts,
        )
        self.cards["household"].grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        self.cards["invest"] = MinistryCard(
            grid,
            "\U0001f4c8",
            "MINISTRY OF FUTURE DEVELOPMENT",
            "Your investments including gold, SIPs, etc.",
            [("investments", "Investments")],
            target_pct=10,
            on_change=self._refresh_step2_pcts,
        )
        self.cards["invest"].grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        self.cards["emergency"] = MinistryCard(
            grid,
            "\U0001f6a8",
            "MINISTRY OF CRISIS MANAGEMENT",
            "Your emergency fund",
            [("emergency_fund", "Funds")],
            target_pct=10,
            on_change=self._refresh_step2_pcts,
        )
        self.cards["emergency"].grid(row=1, column=1, sticky="nsew", padx=8, pady=8)

        grid.rowconfigure(0, weight=1)
        grid.rowconfigure(1, weight=1)

        # Allocation summary strip
        self.alloc_frame = tk.Frame(
            scroll_frame, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1
        )
        self.alloc_frame.pack(fill="x", pady=14, ipady=10)
        self.alloc_lbl = tk.Label(
            self.alloc_frame,
            text="",
            bg=CARD_BG,
            fg=TEXT_DARK,
            font=FONT_BODY_B,
            wraplength=850,
            justify="left",
        )
        self.alloc_lbl.pack(padx=16, pady=4, anchor="w")

    def _all_expenses_total(self):
        return sum(c.total() for c in self.cards.values())

    def _refresh_step2_pcts(self):
        income = self.total_income()
        for c in self.cards.values():
            c.refresh_pct(income)

        total_expenses = self._all_expenses_total()
        remaining = income - total_expenses
        if income <= 0:
            self.alloc_lbl.configure(
                text="Enter your income in Step 1 to see how much of it is allocated.",
                fg=TEXT_MUTED,
            )
        elif remaining > 0:
            self.alloc_lbl.configure(
                text=f"You have {fmt_inr(remaining)} unallocated from your income.",
                fg=GREEN,
            )
        elif remaining == 0:
            self.alloc_lbl.configure(text="Your income is fully allocated.", fg=AMBER)
        else:
            self.alloc_lbl.configure(
                text=f"Your expenses exceed your income by {fmt_inr(-remaining)}. "
                f"Please review the amounts and try again.",
                fg=RED,
            )

    # ------------------------------------------------------------
    # STEP 3 - Analysis
    # ------------------------------------------------------------
    def _build_step3(self):
        self.frame3 = tk.Frame(self.body, bg=BG)

        canvas = tk.Canvas(self.frame3, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.frame3,
            orient="vertical",
            command=canvas.yview,
            style="Thick.Vertical.TScrollbar",
        )
        self.scroll3 = tk.Frame(canvas, bg=BG)
        self.scroll3.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=self.scroll3, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width)
        )

        self._bind_mousewheel(canvas)
        # content built dynamically in _render_analysis()

    def _render_analysis(self):
        for w in self.scroll3.winfo_children():
            w.destroy()

        income = self.total_income()
        debt = self.cards["debt"].total()
        household = self.cards["household"].total()
        invest = self.cards["invest"].total()
        emergency = self.cards["emergency"].total()
        total_expenses = debt + household + invest + emergency
        savings = income - (debt + household)  # savings = income - (debt+lifestyle)
        # Following the 50/30/20 framing: Debt&Needs / Lifestyle / Savings
        # Here we treat: Debt&Needs = debt, Lifestyle = household, Savings = invest+emergency+leftover
        savings_bucket = invest + emergency + max(income - total_expenses, 0)

        debt_pct = (debt / income * 100) if income else 0
        lifestyle_pct = (household / income * 100) if income else 0
        savings_pct = (savings_bucket / income * 100) if income else 0

        healthy = debt_pct <= 50 and lifestyle_pct <= 30 and savings_pct >= 20
        at_risk = not healthy and (debt_pct <= 65 and savings_pct >= 10)

        if healthy:
            verdict = "Healthy"
            verdict_color = GREEN
            verdict_icon = "\u2705"
        elif at_risk:
            verdict = "At Risk"
            verdict_color = AMBER
            verdict_icon = "\u26a0\ufe0f"
        else:
            verdict = "Under Stress"
            verdict_color = RED
            verdict_icon = "\u26d4"

        header = tk.Frame(self.scroll3, bg=BG)
        header.pack(fill="x", pady=(6, 10))
        tk.Label(
            header,
            text=f"{verdict_icon}  Your Budget is {verdict}",
            bg=BG,
            fg=verdict_color,
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        # Summary cards row
        summary_row = tk.Frame(self.scroll3, bg=BG)
        summary_row.pack(fill="x", pady=6)
        self._summary_tile(summary_row, "Monthly Revenue", fmt_inr(income), TEXT_DARK)
        self._summary_tile(summary_row, "Expenses", fmt_inr(total_expenses), TEXT_DARK)
        self._summary_tile(
            summary_row, "Savings", fmt_inr(max(income - total_expenses, 0)), GREEN
        )

        # Chart + bars
        body_row = tk.Frame(self.scroll3, bg=BG)
        body_row.pack(fill="both", expand=True, pady=14)

        chart_card = ttk.Frame(body_row, style="Card.TFrame", padding=16)
        chart_card.pack(side="left", padx=(0, 12), fill="y")
        self._build_pie_chart(chart_card, debt, household, savings_bucket)

        bars_card = ttk.Frame(body_row, style="Card.TFrame", padding=18)
        bars_card.pack(side="left", fill="both", expand=True)

        self._budget_bar(
            bars_card,
            "Debt & Needs",
            debt_pct,
            50,
            "Ideal <50%",
            [
                "Fixed obligations are well within recommended limits, ensuring strong liquidity.",
                "Fixed expenses are high. It is advisable to avoid undertaking new financial liabilities at this stage.",
                "Fixed expenses exceed recommended thresholds. Review recurring costs to improve cash flow.",
            ],
        )
        self._budget_bar(
            bars_card,
            "Lifestyle",
            lifestyle_pct,
            30,
            "Ideal <30%",
            [
                "Discretionary spending is sustainable and within the prudent range.",
                "Discretionary spending is trending higher than optimal. Consider reallocating funds to savings.",
                "Lifestyle expenses are disproportionately high. Rationalise non-essential spending.",
            ],
        )
        self._budget_bar(
            bars_card,
            "Savings",
            savings_pct,
            20,
            "Ideal >20%",
            [
                "Financial health is strong. Current allocation supports long-term wealth accumulation.",
                "Savings rate is moderate. Increase allocation to outpace inflation and meet future goals.",
                "Savings rate is critically low. Prioritise building an emergency fund for financial security.",
            ],
            higher_is_better=True,
        )

        # Category breakdown table
        table_card = ttk.Frame(self.scroll3, style="Card.TFrame", padding=18)
        table_card.pack(fill="x", pady=14)
        tk.Label(
            table_card,
            text="Category breakdown",
            bg=CARD_BG,
            fg=TEXT_DARK,
            font=FONT_H2,
        ).pack(anchor="w", pady=(0, 8))
        rows = [
            ("Home loan EMI", self.cards["debt"].entries["home_loan"].get()),
            ("Credit card bill", self.cards["debt"].entries["credit_card"].get()),
            ("Other loan EMIs", self.cards["debt"].entries["other_loans"].get()),
            (
                "Utilities & groceries",
                self.cards["household"].entries["utilities"].get(),
            ),
            ("Rent", self.cards["household"].entries["rent"].get()),
            ("Other expenses", self.cards["household"].entries["other_expenses"].get()),
            ("Investments", self.cards["invest"].entries["investments"].get()),
            ("Emergency fund", self.cards["emergency"].entries["emergency_fund"].get()),
        ]
        for name, amt in rows:
            r = tk.Frame(table_card, bg=CARD_BG)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=name, bg=CARD_BG, fg=TEXT_MUTED, font=FONT_BODY).pack(
                side="left"
            )
            tk.Label(
                r, text=fmt_inr(amt), bg=CARD_BG, fg=TEXT_DARK, font=FONT_BODY_B
            ).pack(side="right")

        # Actions row
        actions = tk.Frame(self.scroll3, bg=BG)
        actions.pack(fill="x", pady=14)
        ttk.Button(
            actions,
            text="\u21ba  Retake test",
            style="Secondary.TButton",
            command=self._retake,
        ).pack(side="left")
        ttk.Button(
            actions,
            text="\U0001f4be  Save this budget",
            style="Primary.TButton",
            command=lambda: self._save_snapshot(
                income, debt, household, invest, emergency, verdict
            ),
        ).pack(side="right")

        if self.history:
            hist_card = ttk.Frame(self.scroll3, style="Card.TFrame", padding=18)
            hist_card.pack(fill="x", pady=(0, 20))
            tk.Label(
                hist_card, text="Saved budgets", bg=CARD_BG, fg=TEXT_DARK, font=FONT_H2
            ).pack(anchor="w", pady=(0, 8))
            for entry in reversed(self.history[-5:]):
                r = tk.Frame(hist_card, bg=CARD_BG)
                r.pack(fill="x", pady=3)
                tk.Label(
                    r,
                    text=f"{entry['date']}  -  {entry['verdict']}",
                    bg=CARD_BG,
                    fg=TEXT_MUTED,
                    font=FONT_SMALL,
                ).pack(side="left")
                tk.Label(
                    r,
                    text=f"Income {fmt_inr(entry['income'])}",
                    bg=CARD_BG,
                    fg=TEXT_DARK,
                    font=FONT_SMALL,
                ).pack(side="right")

    def _summary_tile(self, parent, label, value, color):
        tile = ttk.Frame(parent, style="Card.TFrame", padding=14)
        tile.pack(side="left", expand=True, fill="x", padx=6)
        tk.Label(tile, text=label, bg=CARD_BG, fg=TEXT_MUTED, font=FONT_BODY).pack(
            anchor="w"
        )
        tk.Label(tile, text=value, bg=CARD_BG, fg=color, font=FONT_BIG_NUM).pack(
            anchor="w"
        )

    def _build_pie_chart(self, parent, debt, household, savings_bucket):
        values = [max(debt, 0), max(household, 0), max(savings_bucket, 0)]
        labels = ["Debt & Needs", "Lifestyle", "Savings"]
        colors = [MAROON, GOLD, GREEN]
        if sum(values) == 0:
            values = [1, 1, 1]

        fig = Figure(figsize=(3.6, 3.6), dpi=100)
        fig.patch.set_facecolor(CARD_BG)
        ax = fig.add_subplot(111)
        ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct="%1.0f%%",
            startangle=90,
            textprops={"fontsize": 9, "color": TEXT_DARK},
            wedgeprops={"edgecolor": "white", "linewidth": 2},
        )
        ax.set_title("Where your income goes", fontsize=11, color=TEXT_DARK, pad=12)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def _budget_bar(
        self,
        parent,
        name,
        pct,
        ideal,
        ideal_label,
        verdict_texts,
        higher_is_better=False,
    ):
        wrap = tk.Frame(parent, bg=CARD_BG)
        wrap.pack(fill="x", pady=10)

        top = tk.Frame(wrap, bg=CARD_BG)
        top.pack(fill="x")
        tk.Label(top, text=name, bg=CARD_BG, fg=TEXT_DARK, font=FONT_BODY_B).pack(
            side="left"
        )
        tk.Label(
            top,
            text=f"Yours: {pct:.0f}%   ({ideal_label})",
            bg=CARD_BG,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        ).pack(side="right")

        bar_bg = tk.Canvas(wrap, height=14, bg="#F0EAE4", highlightthickness=0)
        bar_bg.pack(fill="x", pady=(6, 4))

        if higher_is_better:
            good = pct >= ideal
            borderline = ideal * 0.5 <= pct < ideal
        else:
            good = pct <= ideal
            borderline = ideal < pct <= ideal * 1.3

        color = GREEN if good else (AMBER if borderline else RED)
        verdict_idx = 0 if good else (1 if borderline else 2)

        def draw(event=None):
            bar_bg.delete("all")
            w = bar_bg.winfo_width() or 400
            fill_w = max(6, min(w, w * (pct / 100)))
            bar_bg.create_rectangle(0, 0, w, 14, fill="#F0EAE4", width=0)
            bar_bg.create_rectangle(0, 0, fill_w, 14, fill=color, width=0)
            marker_x = w * (ideal / 100)
            bar_bg.create_line(
                marker_x, -2, marker_x, 16, fill=TEXT_DARK, width=2, dash=(3, 2)
            )

        bar_bg.bind("<Configure>", draw)

        tk.Label(
            wrap,
            text=verdict_texts[verdict_idx],
            bg=CARD_BG,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
            wraplength=460,
            justify="left",
        ).pack(anchor="w")

    # ------------------------------------------------------------
    def _save_snapshot(self, income, debt, household, invest, emergency, verdict):
        entry = {
            "date": datetime.now().strftime("%d %b %Y, %H:%M"),
            "income": income,
            "debt": debt,
            "household": household,
            "invest": invest,
            "emergency": emergency,
            "verdict": verdict,
        }
        self.history.append(entry)
        self._save_history()
        messagebox.showinfo("Saved", "Your budget snapshot has been saved.")
        self._render_analysis()

    def _load_history(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save_history(self):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(self.history, f, indent=2)
        except OSError:
            pass

    def _retake(self):
        self.primary_income_entry.set(0)
        self.other_income_entry.set(0)
        for c in self.cards.values():
            for e in c.entries.values():
                e.set(0)
        self._show_step(0)

    # ------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------
    def _show_step(self, idx):
        self.step = idx
        for f in (self.frame1, self.frame2, self.frame3):
            f.pack_forget()
        if idx == 0:
            self.frame1.pack(fill="both", expand=True)
            self.back_btn.state(["disabled"])
            self.next_btn.configure(text="Next \u2192")
        elif idx == 1:
            self.frame2.pack(fill="both", expand=True)
            self.back_btn.state(["!disabled"])
            self.next_btn.configure(text="Analyse my budget \u2192")
            self._refresh_step2_pcts()
        else:
            self.frame3.pack(fill="both", expand=True)
            self.back_btn.state(["!disabled"])
            self.next_btn.pack_forget()
            self._render_analysis()
        self.steps_bar.set_active(idx)
        if idx != 2:
            self.next_btn.pack(side="right")

    def _go_next(self):
        if self.step == 0:
            if self.total_income() <= 0:
                messagebox.showwarning(
                    "Income required", "Please enter your monthly income to continue."
                )
                return
            self._show_step(1)
        elif self.step == 1:
            income = self.total_income()
            total_expenses = self._all_expenses_total()
            if total_expenses > income:
                messagebox.showwarning(
                    "Expenses exceed income",
                    "Your expenses are exceeding your income. Please review the "
                    "amounts and try again.",
                )
                return
            self._show_step(2)

    def _go_back(self):
        if self.step > 0:
            self._show_step(self.step - 1)


if __name__ == "__main__":
    app = BudgetCalculatorApp()
    app.mainloop()
