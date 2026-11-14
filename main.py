import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from database import *
from ai_models import predict_next_month, detect_anomalies
from reports import export_transactions_csv

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#101522", "sidebar": "#171F32", "card": "#202B42",
    "blue": "#4F8CFF", "purple": "#A78BFA", "pink": "#F472B6",
    "green": "#34D399", "orange": "#FBBF24", "cyan": "#22D3EE",
    "red": "#FB7185", "text": "#F8FAFC", "muted": "#A8B3C7"
}

class SpendMate(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpendMate AI")
        self.geometry("1280x800")
        self.minsize(1050, 680)
        self.configure(fg_color=COLORS["bg"])
        init_db()
        self.user_id = None
        self.show_login()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def label(self, parent, text, size=14, color=None, bold=False):
        return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"),
                            text_color=color or COLORS["text"])

    def entry(self, parent, placeholder, width=220):
        return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width, height=40,
                            corner_radius=10, border_color="#43516D")

    def show_login(self):
        self.clear()
        center = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        center.pack(expand=True)
        self.label(center, "SpendMate AI", 36, COLORS["cyan"], True).pack(pady=(0, 4))
        self.label(center, "Your money. Your goals. Your control.", 14, COLORS["muted"]).pack(pady=(0, 24))
        card = ctk.CTkFrame(center, fg_color=COLORS["card"], corner_radius=22, width=400, height=340)
        card.pack()
        card.pack_propagate(False)
        self.label(card, "Welcome back 👋", 24, COLORS["text"], True).pack(pady=(26, 18))
        self.login_email = self.entry(card, "Email address", 320)
        self.login_email.pack(pady=8)
        self.login_password = self.entry(card, "Password", 320)
        self.login_password.configure(show="•")
        self.login_password.pack(pady=8)
        ctk.CTkButton(card, text="Login", width=320, height=42, fg_color=COLORS["blue"],
                      hover_color="#3473E6", command=self.login).pack(pady=(16, 8))
        ctk.CTkButton(card, text="Create free account", width=320, height=38,
                      fg_color=COLORS["purple"], hover_color="#8866DF",
                      command=self.show_register).pack()

    def show_register(self):
        self.clear()
        center = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        center.pack(expand=True)
        self.label(center, "Create your free account", 28, COLORS["cyan"], True).pack(pady=18)
        card = ctk.CTkFrame(center, fg_color=COLORS["card"], corner_radius=20)
        card.pack(padx=20, pady=10)
        self.reg_name = self.entry(card, "Your name", 320)
        self.reg_email = self.entry(card, "Email address", 320)
        self.reg_password = self.entry(card, "Password (minimum 6 characters)", 320)
        self.reg_password.configure(show="•")
        for w in (self.reg_name, self.reg_email, self.reg_password):
            w.pack(padx=25, pady=9)
        ctk.CTkButton(card, text="Register", width=320, height=42, fg_color=COLORS["green"],
                      text_color="#09251B", command=self.register).pack(padx=25, pady=12)
        ctk.CTkButton(card, text="Back to login", width=320, fg_color="transparent",
                      border_width=1, command=self.show_login).pack(padx=25, pady=(0, 20))

    def register(self):
        try:
            register_user(self.reg_name.get(), self.reg_email.get(), self.reg_password.get())
            messagebox.showinfo("Account created", "Your free account is ready. Please login.")
            self.show_login()
        except Exception as e:
            messagebox.showerror("Could not register", str(e))

    def login(self):
        result = authenticate(self.login_email.get(), self.login_password.get())
        if result:
            self.user_id = result[0]
            self.show_app()
        else:
            messagebox.showerror("Login failed", "Check your email and password.")

    def show_app(self):
        self.clear()
        self.sidebar = ctk.CTkFrame(self, width=235, fg_color=COLORS["sidebar"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.label(self.sidebar, "SpendMate AI", 25, COLORS["cyan"], True).pack(pady=(25, 3))
        self.label(self.sidebar, "PERSONAL FINANCE", 10, COLORS["muted"], True).pack(pady=(0, 20))
        items = [
            ("🏠  Dashboard", self.dashboard), ("🟢  Income", lambda: self.transaction_page("income")),
            ("🔴  Expenses", lambda: self.transaction_page("expense")), ("🎯  Budgets", self.budget_page),
            ("🔮  Future prediction", self.prediction_page), ("🚨  Anomaly detection", self.anomaly_page),
            ("🔁  Recurring expenses", self.recurring_page), ("🌱  Savings goals", self.goals_page),
            ("📊  Reports", self.reports_page), ("🤖  AI assistant", self.assistant_page),
            ("⚙️  Settings", self.settings_page)
        ]
        for name, action in items:
            ctk.CTkButton(self.sidebar, text=name, anchor="w", height=39, fg_color="transparent",
                          hover_color="#2B3853", command=action).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(self.sidebar, text="↪  Logout", fg_color="#713447", hover_color="#91415B",
                      command=self.show_login).pack(side="bottom", fill="x", padx=12, pady=18)
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True, padx=24, pady=22)
        self.dashboard()

    def page(self, title, subtitle):
        for w in self.content.winfo_children():
            w.destroy()
        self.label(self.content, title, 28, COLORS["text"], True).pack(anchor="w")
        self.label(self.content, subtitle, 13, COLORS["muted"]).pack(anchor="w", pady=(3, 18))

    def metric(self, parent, title, value, color, icon):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=16)
        card.pack(side="left", fill="x", expand=True, padx=6)
        self.label(card, icon, 23, color, True).pack(anchor="w", padx=17, pady=(13, 0))
        self.label(card, title, 13, COLORS["muted"]).pack(anchor="w", padx=17, pady=(4, 0))
        self.label(card, value, 23, color, True).pack(anchor="w", padx=17, pady=(3, 15))

    def dashboard(self):
        self.page("Dashboard", "A simple overview of your money")
        d = get_dashboard(self.user_id)
        cards = ctk.CTkFrame(self.content, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 20))
        self.metric(cards, "Total income", f"₹{d['income']:,.0f}", COLORS["green"], "＋")
        self.metric(cards, "Total expenses", f"₹{d['expense']:,.0f}", COLORS["pink"], "－")
        self.metric(cards, "Available balance", f"₹{d['balance']:,.0f}", COLORS["cyan"], "＝")
        self.label(self.content, "Recent transactions", 19, COLORS["text"], True).pack(anchor="w", pady=(8, 10))
        self.table(list_transactions(self.user_id)[:10])

    def table(self, rows):
        box = ctk.CTkScrollableFrame(self.content, fg_color=COLORS["card"], corner_radius=14)
        box.pack(fill="both", expand=True)
        headings = ["DATE", "TYPE", "CATEGORY", "DESCRIPTION", "AMOUNT"]
        for col, h in enumerate(headings):
            self.label(box, h, 11, COLORS["cyan"], True).grid(row=0, column=col, padx=12, pady=12, sticky="w")
        for ri, r in enumerate(rows, 1):
            vals = [r[2], r[3].upper(), r[4], r[5], f"₹{r[6]:,.2f}"]
            color = COLORS["green"] if r[3] == "income" else COLORS["pink"]
            for ci, val in enumerate(vals):
                self.label(box, str(val), 12, color if ci == 4 else COLORS["text"]).grid(
                    row=ri, column=ci, padx=12, pady=8, sticky="w")

    def transaction_page(self, kind):
        title = "Income Management" if kind == "income" else "Expense Management"
        self.page(title, "Add a transaction below. Keep it simple and clear.")
        form = ctk.CTkFrame(self.content, fg_color=COLORS["card"], corner_radius=15)
        form.pack(fill="x", pady=(0, 15))
        self.tx_date = self.entry(form, "YYYY-MM-DD", 140)
        self.tx_date.insert(0, date.today().isoformat())
        self.tx_category = self.entry(form, "Category", 150)
        self.tx_description = self.entry(form, "What was it for?", 220)
        self.tx_amount = self.entry(form, "Amount ₹", 130)
        for w in (self.tx_date, self.tx_category, self.tx_description, self.tx_amount):
            w.pack(side="left", padx=8, pady=14)
        ctk.CTkButton(form, text="＋ Add transaction", fg_color=COLORS["green"],
                      text_color="#09251B", command=lambda: self.save_transaction(kind)).pack(side="left", padx=8)
        rows = [r for r in list_transactions(self.user_id) if r[3] == kind]
        self.table(rows)
        if rows:
            ctk.CTkButton(self.content, text="Delete latest entry", fg_color="#713447",
                          command=lambda: self.delete_latest(kind)).pack(anchor="e", pady=8)

    def save_transaction(self, kind):
        try:
            add_transaction(self.user_id, self.tx_date.get(), kind, self.tx_category.get(),
                            self.tx_description.get(), float(self.tx_amount.get()))
            self.transaction_page(kind)
        except Exception as e:
            messagebox.showerror("Check your entry", str(e))

    def delete_latest(self, kind):
        rows = [r for r in list_transactions(self.user_id) if r[3] == kind]
        if rows:
            delete_transaction(rows[0][0], self.user_id)
            self.transaction_page(kind)

    def budget_page(self):
        self.page("Budget Management", "Set a monthly limit and keep spending on track")
        self.budget_cat = self.entry(self.content, "Category", 220)
        self.budget_amt = self.entry(self.content, "Monthly budget ₹", 220)
        self.budget_cat.pack(anchor="w", pady=6); self.budget_amt.pack(anchor="w", pady=6)
        ctk.CTkButton(self.content, text="Save budget", fg_color=COLORS["purple"],
                      command=self.save_budget).pack(anchor="w", pady=8)
        for cat, limit, spent in get_budgets(self.user_id):
            color = COLORS["red"] if spent > limit else COLORS["green"]
            self.label(self.content, f"{cat}   |   ₹{spent:,.0f} spent of ₹{limit:,.0f}", 15, color, True).pack(anchor="w", pady=7)

    def save_budget(self):
        try:
            set_budget(self.user_id, self.budget_cat.get(), float(self.budget_amt.get()))
            self.budget_page()
        except Exception as e: messagebox.showerror("Error", str(e))

    def prediction_page(self):
        self.page("Future Expense Prediction", "Machine-learning estimate from your previous monthly expenses")
        result = predict_next_month(self.user_id)
        ctk.CTkFrame(self.content, fg_color=COLORS["card"], corner_radius=16, height=170).pack(fill="x")
        self.label(self.content, result, 18, COLORS["cyan"], True).pack(anchor="w", pady=20)

    def anomaly_page(self):
        self.page("Anomaly Detection", "Review unusually high transactions")
        results = detect_anomalies(self.user_id)
        if not results:
            self.label(self.content, "No unusual expenses detected, or add more transaction history.", 16, COLORS["green"]).pack(anchor="w")
        for r in results:
            self.label(self.content, f"⚠  {r[2]}  •  {r[4]}  •  ₹{r[6]:,.2f}", 15, COLORS["orange"], True).pack(anchor="w", pady=6)

    def recurring_page(self):
        self.page("Recurring Expenses", "Find repeated category and amount patterns")
        grouped = {}
        for r in list_transactions(self.user_id):
            if r[3] == "expense":
                grouped.setdefault((r[4], round(r[6], -1)), []).append(r)
        matches = [(k, v) for k, v in grouped.items() if len(v) >= 2]
        if not matches:
            self.label(self.content, "No repeated expense patterns yet. Add more entries to see suggestions.", 15, COLORS["muted"]).pack(anchor="w")
        for (category, amount), rows in matches:
            self.label(self.content, f"🔁  {category} • around ₹{amount:,.0f} • {len(rows)} entries", 15, COLORS["purple"], True).pack(anchor="w", pady=7)
        self.label(self.content, "These are suggestions based on matching entries, not confirmed subscriptions.", 12, COLORS["muted"]).pack(anchor="w", pady=10)


    def goals_page(self):
        self.page("Savings Goals", "Create a target and track your savings")

        # Goal creation section
        self.goal_name = self.entry(self.content, "Goal name", 220)
        self.goal_target = self.entry(self.content, "Target amount", 220)

        self.goal_name.pack(anchor="w", pady=6)
        self.goal_target.pack(anchor="w", pady=6)

        ctk.CTkButton(
            self.content,
            text="+ Add Goal",
            fg_color=COLORS["green"],
            text_color="#09251B",
            command=self.save_goal
        ).pack(anchor="w", pady=10)

        # Display existing goals
        goals = get_goals(self.user_id)

        if not goals:
            self.label(
                self.content,
                "No savings goals yet. Create your first goal!",
                15,
                COLORS["muted"]
            ).pack(anchor="w", pady=15)

        for goal_id, name, target, saved in goals:

            card = ctk.CTkFrame(
                self.content,
                fg_color=COLORS["card"],
                corner_radius=12
            )
            card.pack(fill="x", pady=8, padx=5)

            self.label(
                card,
                f"{name}",
                18,
                COLORS["green"],
                True
            ).pack(anchor="w", padx=15, pady=(12, 5))

            percentage = min(100, (saved / target) * 100) if target > 0 else 0

            self.label(
                card,
                f"Rs. {saved:,.2f} saved / Rs. {target:,.2f}",
                14,
                COLORS["text"]
            ).pack(anchor="w", padx=15, pady=4)

            progress = ctk.CTkProgressBar(
                card,
                width=350,
                progress_color=COLORS["green"]
            )
            progress.pack(anchor="w", padx=15, pady=5)
            progress.set(percentage / 100)

            self.label(
                card,
                f"{percentage:.1f}% completed | Remaining: Rs. {max(0, target-saved):,.2f}",
                12,
                COLORS["muted"]
            ).pack(anchor="w", padx=15, pady=5)

            amount_entry = self.entry(card, "Enter savings amount", 220)
            amount_entry.pack(anchor="w", padx=15, pady=5)

            ctk.CTkButton(
                card,
                text="+ Add Savings",
                fg_color=COLORS["green"],
                text_color="#09251B",
                command=lambda gid=goal_id, entry=amount_entry:
                    self.save_savings(gid, entry)
            ).pack(anchor="w", padx=15, pady=(5, 15))

    def save_goal(self):
        try:
            name = self.goal_name.get().strip()
            target = float(self.goal_target.get())

            add_goal(self.user_id, name, target)

            messagebox.showinfo("Success", "Savings goal created!")
            self.goals_page()

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_savings(self, goal_id, amount_entry):
        try:
            amount = float(amount_entry.get())

            add_savings(self.user_id, goal_id, amount)

            messagebox.showinfo(
                "Success",
                "Savings amount added successfully!"
            )

            self.goals_page()

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def reports_page(self):
        self.page("Reports & Analytics", "Download your transaction data for free")

        ctk.CTkButton(
            self.content,
            text="Export transactions as CSV",
            fg_color=COLORS["blue"],
            command=self.export_report
        ).pack(anchor="w", pady=8)

    def export_report(self):
        try:
            path = export_transactions_csv(self.user_id)
            messagebox.showinfo("Export ready", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def assistant_page(self):
        self.page(
            "AI Finance Assistant",
            "Simple suggestions based on your recorded income and expenses"
        )

        d = get_dashboard(self.user_id)

        if d["income"] <= 0:
            advice = "Start by adding your income and expenses. Then SpendMate can show a useful summary."
        elif d["expense"] > d["income"]:
            advice = "Your recorded expenses are higher than your income. Review optional spending and set category budgets."
        else:
            advice = "Your recorded balance is positive. Consider creating a savings goal and keeping a monthly budget."

        self.label(
            self.content,
            "💡 " + advice,
            18,
            COLORS["purple"],
            True
        ).pack(anchor="w", pady=18)

        self.label(
            self.content,
            "Starter version: rule-based tips. A trained conversational AI can be added later without requiring paid APIs.",
            12,
            COLORS["muted"]
        ).pack(anchor="w")

    def settings_page(self):
        self.page("Settings", "Your app preferences")

        for line in [
            "Theme: Dark and colourful",
            "Currency: Indian Rupee",
            "Storage: Local SQLite database",
            "Cost: No subscription or paid API required for this starter version",
            "Privacy: Your entries stay in the local project database on this computer"
        ]:
            self.label(
                self.content,
                "• " + line,
                15,
                COLORS["muted"]
            ).pack(anchor="w", pady=8)

if __name__ == "__main__":
    app = SpendMate()
    app.mainloop()