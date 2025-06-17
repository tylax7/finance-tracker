import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Personal Finance Assistant", layout="centered")
st.title("💰 Personal Finance Assistant")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your finance Excel file", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    # Load expense data
    try:
        df_expense = pd.read_excel(xls, sheet_name="Leslie Expense Tracker", header=4)
        df_expense = df_expense.dropna(how="all").dropna(axis=1, how="all")
        df_expense = df_expense.rename(columns={
            df_expense.columns[1]: "Date",
            df_expense.columns[2]: "Type",
            df_expense.columns[3]: "Amount"
        })
        df_expense["Date"] = pd.to_datetime(df_expense["Date"], errors="coerce")
        df_expense = df_expense.dropna(subset=["Date", "Amount"])
    except Exception as e:
        st.error(f"Error loading expense data: {e}")

    # Load dashboard data
    try:
        df_dashboard = pd.read_excel(xls, sheet_name="Dashboard", header=None)
        nanny_row = df_dashboard[df_dashboard.astype(str).apply(lambda row: row.str.contains("nanny", case=False)).any(axis=1)]
    except:
        nanny_row = pd.DataFrame()

    st.header("📊 Expense Summary")
    st.write("Latest 10 expenses:")
    st.dataframe(df_expense.sort_values("Date", ascending=False).head(10))

    # Filter by keyword
    keyword = st.text_input("🔎 Filter expenses by keyword (e.g., 'Zelle', 'Rent', 'Nanny')")
    if keyword:
        filtered = df_expense[df_expense["Type"].astype(str).str.contains(keyword, case=False)]
        st.write(f"Found {len(filtered)} matching entries:")
        st.dataframe(filtered)
        st.write(f"**Total:** ${filtered['Amount'].sum():,.2f}")

    # Date filtering and chart
    st.subheader("📅 Date-based Spending")
    start_date = st.date_input("Start date", value=datetime.date(2025, 1, 1))
    end_date = st.date_input("End date", value=datetime.date.today())

    mask = (df_expense["Date"] >= pd.Timestamp(start_date)) & (df_expense["Date"] <= pd.Timestamp(end_date))
    df_range = df_expense.loc[mask]

    if not df_range.empty:
        weekly_summary = df_range.groupby(pd.Grouper(key="Date", freq="W"))['Amount'].sum()
        st.line_chart(weekly_summary)
        st.write(f"**Total spent in range:** ${df_range['Amount'].sum():,.2f}")

    # Nanny question response
    st.subheader("🍼 Nanny Budget Tracker")
    if not nanny_row.empty:
        st.write("**Nanny budget row (from Dashboard):**")
        st.dataframe(nanny_row)
    nanny_expenses = df_expense[df_expense["Type"].astype(str).str.contains("nanny|care", case=False)]
    if not nanny_expenses.empty:
        st.write("**Identified Nanny-related expenses:**")
        st.dataframe(nanny_expenses)
        st.write(f"**Total Paid to Nanny:** ${nanny_expenses['Amount'].sum():,.2f}")
    else:
        st.info("No nanny-related expenses found yet.")
        import os
import openai

# Load OpenAI key securely from Streamlit secrets
openai.api_key = os.getenv("OPENAI_API_KEY")

st.header("🤖 Ask a Question About Your Finances")

question = st.text_input("Ask something like 'How much did we spend on groceries last month?'")

if question and not df_expense.empty:
    with st.spinner("Thinking..."):

        # Optional: limit to 50 rows to keep it snappy
        context_data = df_expense[['Date', 'Type', 'Amount']].dropna().head(50).to_csv(index=False)

        prompt = f"""
You are a helpful finance assistant. Given this table of transactions:

{context_data}

Answer the user's question: "{question}"
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            st.markdown("**Answer:**")
            st.write(response.choices[0].message.content.strip())

        except Exception as e:
            st.error(f"Error from OpenAI: {e}")
Add natural language Q&A using OpenAI

