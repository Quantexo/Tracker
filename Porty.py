import streamlit as st
import pandas as pd

# --- Helper to build CSV URL ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_csv_url(sheet_id, sheet_gid):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"

# --- Portfolio Calculation ---
def calculate_portfolio(holdings, transactions):
    # Ensure numeric
    numeric_cols = ['Quantity', 'Avg Buy Price', 'Last Traded Price', 'Prev Close Price']
    for col in numeric_cols:
        holdings[col] = pd.to_numeric(holdings[col], errors='coerce').fillna(0)
    
    # Calculate metrics
    holdings['Current Value'] = holdings['Quantity'] * holdings['Last Traded Price']
    holdings['Invested Amount'] = holdings['Quantity'] * holdings['Avg Buy Price']
    holdings['Unrealised P&L'] = holdings['Current Value'] - holdings['Invested Amount']
    holdings['Daily P&L'] = (holdings['Last Traded Price'] - holdings['Prev Close Price']) * holdings['Quantity']
    holdings['P&L %'] = (holdings['Unrealised P&L'] / holdings['Invested Amount']) * 100

    # Calculate realized P&L
    realised_pnl = 0
    try:
        transactions['Quantity'] = pd.to_numeric(transactions['Quantity'], errors='coerce')
        transactions['Price'] = pd.to_numeric(transactions['Price'], errors='coerce')
        
        buy_data = transactions[transactions['Type'].str.lower() == 'buy']
        sell_data = transactions[transactions['Type'].str.lower() == 'sell']
        
        for _, row in sell_data.iterrows():
            symbol = row['Symbol']
            qty = row['Quantity']
            price = row['Price']
            avg_buy = buy_data[buy_data['Symbol'] == symbol]['Price'].mean()
            if not pd.isna(avg_buy):
                realised_pnl += (price - avg_buy) * qty
    except Exception as e:
        st.warning(f"Couldn't calculate realized P&L: {str(e)}")
    
    return holdings, realised_pnl

# --- Style DataFrames ---
def style_dataframe(df):
    if 'Unrealised P&L' in df.columns:
        df = df.style.applymap(
            lambda x: 'color: green' if x > 0 else 'color: red',
            subset=['Unrealised P&L', 'Daily P&L', 'P&L %']
        ).format({
            'Current Value': 'Rs {:,.2f}',
            'Invested Amount': 'Rs {:,.2f}',
            'Unrealised P&L': 'Rs {:,.2f}',
            'Daily P&L': 'Rs {:,.2f}',
            'P&L %': '{:.2f}%',
            'Avg Buy Price': 'Rs {:,.2f}',
            'Last Traded Price': 'Rs {:,.2f}',
            'Prev Close Price': 'Rs {:,.2f}'
        }, na_rep="-")
    return df

# --- Main App ---
def main():
    st.set_page_config("NEPSE Portfolio Tracker", layout="wide")
    st.title("📈 NEPSE Portfolio Tracker")
    
    with st.expander("ℹ️ How to use this app"):
        st.markdown("""
        1. Make sure your Google Sheet is publicly accessible (Anyone with link can view)
        2. Get the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/[ID]/edit`
        3. Get the GIDs for your sheets (usually found in the URL when you click on the tab)
        4. Enter the details in the sidebar and your portfolio will load automatically
        """)

    st.sidebar.header("Public Google Sheet Setup")
    sheet_id = st.sidebar.text_input("Google Sheet ID (from URL)", help="From: https://docs.google.com/spreadsheets/d/**[ID]**/edit")
    holdings_gid = st.sidebar.text_input("Holdings GID", value="0")
    transactions_gid = st.sidebar.text_input("Transactions GID", value="1347762871")
    
    if st.sidebar.button("Clear Cache"):
        st.cache_data.clear()

    if sheet_id and holdings_gid and transactions_gid:
        try:
            with st.spinner("Loading data from Google Sheets..."):
                holdings_url = get_csv_url(sheet_id, holdings_gid)
                transactions_url = get_csv_url(sheet_id, transactions_gid)

                holdings = pd.read_csv(holdings_url)
                transactions = pd.read_csv(transactions_url)

                # Validate required columns
                required_holding_cols = ['Symbol', 'Quantity', 'Avg Buy Price', 'Last Traded Price', 'Prev Close Price']
                if not all(col in holdings.columns for col in required_holding_cols):
                    st.error(f"Holdings sheet missing required columns. Needed: {', '.join(required_holding_cols)}")
                    return

                holdings, realised_pnl = calculate_portfolio(holdings, transactions)

            st.success("✅ Data loaded successfully!")
            
            # Dashboard Metrics
            total_value = holdings['Current Value'].sum()
            total_invested = holdings['Invested Amount'].sum()
            total_unrealised = holdings['Unrealised P&L'].sum()
            total_daily_pnl = holdings['Daily P&L'].sum()
            overall_return_pct = (total_unrealised / total_invested * 100) if total_invested > 0 else 0

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Value", f"Rs {total_value:,.2f}")
            col2.metric("Invested", f"Rs {total_invested:,.2f}")
            col3.metric("Unrealised P&L", f"Rs {total_unrealised:,.2f}", f"{overall_return_pct:.2f}%")
            col4.metric("Realised P&L", f"Rs {realised_pnl:,.2f}")
            col5.metric("Daily P&L", f"Rs {total_daily_pnl:,.2f}", delta=f"{total_daily_pnl:,.2f}")

            # Tables
            st.subheader("💼 Holdings")
            st.dataframe(style_dataframe(holdings), use_container_width=True)

            st.subheader("🧾 Transactions")
            st.dataframe(transactions, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            st.error("Please check:")
            st.error("- The Sheet is public (Anyone with link can view)")
            st.error("- The Sheet ID and GIDs are correct")
            st.error("- The sheet has the required columns")
    else:
        st.info("ℹ️ Enter your public Sheet ID and GIDs in the sidebar to continue.")

if __name__ == "__main__":
    main()