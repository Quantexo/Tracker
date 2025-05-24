import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config("NEPSE Portfolio Tracker", layout="wide")

# --- Configuration ---
SHEET_ID = "1ufRCvZj2neZbjSQVJaMvSZUQcP-hdYdjatTy0E_N5-M"
HOLDINGS_GID = "0"
TRANSACTIONS_GID = "1347762871"
HISTORY_GID = "391361477"
DIVIDENDS_GID = "1876183995"
# --- Helper to build CSV URL ---
@st.cache_data(ttl=3600)
def get_csv_url(sheet_id, sheet_gid):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"

# --- Portfolio Calculation ---
def calculate_portfolio(holdings, transactions, dividends=None):
    # Ensure numeric columns
    numeric_cols = ['Quantity', 'Avg Buy Price', 'Last Traded Price', 'Prev Close Price']
    for col in numeric_cols:
        holdings[col] = pd.to_numeric(holdings[col], errors='coerce').fillna(0)
    
    holdings = holdings[holdings['Quantity'] > 0]
    
    # Basic calculations
    holdings['Current Value'] = holdings['Quantity'] * holdings['Last Traded Price']
    holdings['Invested Amount'] = holdings['Quantity'] * holdings['Avg Buy Price']
    holdings['Unrealised P&L'] = holdings['Current Value'] - holdings['Invested Amount']
    holdings['Daily P&L'] = (holdings['Last Traded Price'] - holdings['Prev Close Price']) * holdings['Quantity']
    holdings['P&L %'] = (holdings['Unrealised P&L'] / holdings['Invested Amount']) * 100

    # Calculate realized P&L from transactions
    realised_pnl = 0
    try:
        transactions['Quantity'] = pd.to_numeric(transactions['Quantity'], errors='coerce')
        transactions['Price'] = pd.to_numeric(transactions['Price'], errors='coerce')
        transactions['Date'] = pd.to_datetime(transactions['Date'], errors='coerce')
        
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
    
    # Calculate dividend income if dividend data is available
    dividend_income = 0
    if dividends is not None:
        try:
            dividends['Amount'] = pd.to_numeric(dividends['Amount'], errors='coerce')
            dividends['Date'] = pd.to_datetime(dividends['Date'], errors='coerce')
            dividend_income = dividends['Amount'].sum()
            
            # Add dividend column to holdings
            dividend_by_symbol = dividends.groupby('Symbol')['Amount'].sum().reset_index()
            holdings = holdings.merge(dividend_by_symbol, on='Symbol', how='left')
            holdings['Dividend Income'] = holdings['Amount'].fillna(0)
        except Exception as e:
            st.warning(f"Couldn't process dividend data: {str(e)}")
    
    return holdings, realised_pnl, dividend_income

# --- Historical Performance Tracking ---
def calculate_historical_performance(history_data, transactions):
    try:
        history_data['Date'] = pd.to_datetime(history_data['Date'])
        history_data['Portfolio Value'] = pd.to_numeric(history_data['Portfolio Value'])
        
        # Calculate daily returns
        history_data = history_data.sort_values('Date')
        history_data['Daily Return'] = history_data['Portfolio Value'].pct_change()
        
        # Calculate cumulative returns
        history_data['Cumulative Return'] = (1 + history_data['Daily Return']).cumprod() - 1
        
        # Merge with transaction dates
        if transactions is not None:
            transactions['Date'] = pd.to_datetime(transactions['Date'])
            transactions['Transaction Amount'] = transactions['Quantity'] * transactions['Price']
            transactions['Transaction Amount'] = transactions.apply(
                lambda x: -x['Transaction Amount'] if x['Type'].lower() == 'buy' else x['Transaction Amount'],
                axis=1
            )
        
        return history_data
    except Exception as e:
        st.warning(f"Couldn't process historical data: {str(e)}")
        return None

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
            'Prev Close Price': 'Rs {:,.2f}',
            'Dividend Income': 'Rs {:,.2f}'
        }, na_rep="-")
    return df

# --- Main App ---
def main():
    st.title("📈 NEPSE Portfolio Tracker")
    
    with st.expander("ℹ️ About this app"):
        st.markdown("""
        This app automatically tracks your NEPSE portfolio using data from a public Google Sheet.
        
        **Enhanced Features:**
        - Real-time portfolio valuation
        - Unrealized and realized P&L tracking
        - Daily performance monitoring
        - Historical performance charts
        - Dividend income tracking
        """)

    try:
        with st.spinner("Loading data from Google Sheets..."):
            # Load all data sources
            holdings_url = get_csv_url(SHEET_ID, HOLDINGS_GID)
            transactions_url = get_csv_url(SHEET_ID, TRANSACTIONS_GID)
            history_url = get_csv_url(SHEET_ID, HISTORY_GID)
            dividends_url = get_csv_url(SHEET_ID, DIVIDENDS_GID)

            holdings = pd.read_csv(holdings_url)
            transactions = pd.read_csv(transactions_url)
            history_data = pd.read_csv(history_url)
            dividends = pd.read_csv(dividends_url)

            # Validate required columns
            required_holding_cols = ['Symbol', 'Quantity', 'Avg Buy Price', 'Last Traded Price', 'Prev Close Price']
            if not all(col in holdings.columns for col in required_holding_cols):
                st.error(f"Holdings sheet missing required columns. Needed: {', '.join(required_holding_cols)}")
                return

            # Calculate portfolio metrics
            holdings, realised_pnl, dividend_income = calculate_portfolio(holdings, transactions, dividends)
            
            # Calculate historical performance
            historical_perf = calculate_historical_performance(history_data, transactions)

        st.success("✅ Data loaded successfully!")
        
        # Dashboard Metrics
        total_value = holdings['Current Value'].sum()
        total_invested = holdings['Invested Amount'].sum()
        total_unrealised = holdings['Unrealised P&L'].sum()
        total_daily_pnl = holdings['Daily P&L'].sum()
        overall_return_pct = (total_unrealised / total_invested * 100) if total_invested > 0 else 0

        # Add dividend income to realized P&L
        total_realised = realised_pnl + dividend_income

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Total Value", f"Rs {total_value:,.2f}")
        col2.metric("Invested", f"Rs {total_invested:,.2f}")
        col3.metric("Unrealised P&L", f"Rs {total_unrealised:,.2f}", f"{overall_return_pct:.2f}%")
        col4.metric("Realised P&L", f"Rs {realised_pnl:,.2f}")
        col5.metric("Dividend Income", f"Rs {dividend_income:,.2f}")
        col6.metric("Daily P&L", f"Rs {total_daily_pnl:,.2f}")

        # Historical Performance Charts
        st.subheader("📅 Historical Performance")
        if historical_perf is not None:
            tab1, tab2, tab3 = st.tabs(["Portfolio Value", "Daily Returns", "Cumulative Returns"])
            
            with tab1:
                fig = px.line(historical_perf, x='Date', y='Portfolio Value', 
                             title='Portfolio Value Over Time')
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                fig = px.bar(historical_perf, x='Date', y='Daily Return', 
                            title='Daily Returns', color='Daily Return',
                            color_continuous_scale=['red', 'green'])
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                fig = px.line(historical_perf, x='Date', y='Cumulative Return',
                             title='Cumulative Returns')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Historical performance data not available or couldn't be processed")

        # Holdings Table
        st.subheader("💼 Holdings")
        st.dataframe(style_dataframe(holdings), use_container_width=True)

        # Dividend History
        if not dividends.empty:
            st.subheader("💰 Dividend History")
            dividends['Date'] = pd.to_datetime(dividends['Date'])
            st.dataframe(dividends.sort_values('Date', ascending=False), use_container_width=True)

        # Transactions Table
        st.subheader("🧾 Transactions")
        st.dataframe(transactions.sort_values('Date', ascending=False), use_container_width=True)

        # At the bottom of your main content
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Clear Cache"):
                st.cache_data.clear()
                st.rerun()

    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.error("Please check your Google Sheet configuration and ensure it's publicly accessible.")
    
if __name__ == "__main__":
    main()