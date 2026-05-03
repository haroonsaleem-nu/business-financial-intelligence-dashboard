import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="April Payments Financial Intelligence Dashboard",
    layout="wide"
)

# =========================
# LOAD DATA
# =========================
df = pd.read_excel("April Payments.xlsx")

df = df.dropna(how="all")
df.columns = [
    "Date", "Customer", "Agent", "Amount",
    "Bank", "Type", "Category"
]

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
df["Customer"] = df["Customer"].astype(str).str.strip()
df["Agent"] = df["Agent"].astype(str).str.strip()
df["Bank"] = df["Bank"].astype(str).str.strip()
df["Type"] = df["Type"].astype(str).str.strip()
df["Category"] = df["Category"].astype(str).str.strip().str.title()

df = df.dropna(subset=["Date", "Amount"])
df = df[df["Date"].dt.month == 4]

df["Day"] = df["Date"].dt.day
df["Month"] = df["Date"].dt.strftime("%B %Y")

# =========================
# HEADER
# =========================
st.title("April Payments Financial Intelligence Dashboard")
st.caption(
    "A business analytics dashboard for income, expense, profitability, "
    "agent performance, service type contribution, and banking channel insights."
)

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Business Filters")

agents = st.sidebar.multiselect(
    "Agent",
    sorted(df["Agent"].unique()),
    default=sorted(df["Agent"].unique())
)

banks = st.sidebar.multiselect(
    "Bank",
    sorted(df["Bank"].unique()),
    default=sorted(df["Bank"].unique())
)

categories = st.sidebar.multiselect(
    "Category",
    sorted(df["Category"].unique()),
    default=sorted(df["Category"].unique())
)

types = st.sidebar.multiselect(
    "Payment Type",
    sorted(df["Type"].unique()),
    default=sorted(df["Type"].unique())
)

filtered = df[
    (df["Agent"].isin(agents)) &
    (df["Bank"].isin(banks)) &
    (df["Category"].isin(categories)) &
    (df["Type"].isin(types))
]

# =========================
# KPI CALCULATIONS
# =========================
total_income = filtered[filtered["Category"] == "Income"]["Amount"].sum()
total_expense = filtered[filtered["Category"] == "Expense"]["Amount"].sum()
net_profit = total_income - total_expense
profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
transactions = len(filtered)
avg_transaction = filtered["Amount"].mean() if transactions > 0 else 0

# =========================
# KPI CARDS
# =========================
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Income", f"{total_income:,.2f}")
k2.metric("Total Expense", f"{total_expense:,.2f}")
k3.metric("Net Profit", f"{net_profit:,.2f}")
k4.metric("Profit Margin", f"{profit_margin:.2f}%")
k5.metric("Transactions", transactions)

st.divider()

# =========================
# MONTHLY SUMMARY
# =========================
st.subheader("Monthly Financial Summary")

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
# AGENT PERFORMANCE
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
# DAILY TREND
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
    title="Daily Financial Performance Trend"
)
st.plotly_chart(fig_daily, use_container_width=True)

# =========================
# CATEGORY + BANK ANALYSIS
# =========================
c1, c2 = st.columns(2)

with c1:
    st.subheader("Income vs Expense Share")
    category_summary = filtered.groupby(
        "Category", as_index=False
    )["Amount"].sum()

    fig_category = px.pie(
        category_summary,
        names="Category",
        values="Amount",
        hole=0.45,
        title="Income vs Expense Distribution"
    )
    st.plotly_chart(fig_category, use_container_width=True)

with c2:
    st.subheader("Bank-wise Payment Distribution")
    bank_summary = filtered.groupby(
        "Bank", as_index=False
    )["Amount"].sum().sort_values("Amount", ascending=False)

    fig_bank = px.bar(
        bank_summary,
        x="Bank",
        y="Amount",
        title="Bank-wise Amount"
    )
    st.plotly_chart(fig_bank, use_container_width=True)

# =========================
# TYPE BREAKDOWN
# =========================
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
# TOP CUSTOMERS
# =========================
st.subheader("Top 10 Customers by Amount")

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
# BUSINESS INSIGHTS
# =========================
st.subheader("Business Insights")

st.write(f"""
### Key Findings

- The business generated **{total_income:,.2f}** in total income during April.
- Total expenses were **{total_expense:,.2f}**, resulting in a net profit of **{net_profit:,.2f}**.
- The profit margin is **{profit_margin:.2f}%**, showing the relationship between revenue generation and cost control.
- Agent-wise analysis helps identify top-performing agents and agents with higher expense exposure.
- Payment type analysis highlights major revenue streams and operational cost drivers.
- Bank-wise analysis shows how payment activity is distributed across financial channels.

### Business Value

This dashboard supports data-driven decision-making by helping management monitor profitability,
agent productivity, revenue sources, and expense concentration in one interactive system.
""")

# =========================
# FULL DATASET
# =========================
st.subheader("Cleaned Transaction Dataset")

st.dataframe(filtered, use_container_width=True)

csv = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name="april_payment_analysis_filtered.csv",
    mime="text/csv"
)