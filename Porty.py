import streamlit as st
import pandas as pd

# --- Helper to build CSV URL ---
def get_csv_url(sheet_id, sheet_gid):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"

# --- Portfolio Calculation ---
def calculate_portfolio(holdings, transactions):
    holdings['Current Value'] = holdings['Quantity'] * holdings['Last Traded Price']
    holdings['Invested Amount'] = holdings['Quantity'] * holdings['Avg Buy Price']
    holdings['Unrealised P&L'] = holdings['Current Value'] - holdings['Invested Amount']
    holdings['Daily P&L'] = (holdings['Last Traded Price'] - holdings['Prev Close Price']) * holdings['Quantity']

    realised_pnl = 0
    buy_data = transactions[transactions['Type'].str.lower() == 'buy']
    sell_data = transactions[transactions['Type'].str.lower() == 'sell']

    for _, row in sell_data.iterrows():
        symbol = row['Symbol']
        qty = row['Quantity']
        price = row['Price']
        avg_buy = buy_data[buy_data['Symbol'] == symbol]['Price'].mean()
        realised_pnl += (price - avg_buy) * qty

    return holdings, realised_pnl

# --- Main App ---
def main():
    st.set_page_config("NEPSE Portfolio Tracker", layout="wide")
    st.title("📈 NEPSE Portfolio Tracker")

    st.sidebar.header("Public Google Sheet Setup")
    sheet_id = st.sidebar.text_input("Google Sheet ID (from URL)", help="From: https://docs.google.com/spreadsheets/d/**[ID]**/edit")
    holdings_gid = st.sidebar.text_input("Holdings GID", value="0")
    transactions_gid = st.sidebar.text_input("Transactions GID", value="1347762871")

    if sheet_id and holdings_gid and transactions_gid:
        try:
            holdings_url = get_csv_url(sheet_id, holdings_gid)
            transactions_url = get_csv_url(sheet_id, transactions_gid)

            holdings = pd.read_csv(holdings_url)
            transactions = pd.read_csv(transactions_url)

            # Ensure numeric
            for col in ['Quantity', 'Avg Buy Price', 'Last Traded Price', 'Prev Close Price']:
                holdings[col] = pd.to_numeric(holdings[col], errors='coerce')

            for col in ['Quantity', 'Price']:
                transactions[col] = pd.to_numeric(transactions[col], errors='coerce')

            holdings, realised_pnl = calculate_portfolio(holdings, transactions)

            st.success("✅ Data loaded successfully!")

            # Dashboard Metrics
            total_value = holdings['Current Value'].sum()
            total_invested = holdings['Invested Amount'].sum()
            total_unrealised = holdings['Unrealised P&L'].sum()
            total_daily_pnl = holdings['Daily P&L'].sum()

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Value", f"Rs {total_value:,.2f}")
            col2.metric("Invested", f"Rs {total_invested:,.2f}")
            col3.metric("Unrealised P&L", f"Rs {total_unrealised:,.2f}")
            col4.metric("Realised P&L", f"Rs {realised_pnl:,.2f}")
            col5.metric("Daily P&L", f"Rs {total_daily_pnl:,.2f}", delta=f"{total_daily_pnl:,.2f}")

            # Tables
            st.subheader("💼 Holdings")
            st.dataframe(holdings, use_container_width=True)

            st.subheader("🧾 Transactions")
            st.dataframe(transactions, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
    else:
        st.info("ℹ️ Enter your public Sheet ID and GIDs to continue.")

if __name__ == "__main__":
    main()
