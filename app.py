import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(
    page_title="Business Financial Intelligence Dashboard",
    layout="wide"
)

st.title("Business Financial Intelligence Dashboard")
st.caption("Upload monthly payment files or enter daily transactions manually to analyze income, expenses, profit, agents, banks, and payment types.")

# =========================
# CATEGORY DEFINITIONS
# =========================

income_types = [
    "Initial",
    "Remaining",
    "Flight Income",
    "Refund Income",
    "Refund in our Account",
    "Visa Income",
    "Total Amount",
    "Total Payment"
]
expense_types = [
    "Insurance",
    "Appointment Cost",
    "Flight Cost",
    "Refund",
    "Advertisement Cost",
    "Official Expenses",
    "Flight Purchase",
    "Ads Expense",
    "Visa Fee",
    "Visa Cost"
]

# =========================
# DATA LOADING OPTIONS
# =========================
st.sidebar.header("Data Source")

data_option = st.sidebar.radio(
    "Choose Data Input Method",
    ["Upload Monthly Excel File", "Manual Daily Entry"]
)

df = pd.DataFrame()

# =========================
# OPTION 1: UPLOAD FILE
# =========================
if data_option == "Upload Monthly Excel File":
    uploaded_file = st.sidebar.file_uploader(
        "Upload Monthly Excel File",
        type=["xlsx"]
    )

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df = df.dropna(how="all")

        if len(df.columns) == 7:
            df.columns = ["Date", "Customer", "Agent", "Amount", "Bank", "Type", "Category"]
        elif len(df.columns) == 6:
            df.columns = ["Date", "Customer", "Agent", "Amount", "Bank", "Type"]
            df["Category"] = ""
        else:
            st.error("File format issue: Excel must have 6 or 7 columns.")
            st.stop()

    else:
        st.info("Please upload a monthly Excel file to begin analysis.")
        st.stop()

# =========================
# OPTION 2: MANUAL ENTRY
# =========================
if data_option == "Manual Daily Entry":
    st.sidebar.subheader("Add Daily Transaction")

    if "manual_data" not in st.session_state:
        st.session_state.manual_data = pd.DataFrame(
            columns=["Date", "Customer", "Agent", "Amount", "Bank", "Type", "Category"]
        )

    with st.sidebar.form("manual_entry_form"):
        entry_date = st.date_input("Date", value=date.today())
        customer = st.text_input("Customer Name")
        agent = st.text_input("Agent Name")
        amount = st.number_input("Amount", min_value=0.0, step=1.0)
        bank = st.selectbox("Bank", ["Anna", "Llyods", "Other"])
        payment_type = st.selectbox(
            "Type",
            income_types + expense_types
        )

        if payment_type in income_types:
            category = "Income"
        else:
            category = "Expense"

        submitted = st.form_submit_button("Add Transaction")

        if submitted:
            new_row = pd.DataFrame([{
                "Date": entry_date,
                "Customer": customer,
                "Agent": agent,
                "Amount": amount,
                "Bank": bank,
                "Type": payment_type,
                "Category": category
            }])

            st.session_state.manual_data = pd.concat(
                [st.session_state.manual_data, new_row],
                ignore_index=True
            )

            st.success("Transaction added successfully!")

    df = st.session_state.manual_data.copy()

    if df.empty:
        st.info("Add daily transactions from the sidebar to begin analysis.")
        st.stop()

# =========================
# CLEANING
# =========================
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

df["Customer"] = df["Customer"].astype(str).str.strip()
df["Agent"] = df["Agent"].astype(str).str.strip()
df["Bank"] = df["Bank"].astype(str).str.strip()
df["Type"] = df["Type"].astype(str).str.strip()

df = df.dropna(subset=["Date", "Amount"])

# Strict category assignment
df["Category"] = df["Type"].apply(
    lambda x: "Income" if x in income_types else
    ("Expense" if x in expense_types else "Ignore")
)

df = df[df["Category"] != "Ignore"]

df["Month"] = df["Date"].dt.strftime("%B %Y")
df["Day"] = df["Date"].dt.day

# =========================
# FILTERS
# =========================
st.sidebar.header("Dashboard Filters")

agents = st.sidebar.multiselect(
    "Select Agent",
    sorted(df["Agent"].dropna().unique()),
    default=sorted(df["Agent"].dropna().unique())
)

banks = st.sidebar.multiselect(
    "Select Bank",
    sorted(df["Bank"].dropna().unique()),
    default=sorted(df["Bank"].dropna().unique())
)

categories = st.sidebar.multiselect(
    "Select Category",
    sorted(df["Category"].dropna().unique()),
    default=sorted(df["Category"].dropna().unique())
)

types = st.sidebar.multiselect(
    "Select Type",
    sorted(df["Type"].dropna().unique()),
    default=sorted(df["Type"].dropna().unique())
)

filtered = df[
    (df["Agent"].isin(agents)) &
    (df["Bank"].isin(banks)) &
    (df["Category"].isin(categories)) &
    (df["Type"].isin(types))
]

# =========================
# KPIs
# =========================
total_income = filtered[filtered["Category"] == "Income"]["Amount"].sum()
total_expense = filtered[filtered["Category"] == "Expense"]["Amount"].sum()
net_profit = total_income - total_expense
profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
transactions = len(filtered)
avg_transaction = filtered["Amount"].mean() if transactions > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Income", f"{total_income:,.2f}")
k2.metric("Total Expense", f"{total_expense:,.2f}")
k3.metric("Net Profit", f"{net_profit:,.2f}")
k4.metric("Profit Margin", f"{profit_margin:.2f}%")
k5.metric("Transactions", transactions)

st.divider()

# =========================
# MONTHLY ANALYSIS
# =========================
st.subheader("Company Monthly Financial Summary")

monthly_summary = filtered.pivot_table(
    index="Month",
    columns="Category",
    values="Amount",
    aggfunc="sum",
    fill_value=0
).reset_index()

if "Income" not in monthly_summary.columns:
    monthly_summary["Income"] = 0

if "Expense" not in monthly_summary.columns:
    monthly_summary["Expense"] = 0

monthly_summary["Net Profit"] = monthly_summary["Income"] - monthly_summary["Expense"]
monthly_summary["Profit Margin (%)"] = (
    monthly_summary["Net Profit"] / monthly_summary["Income"] * 100
).replace([float("inf"), -float("inf")], 0).fillna(0)

st.dataframe(monthly_summary, use_container_width=True)

# =========================
# DAILY ANALYSIS
# =========================
st.subheader("Daily Income, Expense & Profit Trend")

daily_summary = filtered.pivot_table(
    index="Date",
    columns="Category",
    values="Amount",
    aggfunc="sum",
    fill_value=0
).reset_index()

if "Income" not in daily_summary.columns:
    daily_summary["Income"] = 0

if "Expense" not in daily_summary.columns:
    daily_summary["Expense"] = 0

daily_summary["Net Profit"] = daily_summary["Income"] - daily_summary["Expense"]

fig_daily = px.line(
    daily_summary,
    x="Date",
    y=["Income", "Expense", "Net Profit"],
    markers=True,
    title="Daily Financial Performance"
)

st.plotly_chart(fig_daily, use_container_width=True)

st.dataframe(daily_summary, use_container_width=True)

# =========================
# AGENT ANALYSIS
# =========================
st.subheader("Agent-wise Income, Expense & Profit")

agent_summary = filtered.pivot_table(
    index="Agent",
    columns="Category",
    values="Amount",
    aggfunc="sum",
    fill_value=0
).reset_index()

if "Income" not in agent_summary.columns:
    agent_summary["Income"] = 0

if "Expense" not in agent_summary.columns:
    agent_summary["Expense"] = 0

agent_summary["Net Profit"] = agent_summary["Income"] - agent_summary["Expense"]
agent_summary["Profit Margin (%)"] = (
    agent_summary["Net Profit"] / agent_summary["Income"] * 100
).replace([float("inf"), -float("inf")], 0).fillna(0)

agent_summary = agent_summary.sort_values("Income", ascending=False)

st.dataframe(agent_summary, use_container_width=True)

fig_agent = px.bar(
    agent_summary,
    x="Agent",
    y=["Income", "Expense", "Net Profit"],
    barmode="group",
    title="Agent-wise Income, Expense & Net Profit"
)

st.plotly_chart(fig_agent, use_container_width=True)

# =========================
# TYPE AND BANK ANALYSIS
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Income vs Expense Share")
    category_summary = filtered.groupby("Category", as_index=False)["Amount"].sum()

    fig_category = px.pie(
        category_summary,
        names="Category",
        values="Amount",
        hole=0.45,
        title="Income vs Expense Distribution"
    )

    st.plotly_chart(fig_category, use_container_width=True)

with col2:
    st.subheader("Bank-wise Payment Distribution")
    bank_summary = filtered.groupby("Bank", as_index=False)["Amount"].sum()

    fig_bank = px.bar(
        bank_summary,
        x="Bank",
        y="Amount",
        title="Bank-wise Financial Flow"
    )

    st.plotly_chart(fig_bank, use_container_width=True)

st.subheader("Payment Type-wise Breakdown")

type_summary = filtered.groupby(
    ["Type", "Category"],
    as_index=False
)["Amount"].sum().sort_values("Amount", ascending=False)

fig_type = px.bar(
    type_summary,
    x="Type",
    y="Amount",
    color="Category",
    title="Income and Expense by Payment Type"
)

st.plotly_chart(fig_type, use_container_width=True)

st.dataframe(type_summary, use_container_width=True)

# =========================
# MODERN BUSINESS ANALYTICS
# =========================
st.subheader("Business Performance Insights")

largest_income_type = (
    type_summary[type_summary["Category"] == "Income"]
    .sort_values("Amount", ascending=False)
    .head(1)
)

largest_expense_type = (
    type_summary[type_summary["Category"] == "Expense"]
    .sort_values("Amount", ascending=False)
    .head(1)
)

top_agent = (
    agent_summary.sort_values("Income", ascending=False)
    .head(1)
)

st.write(f"""
### Executive Summary

- Total income generated: **{total_income:,.2f}**
- Total expenses recorded: **{total_expense:,.2f}**
- Net profit achieved: **{net_profit:,.2f}**
- Profit margin: **{profit_margin:.2f}%**
- Average transaction value: **{avg_transaction:,.2f}**

### Management Insights

- The dashboard highlights profitability, cost structure, and operational efficiency.
- Agent-wise reporting identifies which agents generate the highest income and which create higher expenses.
- Type-wise analysis identifies major revenue streams and cost drivers.
- Daily trend analysis supports cash-flow monitoring and short-term decision-making.
- Monthly summaries help management compare performance across periods when multiple monthly files are uploaded.
""")

# =========================
# CUSTOMER ANALYSIS
# =========================
st.subheader("Top Customers by Amount")

customer_summary = filtered.groupby(
    "Customer",
    as_index=False
)["Amount"].sum().sort_values("Amount", ascending=False).head(10)

fig_customer = px.bar(
    customer_summary,
    x="Customer",
    y="Amount",
    title="Top 10 Customers by Transaction Value"
)

st.plotly_chart(fig_customer, use_container_width=True)

# =========================
# DATASET + DOWNLOAD
# =========================
st.subheader("Cleaned Transaction Dataset")

st.dataframe(filtered, use_container_width=True)

csv = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name="business_financial_analysis.csv",
    mime="text/csv"
)