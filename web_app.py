
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

from datetime import date
from database import (
    init_db, conn, register_user, authenticate,
    add_transaction, list_transactions, delete_transaction,
    get_dashboard, set_budget, get_budgets,
    add_goal, get_goals, add_savings, get_savings_history
)
from ai_models import predict_next_month, detect_anomalies

st.set_page_config(
    page_title="SpendMate AI",
    page_icon="💰",
    layout="wide"
)

# Initialize database
init_db()

# Session state
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""


def get_user_name(uid):
    with conn() as c:
        result = c.execute(
            "SELECT name FROM users WHERE id=?", (uid,)
        ).fetchone()
    return result[0] if result else "User"


def money(value):
    return f"Rs. {value:,.2f}"


# ---------------- LOGIN / REGISTER ----------------

def authentication_page():
    st.title("💰 SpendMate AI")
    st.subheader("Smart Personal Finance Management")
    st.write("Manage your income, expenses and savings in one place.")

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        st.subheader("Welcome Back")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button(
                "Login", use_container_width=True
            )

        if login_button:
            result = authenticate(email, password)

            if result:
                st.session_state.user_id = result[0]
                st.session_state.user_name = get_user_name(result[0])
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with register_tab:
        st.subheader("Create Your Account")

        with st.form("register_form"):
            name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            new_password = st.text_input(
                "Create Password", type="password"
            )
            confirm_password = st.text_input(
                "Confirm Password", type="password"
            )

            register_button = st.form_submit_button(
                "Create Account", use_container_width=True
            )

        if register_button:
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    register_user(name, new_email, new_password)
                    st.success("Account created successfully! Please login.")
                except sqlite3.IntegrityError:
                    st.error("This email is already registered.")
                except Exception as e:
                    st.error(str(e))


# ---------------- MAIN APPLICATION ----------------

def main_app():

    uid = st.session_state.user_id

    st.sidebar.title("💰 SpendMate AI")
    st.sidebar.write(f"Welcome, {st.session_state.user_name}!")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Income & Expenses",
            "AI Predictions",
            "Budget Planner",
            "Savings Goals",
            "Reports"
        ]
    )

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.user_name = ""
        st.rerun()

    # ---------------- DASHBOARD ----------------

    if page == "Dashboard":

        st.title("📊 Dashboard")
        st.write("Your personal financial overview")

        data = get_dashboard(uid)
        goals = get_goals(uid)
        total_saved = sum(g[3] for g in goals)

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Income", money(data["income"]))
        col2.metric("Total Expenses", money(data["expense"]))
        col3.metric("Total Savings", money(total_saved))

        st.divider()

        rows = list_transactions(uid)

        if rows:
            df = pd.DataFrame(
                rows,
                columns=[
                    "ID", "User ID", "Date", "Type",
                    "Category", "Description", "Amount"
                ]
            )

            df["Date"] = pd.to_datetime(df["Date"])
            df["Month"] = df["Date"].dt.strftime("%Y-%m")

            st.subheader("Monthly Expense Analysis")

            expenses = df[df["Type"] == "expense"]

            if not expenses.empty:
                monthly = (
                    expenses.groupby("Month")["Amount"]
                    .sum()
                    .reset_index()
                )

                fig = px.bar(
                    monthly,
                    x="Month",
                    y="Amount",
                    title="Monthly Expenses",
                    text_auto=".2f"
                )
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Category-wise Expenses")

                category_data = (
                    expenses.groupby("Category")["Amount"]
                    .sum()
                    .reset_index()
                )

                fig2 = px.pie(
                    category_data,
                    names="Category",
                    values="Amount",
                    hole=0.4
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No expenses recorded yet.")

            st.subheader("Recent Transactions")
            st.dataframe(
                df[[
                    "Date", "Type", "Category",
                    "Description", "Amount"
                ]].head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Start by adding your first income or expense.")

    # ---------------- INCOME AND EXPENSES ----------------

    elif page == "Income & Expenses":

        st.title("💸 Income & Expense Management")

        with st.form("transaction_form"):

            kind = st.selectbox(
                "Transaction Type", ["income", "expense"]
            )

            tx_date = st.date_input("Date", value=date.today())

            if kind == "income":
                categories = [
                    "Salary", "Allowance", "Freelance",
                    "Business", "Other"
                ]
            else:
                categories = [
                    "Food", "Travel", "Shopping",
                    "Bills", "Education", "Entertainment",
                    "Health", "Office", "Other"
                ]

            category = st.selectbox("Category", categories)
            description = st.text_input("Description")
            amount = st.number_input(
                "Amount (Rs.)", min_value=0.0, step=100.0
            )

            submitted = st.form_submit_button(
                "Save Transaction", use_container_width=True
            )

        if submitted:
            try:
                add_transaction(
                    uid,
                    tx_date.isoformat(),
                    kind,
                    category,
                    description,
                    amount
                )
                st.success("Transaction saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.subheader("Transaction History")

        rows = list_transactions(uid)

        if rows:
            df = pd.DataFrame(
                rows,
                columns=[
                    "ID", "User ID", "Date", "Type",
                    "Category", "Description", "Amount"
                ]
            )

            st.dataframe(
                df.drop(columns=["User ID"]),
                use_container_width=True,
                hide_index=True
            )

            transaction_options = {
                f"ID {r[0]} - {r[2]} - {r[3]} - {money(r[6])}": r[0]
                for r in rows
            }

            selected = st.selectbox(
                "Select transaction to delete",
                list(transaction_options.keys())
            )

            if st.button("Delete Selected Transaction"):
                delete_transaction(
                    transaction_options[selected], uid
                )
                st.success("Transaction deleted.")
                st.rerun()
        else:
            st.info("No transactions available.")

    # ---------------- AI PREDICTIONS ----------------

    elif page == "AI Predictions":

        st.title("🤖 SpendMate AI Predictions")
        st.write("AI-powered financial insights")

        st.subheader("Next Month Expense Prediction")

        if st.button("Generate AI Prediction"):
            with st.spinner("Analyzing your expense history..."):
                prediction = predict_next_month(uid)
            st.info(prediction)

        st.divider()

        st.subheader("Unusual Expense Detection")

        if st.button("Detect Unusual Expenses"):
            anomalies = detect_anomalies(uid)

            if anomalies:
                st.warning(
                    f"{len(anomalies)} unusual expense(s) detected."
                )

                anomaly_df = pd.DataFrame(
                    anomalies,
                    columns=[
                        "ID", "User ID", "Date", "Type",
                        "Category", "Description", "Amount"
                    ]
                )

                st.dataframe(
                    anomaly_df[[
                        "Date", "Category",
                        "Description", "Amount"
                    ]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success(
                    "No unusual expenses detected, or more data is needed."
                )

    # ---------------- BUDGET PLANNER ----------------

    elif page == "Budget Planner":

        st.title("🎯 Monthly Budget Planner")

        with st.form("budget_form"):

            budget_category = st.selectbox(
                "Expense Category",
                [
                    "Food", "Travel", "Shopping",
                    "Bills", "Education", "Entertainment",
                    "Health", "Office", "Other"
                ]
            )

            budget_amount = st.number_input(
                "Monthly Budget (Rs.)",
                min_value=0.0,
                step=500.0
            )

            budget_submit = st.form_submit_button("Save Budget")

        if budget_submit:
            try:
                set_budget(uid, budget_category, budget_amount)
                st.success("Budget saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.subheader("Your Monthly Budgets")

        budgets = get_budgets(uid)

        if budgets:
            for category, limit, spent in budgets:

                remaining = limit - spent

                st.write(f"**{category}**")
                st.progress(
                    min(spent / limit, 1.0) if limit > 0 else 0.0
                )

                c1, c2, c3 = st.columns(3)
                c1.metric("Budget", money(limit))
                c2.metric("Spent", money(spent))
                c3.metric("Remaining", money(remaining))

                if spent > limit:
                    st.error("Budget exceeded!")
                st.divider()
        else:
            st.info("No budgets created yet.")

    # ---------------- SAVINGS GOALS ----------------

    elif page == "Savings Goals":

        st.title("💰 Savings Goals")

        with st.form("goal_form"):

            goal_name = st.text_input("Goal Name")
            target = st.number_input(
                "Target Amount (Rs.)",
                min_value=0.0,
                step=500.0
            )

            goal_submit = st.form_submit_button("Create Goal")

        if goal_submit:
            try:
                add_goal(uid, goal_name, target)
                st.success("Savings goal created!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.subheader("Your Savings Goals")

        goals = get_goals(uid)

        if goals:

            goal_options = {
                f"{g[1]} - Target: {money(g[2])}": g[0]
                for g in goals
            }

            for goal in goals:
                goal_id, name, target, saved = goal

                st.write(f"**{name}**")
                st.progress(
                    min(saved / target, 1.0) if target > 0 else 0.0
                )

                c1, c2 = st.columns(2)
                c1.metric("Saved", money(saved))
                c2.metric("Target", money(target))

            st.divider()
            st.subheader("Add Savings")

            with st.form("savings_form"):

                selected_goal = st.selectbox(
                    "Choose Goal", list(goal_options.keys())
                )

                savings_amount = st.number_input(
                    "Amount to Save (Rs.)",
                    min_value=0.0,
                    step=100.0
                )

                savings_submit = st.form_submit_button(
                    "Add Savings"
                )

            if savings_submit:
                try:
                    add_savings(
                        uid,
                        goal_options[selected_goal],
                        savings_amount
                    )
                    st.success("Savings added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

            st.subheader("Savings History")

            history_goal = st.selectbox(
                "Choose goal to view history",
                list(goal_options.keys()),
                key="history_goal"
            )

            history = get_savings_history(
                uid, goal_options[history_goal]
            )

            if history:
                history_df = pd.DataFrame(
                    history,
                    columns=["Amount", "Date"]
                )
                st.dataframe(
                    history_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No savings history available.")

        else:
            st.info("Create your first savings goal.")

    # ---------------- REPORTS ----------------

    elif page == "Reports":

        st.title("📁 Financial Reports")

        rows = list_transactions(uid)

        if rows:
            df = pd.DataFrame(
                rows,
                columns=[
                    "ID", "User ID", "Date", "Type",
                    "Category", "Description", "Amount"
                ]
            )

            report_df = df.drop(columns=["User ID"])

            st.subheader("Transaction Report")
            st.dataframe(
                report_df,
                use_container_width=True,
                hide_index=True
            )

            csv_data = report_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download CSV Report",
                data=csv_data,
                file_name="SpendMate_AI_Report.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.subheader("Financial Summary")

            income = df[df["Type"] == "income"]["Amount"].sum()
            expenses = df[df["Type"] == "expense"]["Amount"].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Income", money(income))
            c2.metric("Expenses", money(expenses))
            c3.metric("Balance", money(income - expenses))

        else:
            st.info("Add transactions to generate reports.")


# ---------------- APPLICATION START ----------------

if st.session_state.user_id is None:
    authentication_page()
else:
    main_app()
