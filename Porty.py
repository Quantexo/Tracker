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
    sheet_id = st.sidebar.text_input("Google Sheet ID (from URL)", help="Get this from the URL: https://docs.google.com/spreadsheets/d/**[ID]**/edit")
    holdings_gid = st.sidebar.text_input("Holdings GID", value="0")
    transactions_gid = st.sidebar.text_input("Transactions GID", value="1347762871")

    if sheet_id and holdings_gid and transactions_gid:
        try:
            holdings_url = get_csv_url(sheet_id, holdings_gid)
            transactions_url = get_csv_url(sheet_id, transactions_gid)

            holdings = pd.read_csv(holdings_url)
            transactions = pd.read_csv(transactions_url)

            holdings, realised_pnl = calculate_portfolio(holdings, transactions)

            st.success("✅ Data loaded successfully!")

            # Dashboard
            st.subheader("💼 Portfolio Summary")
            total_value = holdings['Current Value'].sum()
            total_invested = holdings['Invested Amount'].sum()
            total_unrealised = holdings['Unrealised P&L'].sum()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Value", f"Rs {total_value:,.2f}")
            col2.metric("Invested", f"Rs {total_invested:,.2f}")
            col3.metric("Unrealised P&L", f"Rs {total_unrealised:,.2f}")
            col4.metric("Realised P&L", f"Rs {realised_pnl:,.2f}")

            st.subheader("📊 Holdings")
            st.dataframe(holdings, use_container_width=True)

            st.subheader("🧾 Transactions")
            st.dataframe(transactions, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
    else:
        st.info("ℹ️ Enter your public Sheet ID and GIDs to continue.")

if __name__ == "__main__":
    main()
