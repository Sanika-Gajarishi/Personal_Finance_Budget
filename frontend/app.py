from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import plotly.express as px
import streamlit as st

from api_client import (
    ask_finance_assistant,
    create_transaction,
    delete_transaction,
    update_transaction,
    get_budgets,
    create_budget,
    update_budget,
    delete_budget,
    get_budget_summary,
    get_current_user,
    get_transactions,
    login_user,
    register_user,
    
)


st.set_page_config(
    page_title="Personal Finance Budget",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        .main-title {
            font-size: 3rem;
            font-weight: 900;
            color: #12305a;
            text-align: center;
            margin-bottom: 0.25rem;
        }

        .main-subtitle {
            text-align: center;
            font-size: 1.05rem;
            color: #64748b;
            margin-bottom: 2rem;
        }

        .title-banner {
            background: linear-gradient(120deg, #eaf3ff, #f8fbff);
            padding: 1.7rem 1rem;
            border-radius: 16px;
            border: 1px solid #d8e7fb;
            margin-bottom: 1.5rem;
        }

        div[data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 1rem;
            border-radius: 12px;
        }

        div.stButton > button {
            border-radius: 8px;
        }

        .section-title {
            color: #12305a;
            font-weight: 800;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


DEFAULT_STATE = {
    "token": None,
    "user": None,
    "pending_name": "",
    "chat_history": [],
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def money(value):
    """Format a number as Indian rupees."""
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, ValueError, TypeError):
        amount = Decimal("0")

    return f"₹{amount:,.2f}"


def result_data(result, default=None):
    """Extract API data safely."""
    if not result or not result.get("success"):
        return default

    data = result.get("data")

    return data if data is not None else default


def show_api_error(result):
    st.error(
        result.get("message", "Something went wrong.")
        if result
        else "Something went wrong."
    )


def get_user_display_name():
    """Choose a friendly name for the logged-in user."""
    user = st.session_state.get("user") or {}

    if isinstance(user, dict):
        name = user.get("full_name") or user.get("name")

        if name:
            return name

        email = user.get("email")

        if email:
            return email.split("@")[0]

    return st.session_state.get("pending_name") or "there"

def load_transactions():
    """Load all transactions in batches of 100."""
    all_transactions = []
    offset = 0
    batch_size = 100

    while True:
        result = get_transactions(
            st.session_state.token,
            limit=batch_size,
            offset=offset,
        )

        if not result.get("success"):
            show_api_error(result)
            return None

        batch = result_data(result, [])

        if not isinstance(batch, list):
            st.error("The transactions API returned an unexpected response.")
            return None

        all_transactions.extend(batch)

        # No more records to fetch.
        if len(batch) < batch_size:
            break

        offset += batch_size

    return all_transactions


def load_budgets():
    result = get_budgets(st.session_state.token)

    if not result.get("success"):
        show_api_error(result)
        return None

    budgets = result_data(result, [])

    return budgets if isinstance(budgets, list) else []


def transactions_to_dataframe(transactions):
    """Convert API transaction objects into a DataFrame."""
    if not transactions:
        return pd.DataFrame(
            columns=[
                "id",
                "transaction_date",
                "transaction_type",
                "category",
                "description",
                "amount",
            ]
        )

    df = pd.DataFrame(transactions)

    expected_columns = [
        "id",
        "transaction_date",
        "transaction_type",
        "category",
        "description",
        "amount",
    ]

    for column in expected_columns:
        if column not in df.columns:
            df[column] = None

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce",
    ).fillna(0)

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce",
    )

    return df


def display_transaction_table(df):
    """Display transaction data in a user-friendly table."""
    if df.empty:
        st.info("No transactions found.")
        return

    display_df = df.copy()

    display_df["transaction_date"] = (
        display_df["transaction_date"]
        .dt.strftime("%d %b %Y")
    )

    display_df["amount"] = display_df["amount"].apply(money)

    display_df = display_df.rename(
        columns={
            "id": "Transaction ID",
            "transaction_date": "Date",
            "transaction_type": "Type",
            "category": "Category",
            "description": "Description",
            "amount": "Amount",
        }
    )

    columns = [
        "Transaction ID",
        "Date",
        "Type",
        "Category",
        "Description",
        "Amount",
    ]

    st.dataframe(
        display_df[columns],
        use_container_width=True,
        hide_index=True,
    )

def render_header():
    st.markdown(
        """
        <div class="title-banner">
            <div class="main-title">
                💰 PERSONAL FINANCE BUDGET
            </div>
            <div class="main-subtitle">
                Track your income, manage expenses, and understand
                your financial habits.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_authentication_page():
    render_header()

    st.markdown(
        "<h3 style='text-align:center;'>Welcome!</h3>",
        unsafe_allow_html=True,
    )

    st.write(
        "Sign in to manage your money, or create an account "
        "to get started."
    )

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "📝 Create Account"]
    )

    with login_tab:
        st.subheader("Login")

        with st.form("login_form"):
            email = st.text_input(
                "Email address",
                key="login_email",
            ).strip().lower()

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            login_submitted = st.form_submit_button(
                "Login",
                use_container_width=True,
            )

        if login_submitted:
            if not email or not password:
                st.warning("Please enter your email and password.")

            else:
                with st.spinner("Signing you in..."):
                    result = login_user(email, password)

                if not result.get("success"):
                    show_api_error(result)

                else:
                    data = result_data(result, {})

                    if not isinstance(data, dict):
                        st.error("The login response was unexpected.")

                    else:
                        token = data.get("access_token")

                        if not token:
                            st.error(
                                "Login succeeded, but the response "
                                "did not contain an access token."
                            )

                        else:
                            st.session_state.token = token

                            # Load the actual authenticated user.
                            user_result = get_current_user(token)

                            if user_result.get("success"):
                                st.session_state.user = result_data(
                                    user_result,
                                    {},
                                )

                            st.session_state.chat_history = []

                            st.success("Login successful!")
                            st.rerun()

    with register_tab:
        st.subheader("Create your account")

        with st.form("register_form"):
            full_name = st.text_input(
                "Full name",
                key="register_name",
            ).strip()

            email = st.text_input(
                "Email address",
                key="register_email",
            ).strip().lower()

            password = st.text_input(
                "Password",
                type="password",
                key="register_password",
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="register_confirm_password",
            )

            register_submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True,
            )

        if register_submitted:
            if not full_name or not email or not password:
                st.warning("Please fill in all required fields.")

            elif password != confirm_password:
                st.error("The passwords do not match.")

            elif len(password) < 8:
                st.error(
                    "Please use a password with at least 8 characters."
                )

            else:
                with st.spinner("Creating your account..."):
                    registration = register_user(
                        email=email,
                        password=password,
                        full_name=full_name,
                    )

                if not registration.get("success"):
                    show_api_error(registration)

                else:
                    st.session_state.pending_name = full_name

                    # Log in automatically after successful registration.
                    with st.spinner("Signing you in..."):
                        login_result = login_user(email, password)

                    if not login_result.get("success"):
                        st.success(
                            "Account created successfully. "
                            "Please log in using the Login tab."
                        )

                    else:
                        login_data = result_data(
                            login_result,
                            {},
                        )

                        token = (
                            login_data.get("access_token")
                            if isinstance(login_data, dict)
                            else None
                        )

                        if not token:
                            st.success(
                                "Account created successfully. "
                                "Please log in."
                            )

                        else:
                            st.session_state.token = token

                            user_result = get_current_user(token)

                            if user_result.get("success"):
                                st.session_state.user = result_data(
                                    user_result,
                                    {},
                                )

                            st.session_state.chat_history = []

                            st.success("Account created successfully!")
                            st.rerun()



def render_dashboard(transactions, budgets):
    st.title("📊 Dashboard")

    st.write(
        f"Welcome back, **{get_user_display_name()}**!"
    )

    df = transactions_to_dataframe(transactions)

    # Show totals for the current calendar month.
    today = date.today()

    if not df.empty:
        current_month = df[
            (df["transaction_date"].dt.year == today.year)
            & (df["transaction_date"].dt.month == today.month)
        ].copy()

    else:
        current_month = df.copy()

    if current_month.empty:
        total_income = 0.0
        total_expenses = 0.0

    else:
        income_mask = (
            current_month["transaction_type"] == "income"
        )

        expense_mask = (
            current_month["transaction_type"] == "expense"
        )

        total_income = float(
            current_month.loc[income_mask, "amount"].sum()
        )

        total_expenses = float(
            current_month.loc[expense_mask, "amount"].sum()
        )

    balance = total_income - total_expenses

    st.caption(
        f"Financial summary for "
        f"{today.strftime('%B %Y')}"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "💵 Total Income",
        money(total_income),
    )

    col2.metric(
        "💸 Total Expenses",
        money(total_expenses),
    )

    col3.metric(
        "💰 Remaining Balance",
        money(balance),
    )

    col4.metric(
        "🎯 Budgets",
        len(budgets),
    )

    st.divider()

    
    st.subheader("🎯 Monthly Budget Progress")

    budget_result = get_budget_summary(
        st.session_state.token,
        today.month,
        today.year,
    )

    if not budget_result.get("success"):
        st.warning(
            "Unable to load budget progress. "
            "Please check the Budgets page."
        )
    else:
        monthly_summary = result_data(budget_result, {})

        if not isinstance(monthly_summary, dict):
            st.warning("The budget summary response was invalid.")
        else:
            monthly_budgets = monthly_summary.get("budgets", [])

            monthly_total_budget = Decimal(
                str(monthly_summary.get("total_budget", 0))
            )
            monthly_budget_spent = Decimal(
                str(monthly_summary.get("total_spent", 0))
            )
            monthly_budget_remaining = Decimal(
                str(monthly_summary.get("total_remaining", 0))
            )

            budget_col1, budget_col2, budget_col3 = st.columns(3)

            budget_col1.metric(
                "Total Budget",
                money(monthly_total_budget),
            )

            budget_col2.metric(
                "Spent in Budgeted Categories",
                money(monthly_budget_spent),
            )

            budget_col3.metric(
                "Budget Remaining",
                money(monthly_budget_remaining),
                delta=(
                    "Over budget"
                    if monthly_budget_remaining < 0
                    else None
                ),
                delta_color="inverse",
            )

            if not monthly_budgets:
                st.info(
                    "You haven't created any budgets for "
                    f"{today.strftime('%B %Y')} yet. "
                    "Open the Budgets page to create one."
                )
            else:
                # Display alerts first.
                exceeded_budgets = [
                    item
                    for item in monthly_budgets
                    if item.get("status") == "exceeded"
                ]

                warning_budgets = [
                    item
                    for item in monthly_budgets
                    if item.get("status") in ("warning", "limit_reached")
                ]

                if exceeded_budgets:
                    st.error(
                        "🚨 You have exceeded "
                        f"{len(exceeded_budgets)} budget category/categories."
                    )

                    for item in exceeded_budgets:
                        overspent = abs(
                            Decimal(str(item["remaining_budget"]))
                        )

                        st.write(
                            f"- **{item['category']}**: "
                            f"over budget by {money(overspent)}"
                        )

                if warning_budgets:
                    st.warning(
                        "⚠️ The following budgets are close to "
                        "their limits or have reached them."
                    )

                    for item in warning_budgets:
                        st.write(
                            f"- **{item['category']}**: "
                            f"{float(item['percentage_used']):.1f}% used"
                        )

                # Display individual category progress.
                for item in monthly_budgets:
                    category = item["category"]
                    limit = Decimal(str(item["monthly_limit"]))
                    spent = Decimal(str(item["amount_spent"]))
                    remaining = Decimal(str(item["remaining_budget"]))
                    percentage = float(item["percentage_used"])
                    status_value = item["status"]

                    with st.container(border=True):
                        heading_col, amount_col = st.columns([2, 1])

                        with heading_col:
                            st.markdown(f"**{category}**")

                        with amount_col:
                            st.write(
                                f"{money(spent)} / {money(limit)}"
                            )

                        progress = max(
                            0.0,
                            min(percentage / 100.0, 1.0),
                        )

                        st.progress(
                            progress,
                            text=f"{percentage:.1f}% used",
                        )

                        if status_value == "exceeded":
                            st.error(
                                f"Over budget by {money(abs(remaining))}"
                            )
                        elif status_value == "limit_reached":
                            st.warning("Your budget limit has been reached.")
                        elif status_value == "warning":
                            st.warning(
                                f"Only {money(remaining)} remaining."
                            )
                        else:
                            st.caption(
                                f"{money(remaining)} remaining in this category."
                            )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Income vs Expenses")

        if total_income == 0 and total_expenses == 0:
            st.info(
                "Add income or expense transactions "
                "to see your financial summary."
            )

        else:
            chart_df = pd.DataFrame(
                {
                    "Type": ["Income", "Expenses"],
                    "Amount": [
                        total_income,
                        total_expenses,
                    ],
                }
            )

            fig = px.bar(
                chart_df,
                x="Type",
                y="Amount",
                text="Amount",
                title="This Month",
            )

            fig.update_traces(
                texttemplate="₹%{y:,.2f}",
                textposition="outside",
            )

            fig.update_layout(
                showlegend=False,
                yaxis_title="Amount (INR)",
                xaxis_title="",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    with right:
        st.subheader("Expense Breakdown")

        if current_month.empty:
            st.info("No transactions recorded this month.")

        else:
            expenses = current_month[
                current_month["transaction_type"] == "expense"
            ]

            if expenses.empty:
                st.info("No expenses recorded this month.")

            else:
                category_totals = (
                    expenses.groupby("category")["amount"]
                    .sum()
                    .reset_index()
                )

                fig = px.pie(
                    category_totals,
                    names="category",
                    values="amount",
                    hole=0.45,
                    title="Expenses by Category",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

    st.divider()

    st.subheader("🕒 Recent Transactions")

    if df.empty:
        st.info(
            "You haven't recorded any transactions yet. "
            "Open Transactions to add your first entry."
        )

    else:
        recent = df.sort_values(
            "transaction_date",
            ascending=False,
        ).head(10)

        display_transaction_table(recent)


def render_add_transaction_form():
    st.subheader("➕ Add a Transaction")

    st.caption(
        "Record your income or expenses. "
        "Saved transactions are stored in your database."
    )

    # Keep this selector OUTSIDE the form. Streamlit reruns the app
    # when this value changes, allowing the category list to update
    # immediately between Income and Expense.
    transaction_type = st.selectbox(
        "Transaction type",
        options=["expense", "income"],
        format_func=lambda value: (
            "💸 Expense" if value == "expense"
            else "💵 Income"
        ),
        key="add_transaction_type",
    )

    if transaction_type == "income":
        categories = [
            "Salary",
            "Freelance",
            "Business",
            "Investment",
            "Other Income",
        ]
    else:
        categories = [
            "Food",
            "Groceries",
            "Transport",
            "Shopping",
            "Entertainment",
            "Bills",
            "Healthcare",
            "Education",
            "Travel",
            "Rent",
            "Utilities",
            "Other",
        ]

    with st.form("add_transaction_form", clear_on_submit=True):
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            max_value=9999999999.99,
            value=100.00,
            step=100.00,
            format="%.2f",
        )

        category = st.selectbox(
            "Category",
            options=categories,
            key=f"transaction_category_{transaction_type}",
        )

        custom_category = st.text_input(
            "Custom category (optional)",
            placeholder="Enter another category if needed",
        )

        description = st.text_input(
            "Description (optional)",
            max_chars=500,
            placeholder="e.g. Monthly salary",
        )

        transaction_date = st.date_input(
            "Transaction date",
            value=date.today(),
            max_value=date.today(),
        )

        submitted = st.form_submit_button(
            "💾 Save Transaction",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        final_category = (
            custom_category.strip()
            if custom_category.strip()
            else category
        )

        if not final_category:
            st.error("Please select or enter a category.")
            return

        if len(final_category) > 100:
            st.error(
                "Category must contain 100 characters or fewer."
            )
            return

        try:
            validated_amount = Decimal(str(amount)).quantize(
                Decimal("0.01")
            )
        except InvalidOperation:
            st.error("Please enter a valid amount.")
            return

        if validated_amount <= 0:
            st.error("Amount must be greater than zero.")
            return

        with st.spinner("Saving transaction..."):
            result = create_transaction(
                token=st.session_state.token,
                amount=validated_amount,
                category=final_category,
                description=description,
                transaction_type=transaction_type,
                transaction_date=transaction_date,
            )

        if result.get("success"):
            st.success(
                f"{transaction_type.title()} saved successfully!"
            )

            st.toast("Transaction saved!")

            # Rerun reloads data from the backend.
            st.rerun()

        else:
            show_api_error(result)


def render_transaction_history(transactions):
    st.subheader("📋 Transaction History")

    df = transactions_to_dataframe(transactions)

    if df.empty:
        st.info(
            "No transactions yet. Add your first transaction above."
        )
        return

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        type_filter = st.selectbox(
            "Filter by type",
            options=[
                "All",
                "income",
                "expense",
            ],
            format_func=lambda value: {
                "All": "All transactions",
                "income": "Income only",
                "expense": "Expenses only",
            }[value],
        )

    with filter_col2:
        categories = sorted(
            df["category"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        category_filter = st.selectbox(
            "Filter by category",
            options=["All"] + categories,
        )

    filtered = df.copy()

    if type_filter != "All":
        filtered = filtered[
            filtered["transaction_type"] == type_filter
        ]

    if category_filter != "All":
        filtered = filtered[
            filtered["category"] == category_filter
        ]

    search = st.text_input(
        "Search transactions",
        placeholder="Search category or description...",
    ).strip().lower()

    if search:
        filtered = filtered[
            filtered["category"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(search, na=False)
            |
            filtered["description"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(search, na=False)
        ]

    st.caption(
        f"Showing {len(filtered)} of {len(df)} loaded transactions."
    )

    display_transaction_table(filtered)

    st.divider()

    st.subheader("✏️ Edit a Transaction")

    if filtered.empty:
        st.info("There are no transactions available to edit.")
    else:
        edit_options = {}

        for _, row in filtered.iterrows():
            transaction_id = int(row["id"])
            edit_options[transaction_id] = (
                f"#{transaction_id} | "
                f"{row['category']} | "
                f"{money(row['amount'])}"
            )

        edit_id = st.selectbox(
            "Select a transaction to edit",
            options=list(edit_options.keys()),
            format_func=lambda value: edit_options[value],
            key="edit_transaction_id",
        )

        selected_row = filtered[
            filtered["id"].astype(int) == edit_id
        ].iloc[0]

        current_date = selected_row["transaction_date"]
        if pd.isna(current_date):
            current_date = date.today()
        else:
            current_date = current_date.date()

        current_amount = Decimal(str(selected_row["amount"]))
        current_category = str(selected_row["category"])
        current_description = selected_row["description"]

        if pd.isna(current_description):
            current_description = ""
        else:
            current_description = str(current_description)

        current_type = str(selected_row["transaction_type"])

        with st.form("edit_transaction_form"):
            edit_amount = st.number_input(
                "Amount (₹)",
                min_value=0.01,
                max_value=9999999999.99,
                value=float(current_amount),
                step=100.00,
                format="%.2f",
            )

            standard_categories = [
                "Food",
                "Transport",
                "Shopping",
                "Bills",
                "Entertainment",
                "Healthcare",
                "Education",
                "Salary",
                "Freelance",
                "Investment",
                "Other",
            ]

            if current_category not in standard_categories:
                standard_categories.append(current_category)

            edit_category = st.selectbox(
                "Category",
                options=standard_categories,
                index=standard_categories.index(current_category),
            )

            custom_edit_category = st.text_input(
                "Custom category (optional)",
                placeholder="Enter another category if needed",
            )

            edit_description = st.text_input(
                "Description (optional)",
                value=current_description,
                max_chars=500,
            )

            edit_type = st.selectbox(
                "Transaction type",
                options=["expense", "income"],
                index=["expense", "income"].index(current_type),
                format_func=lambda value: value.title(),
            )

            edit_date = st.date_input(
                "Transaction date",
                value=current_date,
            )

            edit_submitted = st.form_submit_button(
                "Save Transaction Changes",
                use_container_width=True,
                type="primary",
            )

        if edit_submitted:
            final_category = (
                custom_edit_category.strip()
                if custom_edit_category.strip()
                else edit_category
            )

            updates = {
                "amount": str(Decimal(str(edit_amount)).quantize(Decimal("0.01"))),
                "category": final_category,
                "description": edit_description.strip() or None,
                "transaction_type": edit_type,
                "transaction_date": edit_date.isoformat(),
            }

            with st.spinner("Updating transaction..."):
                result = update_transaction(
                    token=st.session_state.token,
                    transaction_id=edit_id,
                    updates=updates,
                )

            if result.get("success"):
                st.success("Transaction updated successfully.")
                st.rerun()
            else:
                show_api_error(result)

    st.divider()

    st.subheader("🗑️ Delete a Transaction")

    if filtered.empty:
        st.info("There are no transactions available to delete.")
        return

    transaction_options = {}

    for _, row in filtered.iterrows():
        transaction_id = int(row["id"])

        transaction_options[
            transaction_id
        ] = (
            f"#{transaction_id} | "
            f"{row['transaction_date'].strftime('%d %b %Y') if pd.notna(row['transaction_date']) else 'No date'} | "
            f"{row['category']} | "
            f"{money(row['amount'])}"
        )

    selected_id = st.selectbox(
        "Select a transaction",
        options=list(transaction_options.keys()),
        format_func=lambda value: transaction_options[value],
    )

    confirm_delete = st.checkbox(
        "I confirm that I want to delete this transaction."
    )

    if st.button(
        "Delete Selected Transaction",
        type="secondary",
        disabled=not confirm_delete,
    ):
        with st.spinner("Deleting transaction..."):
            result = delete_transaction(
                token=st.session_state.token,
                transaction_id=selected_id,
            )

        if result.get("success"):
            st.success("Transaction deleted successfully.")
            st.rerun()

        else:
            show_api_error(result)


def render_transactions_page(transactions):
    st.title("💳 Transactions")

    add_tab, history_tab = st.tabs(
        ["➕ Add Transaction", "📋 Transaction History"]
    )

    with add_tab:
        render_add_transaction_form()

    with history_tab:
        render_transaction_history(transactions)


def render_budgets_page():
    st.title("💰 Budget Management")
    st.caption("Set monthly limits and keep track of your spending.")

    token = st.session_state.token
    today = date.today()

    selector_col1, selector_col2 = st.columns(2)

    with selector_col1:
        selected_month = st.selectbox(
            "Month",
            options=list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda month: date(2000, month, 1).strftime("%B"),
            key="budget_month",
        )

    with selector_col2:
        selected_year = st.number_input(
            "Year",
            min_value=2000,
            max_value=2100,
            value=today.year,
            step=1,
            key="budget_year",
        )

    selected_year = int(selected_year)

    summary_result = get_budget_summary(
        token,
        selected_month,
        selected_year,
    )

    if not summary_result.get("success"):
        show_api_error(summary_result)
        return

    summary = result_data(summary_result, {})
    if not isinstance(summary, dict):
        st.error("The backend returned an invalid budget summary.")
        return

    total_budget = Decimal(str(summary["total_budget"]))
    total_spent = Decimal(str(summary["total_spent"]))
    total_remaining = Decimal(str(summary["total_remaining"]))

    st.subheader(
        f"{date(selected_year, selected_month, 1).strftime('%B %Y')} Overview"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Budget", f"₹{total_budget:,.2f}")
    col2.metric("Total Spent", f"₹{total_spent:,.2f}")
    col3.metric("Remaining", f"₹{total_remaining:,.2f}")

    if total_remaining < 0:
        st.error(
            f"You have exceeded your combined budget by "
            f"₹{abs(total_remaining):,.2f}."
        )

    st.divider()
    st.subheader("➕ Create a Monthly Budget")

    with st.form("create_budget_form"):
        category_options = [
            "Food",
            "Groceries",
            "Transport",
            "Shopping",
            "Entertainment",
            "Bills",
            "Healthcare",
            "Education",
            "Travel",
            "Rent",
            "Utilities",
            "Other",
        ]

        budget_category = st.selectbox(
            "Category",
            options=category_options,
        )
        custom_category = st.text_input(
            "Custom category (optional)",
            placeholder="Enter a category if it isn't listed",
        )
        monthly_limit = st.number_input(
            "Monthly spending limit (₹)",
            min_value=0.01,
            value=1000.0,
            step=100.0,
            format="%.2f",
        )
        create_submitted = st.form_submit_button(
            "Create Budget",
            use_container_width=True,
        )

        if create_submitted:
            category = custom_category.strip() or budget_category
            create_result = create_budget(
                token=token,
                category=category,
                monthly_limit=monthly_limit,
                month=selected_month,
                year=selected_year,
            )

            if create_result.get("success"):
                st.success(
                    f"Budget created for {category} "
                    f"({date(selected_year, selected_month, 1).strftime('%B %Y')})."
                )
                st.rerun()
            else:
                show_api_error(create_result)

    st.divider()
    st.subheader("📊 Category Budgets")

    budgets = summary.get("budgets", [])
    if not budgets:
        st.info(
            "No budgets found for this month. "
            "Create your first budget using the form above."
        )
        return

    for index, budget in enumerate(budgets):
        category = budget["category"]
        monthly_limit = Decimal(str(budget["monthly_limit"]))
        amount_spent = Decimal(str(budget["amount_spent"]))
        remaining = Decimal(str(budget["remaining_budget"]))
        percentage = float(budget["percentage_used"])
        budget_status = budget["status"]

        with st.container(border=True):
            heading_col, status_col = st.columns([3, 1])

            with heading_col:
                st.markdown(f"### {category}")

            with status_col:
                if budget_status == "exceeded":
                    st.error("Over budget")
                elif budget_status == "limit_reached":
                    st.warning("Limit reached")
                elif budget_status == "warning":
                    st.warning("Near limit")
                else:
                    st.success("Within budget")

            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("Monthly Limit", f"₹{monthly_limit:,.2f}")
            metric2.metric("Amount Spent", f"₹{amount_spent:,.2f}")
            metric3.metric("Remaining", f"₹{remaining:,.2f}")

            progress = max(0.0, min(percentage / 100.0, 1.0))
            st.progress(
                progress,
                text=f"{percentage:.2f}% of budget used",
            )

            if budget_status == "exceeded":
                st.error(
                    f"You exceeded this budget by "
                    f"₹{abs(remaining):,.2f}."
                )
            elif budget_status == "limit_reached":
                st.warning("You have used your entire budget.")
            elif budget_status == "warning":
                st.warning(
                    "You have used at least 80% of this budget. "
                    "Monitor your remaining spending."
                )

            with st.expander("Manage this budget"):
                with st.form(f"edit_budget_form_{budget['category']}_{index}"):
                    new_limit = st.number_input(
                        "New monthly limit (₹)",
                        min_value=0.01,
                        value=float(monthly_limit),
                        step=100.0,
                        format="%.2f",
                        key=f"limit_{budget['category']}_{index}",
                    )
                    update_submitted = st.form_submit_button("Update Budget")

                    if update_submitted:
                        records_result = get_budgets(
                            token,
                            month=selected_month,
                            year=selected_year,
                        )

                        if not records_result.get("success"):
                            show_api_error(records_result)
                        else:
                            budget_records = result_data(records_result, [])
                            matching_budget = next(
                                (
                                    item
                                    for item in budget_records
                                    if item["category"] == category
                                    and item["month"] == selected_month
                                    and item["year"] == selected_year
                                ),
                                None,
                            )

                            if matching_budget is None:
                                st.error("Could not find the budget record.")
                            else:
                                update_result = update_budget(
                                    token,
                                    matching_budget["id"],
                                    new_limit,
                                )

                                if update_result.get("success"):
                                    st.success("Budget updated successfully.")
                                    st.rerun()
                                else:
                                    show_api_error(update_result)

                if st.button(
                    "🗑️ Delete Budget",
                    key=f"delete_budget_{budget['category']}_{index}",
                    type="secondary",
                ):
                    records_result = get_budgets(
                        token,
                        month=selected_month,
                        year=selected_year,
                    )

                    if not records_result.get("success"):
                        show_api_error(records_result)
                    else:
                        budget_records = result_data(records_result, [])
                        matching_budget = next(
                            (
                                item
                                for item in budget_records
                                if item["category"] == category
                                and item["month"] == selected_month
                                and item["year"] == selected_year
                            ),
                            None,
                        )

                        if matching_budget is None:
                            st.error("Could not find the budget record.")
                        else:
                            delete_result = delete_budget(
                                token,
                                matching_budget["id"],
                            )

                            if delete_result.get("success"):
                                st.success("Budget deleted successfully.")
                                st.rerun()
                            else:
                                show_api_error(delete_result)

def render_ai_page():
    st.title("🤖 AI Finance Assistant")

    st.write(
        "Ask questions about your spending and personal finances."
    )

    st.caption(
        "Examples: What is my food spending? "
        "How can I reduce my expenses? "
        "Summarize my spending this month."
    )

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask your finance question..."
    )

    if question:
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your question..."):
                result = ask_finance_assistant(
                    token=st.session_state.token,
                    question=question,
                )

            if not result.get("success"):
                answer = result.get(
                    "message",
                    "Unable to get an answer.",
                )
                st.error(answer)

            else:
                data = result_data(result, {})

                if isinstance(data, dict):
                    answer = (
                        data.get("answer")
                        or data.get("response")
                        or data.get("message")
                        or str(data)
                    )

                    st.markdown(str(answer))

                    tool_result = data.get("tool_result")

                    if tool_result is not None:
                        with st.expander("View tool result"):
                            st.json(tool_result)

                else:
                    answer = str(data)
                    st.markdown(answer)

            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": str(answer),
                }
            )


def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.pending_name = ""
    st.session_state.chat_history = []

    st.rerun()

def main():
    # Logged-out state.
    if not st.session_state.token:
        render_authentication_page()
        return

    # Validate the current token.
    user_result = get_current_user(
        st.session_state.token
    )

    if not user_result.get("success"):
        st.session_state.token = None
        st.session_state.user = None

        st.warning(
            "Your session may have expired. Please log in again."
        )

        st.rerun()
        return

    st.session_state.user = result_data(
        user_result,
        {},
    )

    # Load data from the backend.
    with st.spinner("Loading your financial data..."):
        transactions = load_transactions()
        budgets = load_budgets()

    # Stop rendering financial pages if the transaction API fails.
    if transactions is None:
        st.error(
            "Unable to load transactions. Check the backend and "
            "try refreshing the page."
        )

        if st.button("Retry"):
            st.rerun()

        return

    if budgets is None:
        budgets = []

    # Sidebar.
    with st.sidebar:
        st.markdown("## 💰 Personal Finance Budget")

        st.write(
            f"Logged in as **{get_user_display_name()}**"
        )

        st.divider()

        page = st.radio(
            "Navigation",
            options=[
                "Dashboard",
                "Transactions",
                "Budgets",
                "AI Finance Assistant",
            ],
            index=0,
        )

        st.divider()

        st.caption(
            "Your financial records are retrieved from "
            "your authenticated backend account."
        )

        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):
            logout()

    # Render the selected page.
    if page == "Dashboard":
        render_dashboard(
            transactions,
            budgets,
        )

    elif page == "Transactions":
        render_transactions_page(
            transactions,
        )

    elif page == "Budgets":
        render_budgets_page()

    elif page == "AI Finance Assistant":
        render_ai_page()


if __name__ == "__main__":
    main()