import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
import io

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
    # (Keep all existing calculation code the same)
    # ...
    return holdings, realised_pnl, dividend_income

# --- Historical Performance Tracking ---
def calculate_historical_performance(history_data, transactions):
    # (Keep all existing calculation code the same)
    # ...
    return history_data

# --- Style DataFrames ---
def style_dataframe(df):
    # (Keep all existing styling code the same)
    # ...
    return df

# --- Create Plotly Figures ---
def create_portfolio_value_chart(historical_perf):
    # (Keep all existing chart creation code the same)
    # ...
    return fig

def create_daily_returns_chart(historical_perf):
    # (Keep all existing chart creation code the same)
    # ...
    return fig

def create_cumulative_returns_chart(historical_perf):
    # (Keep all existing chart creation code the same)
    # ...
    return fig

def create_dividend_pie_chart(dividends):
    # (Keep all existing chart creation code the same)
    # ...
    return fig

# --- Main App ---
def main():
    st.title("📈 NEPSE Portfolio Tracker")
    
    # Add navigation sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select View", 
                           ["Dashboard", "Holdings", "Transactions", 
                            "Historic Performance", "Dividend History"])
    
    # Load all data (cached)
    @st.cache_data
    def load_data():
        with st.spinner("Loading data from Google Sheets..."):
            holdings = pd.read_csv(get_csv_url(SHEET_ID, HOLDINGS_GID))
            transactions = pd.read_csv(get_csv_url(SHEET_ID, TRANSACTIONS_GID))
            history_data = pd.read_csv(get_csv_url(SHEET_ID, HISTORY_GID))
            dividends = pd.read_csv(get_csv_url(SHEET_ID, DIVIDENDS_GID))
            
            # Validate required columns
            required_holding_cols = ['Symbol', 'Quantity', 'Avg Buy Price', 'Last Traded Price', 'Prev Close Price']
            if not all(col in holdings.columns for col in required_holding_cols):
                st.error(f"Holdings sheet missing required columns. Needed: {', '.join(required_holding_cols)}")
                return None, None, None, None
            
            holdings, realised_pnl, dividend_income = calculate_portfolio(holdings, transactions, dividends)
            historical_perf = calculate_historical_performance(history_data, transactions)
            
            return holdings, transactions, historical_perf, dividends, realised_pnl, dividend_income
    
    data = load_data()
    if data[0] is None:
        return
    
    holdings, transactions, historical_perf, dividends, realised_pnl, dividend_income = data
    
    # Dashboard View
    if page == "Dashboard":
        with st.expander("ℹ️ About this app"):
            st.markdown("""
            This app automatically tracks your NEPSE portfolio using data from a public Google Sheet.
            
            **Features:**
            - Real-time portfolio valuation
            - Unrealized and realized P&L tracking
            - Daily performance monitoring
            - Historical performance charts
            - Dividend income tracking
            """)
        
        # Dashboard Metrics
        total_value = holdings['Current Value'].sum()
        total_invested = holdings['Invested Amount'].sum()
        total_unrealised = holdings['Unrealised P&L'].sum()
        total_daily_pnl = holdings['Daily P&L'].sum()
        overall_return_pct = (total_unrealised / total_invested * 100) if total_invested > 0 else 0
        total_realised = realised_pnl + dividend_income

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Total Value", f"Rs {total_value:,.2f}")
        col2.metric("Invested", f"Rs {total_invested:,.2f}")
        col3.metric("Unrealised P&L", f"Rs {total_unrealised:,.2f}", f"{overall_return_pct:.2f}%")
        col4.metric("Realised P&L", f"Rs {realised_pnl:,.2f}")
        col5.metric("Dividend Income", f"Rs {dividend_income:,.2f}")
        col6.metric("Daily P&L", f"Rs {total_daily_pnl:,.2f}")
        
        # Mini charts
        st.subheader("Quick Overview")
        if historical_perf is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_portfolio_value_chart(historical_perf), use_container_width=True)
            with col2:
                st.plotly_chart(create_daily_returns_chart(historical_perf), use_container_width=True)
    
    # Holdings View
    elif page == "Holdings":
        st.subheader("💼 Holdings")
        st.dataframe(style_dataframe(holdings), use_container_width=True)
        
    # Transactions View
    elif page == "Transactions":
        st.subheader("🧾 Transactions")
        st.dataframe(transactions.sort_values('Date', ascending=False), use_container_width=True)
    
    # Historic Performance View
    elif page == "Historic Performance":
        st.subheader("📅 Historical Performance")
        if historical_perf is not None:
            tab1, tab2, tab3 = st.tabs(["Portfolio Value", "Daily Returns", "Cumulative Returns"])
            
            with tab1:
                fig = create_portfolio_value_chart(historical_perf)
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                fig = create_daily_returns_chart(historical_perf)
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                fig = create_cumulative_returns_chart(historical_perf)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Historical performance data not available")
    
    # Dividend History View
    elif page == "Dividend History":
        st.subheader("💰 Dividend History")
        if not dividends.empty:
            dividends['Date'] = pd.to_datetime(dividends['Date'])
            st.dataframe(dividends.sort_values('Date', ascending=False), use_container_width=True)
            
            st.subheader("📊 Dividend Analysis")
            fig = create_dividend_pie_chart(dividends)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No dividend data available")
    
    # Clear cache button in sidebar
    st.sidebar.divider()
    if st.sidebar.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

if __name__ == "__main__":
    main()