import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Finance Dashboard", layout="wide")
st.title("Finance Visualizer")

def load_and_clean(df):
    # Remove garbage column
    df = df.drop(columns=[col for col in df.columns if col.startswith("Unnamed")], errors="ignore")

    # Date -> datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Amount -> numeric CHF
    df["Amount_numeric"] = (
        df["Amount"]
        .astype(str)
        .str.replace("CHF", "", regex=False)
        .str.replace(r"[^\d\.-]", "", regex=True)
    )
    df["Amount_numeric"] = pd.to_numeric(df["Amount_numeric"], errors="coerce").fillna(0)

    # Month
    df["Month"] = df["Date"].dt.strftime("%Y-%m")

    # Fill missing text fields
    df["Category"] = df["Category"].fillna("Uncategorized")
    df["Received / paid"] = df["Received / paid"].fillna("Unknown")
    df["If shopped, where"] = df["If shopped, where"].fillna("")

    # Remove rows with no valid date
    df = df.dropna(subset=["Date"])

    return df

uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file is None:
    st.stop()

df = pd.read_csv(uploaded_file)
df = load_and_clean(df)

# Month list sorted newest first
month_list = sorted(df["Month"].unique(), reverse=True)
selected_month = st.sidebar.selectbox("Month", month_list)
month_df = df[df["Month"] == selected_month].copy()

# Overview
paid_total = month_df[month_df["Received / paid"].str.contains("Paid", case=False, na=False)]["Amount_numeric"].sum()
received_total = month_df[month_df["Received / paid"].str.contains("Received", case=False, na=False)]["Amount_numeric"].sum()
net = received_total - paid_total

st.subheader(f"Overview: {selected_month}")
c1, c2, c3 = st.columns(3)
c1.metric("Total Paid", f"CHF {paid_total:,.2f}")
c2.metric("Total Received", f"CHF {received_total:,.2f}")
c3.metric("Net", f"CHF {net:,.2f}")

# Category breakdown
st.subheader("Category Breakdown")
cat_sum = month_df.groupby("Category", as_index=False)["Amount_numeric"].sum()

fig_pie = px.pie(
    cat_sum,
    values="Amount_numeric",
    names="Category",
    title="Spending by Category"
)
st.plotly_chart(fig_pie, use_container_width=True)

# Bar: category + type
cat_type = month_df.groupby(["Category", "Received / paid"], as_index=False)["Amount_numeric"].sum()
fig_bar = px.bar(
    cat_type,
    x="Category",
    y="Amount_numeric",
    color="Received / paid",
    barmode="group",
    title="Paid vs Received by Category"
)
st.plotly_chart(fig_bar, use_container_width=True)

# Trend over time
st.subheader("Paid vs Received Over Time")

trend = df.groupby(["Month", "Received / paid"], as_index=False)["Amount_numeric"].sum()
trend = trend.sort_values("Month")

fig_line = px.line(
    trend,
    x="Month",
    y="Amount_numeric",
    color="Received / paid",
    markers=True,
    title="Monthly Trend"
)
fig_line.update_xaxes(tickangle=45)
st.plotly_chart(fig_line, use_container_width=True)

# Detailed table
st.subheader("Detailed Transactions")
cols = ["Date", "Category", "Amount", "Received / paid", "If shopped, where"]
month_df_display = month_df[cols].copy()
month_df_display["Date"] = month_df_display["Date"].astype(str)

st.dataframe(month_df_display, use_container_width=True, height=400)

# Download filtered
csv_data = month_df_display.to_csv(index=False)
st.download_button(
    label="Download Month CSV",
    data=csv_data,
    file_name=f"transactions_{selected_month}.csv",
    mime="text/csv"
)
