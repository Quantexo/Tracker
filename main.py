import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta
import pytz
import kaleido
import plotly.io as pio

# --- Page Setup ---

st.set_page_config(page_title="Quantexo", layout="wide")

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    """ <style>
    .stApp {
    background-color: darkslategray;
    } </style> <div class='header-container'> <div class='header-title'>Quantexo🕵️</div> <div class='header-subtitle'>💰 Advanced Insights for Bold Trades</div> </div>
    """,
    unsafe_allow_html=True
)
# --- SECTOR TO COMPANY MAPPING ---
sector_to_companies ={
    "Commercial Banks": {"ADBL","CZBIL","EBL","GBIME","HBL","KBL","LSL","MBL","NABIL","NBL","NICA","NIMB","NMB","PCBL","PRVU","SANIMA","SBI","SBL","SCB"},
    "Development Banks": {"CORBL","EDBL","GBBL","GRDBL","JBBL","KSBBL","LBBL","MDB","MLBL","MNBBL","NABBC","SADBL","SAPDBL","SHINE","SINDU"},
    "Finance": {"BFC","CFCL","GFCL","GMFIL","GUFL","ICFC","JFL","MFIL","MPFL","NFS","PFL","PROFL","RLFL","SFCL","SIFC"},
    "Hotels": {"CGH","CITY","KDL","OHL","SHL","TRH"},
    "Hydro Power": {"AHPC", "AHL", "AKJCL", "AKPL", "API", "BARUN", "BEDC", "BHDC", "BHPL", "BGWT", "BHL", "BNHC", "BPCL", "CHCL", "CHL", "CKHL", "DHPL", "DOLTI", "DORDI", "EHPL", "GHL", "GLH", "GVL", "HDHPC", "HHL", "HPPL", "HURJA", "IHL", "JOSHI", "KKHC", "KPCL", "KBSH", "LEC", "MAKAR", "MANDU", "MBJC", "MEHL", "MEL", "MEN", "MHCL", "MHNL", "MKHC", "MKHL", "MKJC", "MMKJL", "MHL", "MCHL", "MSHL", "NGPL", "NHDL", "NHPC", "NYADI", "PPL", "PHCL", "PMHPL", "PPCL", "RADHI", "RAWA", "RHGCL", "RFPL", "RIDI", "RHPL", "RURU", "SAHAS", "SHEL", "SGHC", "SHPC", "SIKLES", "SJCL", "SMH", "SMHL", "SMJC", "SPC", "SPDL", "SPHL", "SPL", "SSHL", "TAMOR", "TPC", "TSHL", "TVCL", "UHEWA", "ULHC", "UMHL", "UMRH", "UNHPL", "UPCL", "UPPER", "USHL", "USHEC", "VLUCL"},
    "Investment": {"CHDC","CIT","ENL","HATHY","HIDCL","NIFRA","NRN"},
    "Life Insurance":{"ALICL","CLI","CREST","GMLI","HLI","ILI","LICN","NLIC","NLICL","PMLI","RNLI","SJLIC","SNLI","SRLI"},
    "Manufacturing and Processing": {"BNL","BNT","GCIL","HDL","NLO","OMPL","SARBTM","SHIVM","SONA","UNL"},
    "Microfinance": {"ACLBSL","ALBSL","ANLB","AVYAN","CBBL","CYCL","DDBL","DLBS","FMDBL","FOWAD","GBLBS","GILB","GLBSL","GMFBS","HLBSL","ILBS","JBLB","JSLBB","KMCDB","LLBS","MATRI","MERO","MLBBL","MLBS","MLBSL","MSLB","NADEP","NESDO","NICLBSL","NMBMF","NMFBS","NMLBBL","NUBL","RSDC","SAMAJ","SHLB","SKBBL","SLBBL","SLBSL","SMATA","SMB","SMFBS","SMPDA","SWBBL","SWMF","ULBSL","UNLB","USLB","VLBS","WNLB"},
    "Non Life Insurance": {"HEI","IGI","NICL","NIL","NLG","NMIC","PRIN","RBCL","SALICO","SGIC"},
    "Others": {"HRL","MKCL","NRIC","NRM","NTC","NWCL"},
    "Trading": {"BBC","STC"}
}
#---UI LAYOUT---
col1, col2, col3, col4 =st.columns([0.5,0.5,0.5,0.5])

# --- Sector Selection ---
with col1:
    selected_sector = st.selectbox("Select Sector",options=[""]+ list(sector_to_companies.keys()),label_visibility= "collapsed")
# ---Filter Companies based on Sector ---
with col2:
    if selected_sector:
        filered_companies = sorted(sector_to_companies[selected_sector])
    else:
        filered_companies =[]
    
    selected_dropdown = st.selectbox(
        "Select Company",
        options=[""]+ filered_companies,
        label_visibility= "collapsed",
        key="company"
    )
# ---Manual Input---
with col3:
    user_input = st.text_input(
        "🔍 Enter Company Symbol",
        "",
        label_visibility= "collapsed",
        placeholder= "🔍 Enter Symbol"
    )
with col4:
    col_search, col_scan =st.columns([1,1])
    with col_search:
        search_clicked = st.button("Search")
    with col_scan:
        scan_all_clicked = st.button("Scan All")

# Define function to get sheet data (outside the if blocks)
@st.cache_data(ttl=3600)
def get_sheet_data(symbol, sheet_name="Daily Price"):
    try:
        # Google Sheets URL with the specific sheet's gid
        sheet_url = f"https://docs.google.com/spreadsheets/d/1Q_En7VGGfifDmn5xuiF-t_02doPpwl4PLzxb4TBCW0Q/export?format=csv&gid={get_sheet_gid(sheet_name)}"

        # Read data as CSV directly (no auth needed if public)
        df = pd.read_csv(sheet_url)

        # Ensure only the first 7 columns are used (ignoring any additional columns)
        df = df.iloc[:, :7]  # Select only the first 7 columns

        # Define the columns based on the new column mappings
        df.columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']

        # Filter data based on company symbol
        df['symbol'] = df['symbol'].astype(str).str.strip().str.upper()
        return df[df['symbol'].str.upper() == symbol.upper()]
    except Exception as e:
        st.error(f"🔴 Error fetching data: {str(e)}")
        return pd.DataFrame()

def get_sheet_gid(sheet_name):
    # You need to know the gid value of the sheet, or you can find it in the sheet's URL when editing the sheet
    sheet_gids = {
        "Daily Price": 0,  # Default sheet (GID of Sheet1)
        # Add more sheets here with their respective GIDs
    }
    return sheet_gids.get(sheet_name, 0)  # Default to GID 0 if sheet_name not found

# Define the detect_signals function outside if blocks
def detect_signals(df):
    results = []
    # Make a copy of the dataframe to avoid modifying the original
    df_signals = df.copy()
    df_signals['point_change'] = df_signals['close'].diff().fillna(0)
    df_signals['tag'] = ''

    min_window = min(20, max(5, len(df_signals) // 2)) 
    avg_volume = df_signals['volume'].rolling(window=min_window).mean().fillna(method='bfill').fillna(df_signals['volume'].mean())

    for i in range(min(3, len(df_signals)-1), len(df_signals)):
        row = df_signals.iloc[i]
        prev = df_signals.iloc[i - 1]
        next_candles = df_signals.iloc[i + 1:min(i + 6, len(df_signals))]
        body = abs(row['close'] - row['open'])
        prev_body = abs(prev['close'] - prev['open'])
        recent_tags = df_signals['tag'].iloc[max(0, i - 9):i]
        
        if (
            row['close'] > row['open'] and
            row['close'] >= row['high'] - (row['high'] - row['low']) * 0.1 and
            row['volume'] > avg_volume[i] * 2 and
            body > prev_body and
            '🟢' not in recent_tags.values
        ):
            df_signals.at[i, 'tag'] = '🟢'
        elif (
            row['open'] > row['close'] and
            row['close'] <= row['low'] + (row['high'] - row['low']) * 0.1 and
            row['volume'] > avg_volume[i] * 2 and
            body > prev_body and
            '🔴' not in recent_tags.values
        ):
            df_signals.at[i, 'tag'] = '🔴'
        elif (
            row['close'] > row['open'] and
            row['volume'] > avg_volume[i] * 1.2
        ):
            df_signals.loc[df_signals['tag'] == '⛔', 'tag'] = ''
            for j, candle in next_candles.iterrows():
                if candle['close'] < row['open']:
                    df_signals.at[j, 'tag'] = '⛔'
                    break
        elif (
            row['open'] > row['close'] and
            row['volume'] > avg_volume[i] * 1.2
        ):
            df_signals.loc[df_signals['tag'] == '🚀', 'tag'] = ''
            for j, candle in next_candles.iterrows():
                if candle['close'] > row['open']:
                    df_signals.at[j, 'tag'] = '🚀'
                    break
        elif (
            i >= 10 and
            row['high'] > max(df_signals['high'].iloc[i - 10:i]) and
            row['volume'] > avg_volume[i] * 1.8
        ):
            if not (df_signals['tag'].iloc[i - 8:i] == '💥').any():
                df_signals.at[i, 'tag'] = '💥'
        elif (
            i >= 10 and
            row['low'] < min(df_signals['low'].iloc[i - 10:i]) and
            row['volume'] > avg_volume[i] * 1.8
        ):
            if not (df_signals['tag'].iloc[i - 8:i] == '💣').any():
                df_signals.at[i, 'tag'] = '💣'
        elif (
            row['close'] > row['open'] and
            body > (row['high'] - row['low']) * 0.7 and
            row['volume'] > avg_volume[i] * 2
        ):
            df_signals.at[i, 'tag'] = '🐂'
        elif (
            row['open'] > row['close'] and
            body > (row['high'] - row['low']) * 0.7 and
            row['volume'] > avg_volume[i] * 2
        ):
            df_signals.at[i, 'tag'] = '🐻'

        if df_signals.at[i,'tag']:
            results.append({
                'symbol': row['symbol'],
                'tag': df_signals.at[i, 'tag'],
                'date': row['date'].strftime('%Y-%m-%d'),  # Corrected date format
                'price': row['close'],
                'volume': row['volume']
            })
    
    return results, df_signals  # Return both results and the modified dataframe

# --- Priority: Manual Entry Overries Dropdown ---
if search_clicked:
    if user_input.strip():
        company_symbol = user_input.strip().upper()
    elif selected_dropdown:
        company_symbol = selected_dropdown
    else:
        st.warning("⚠️ Please enter or select a company.")
        company_symbol = ""
else:
    company_symbol = ""

# Scan All Companies
if scan_all_clicked:
    st.subheader("📊 Signal Scan Results for All Companies")
    all_results = []
    sheet_name = "Daily Price"

    # Flatten all companies
    all_companies = sorted(set().union(*sector_to_companies.values()))

    progress = st.progress(0, text="🔍 Scanning...")

    for i, symbol in enumerate(all_companies):
        df = get_sheet_data(symbol, sheet_name)
        if df.empty:
            continue

        df.columns = [col.lower() for col in df.columns]
        df['symbol'] = symbol
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('[^\d.]', '', regex=True), errors='coerce')
            df = df.dropna()
            df.sort_values('date', inplace=True)
            df.reset_index(drop=True, inplace=True)

            if len(df) > 10:
                results, _ = detect_signals(df)  # Ignore the second return value
                all_results.extend(results)
        except Exception as e:
            st.warning(f"⚠️ Error processing {symbol}: {str(e)}")

        progress.progress((i + 1) / len(all_companies), text=f"Scanning {symbol}...")

    progress.empty()

    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df = result_df.sort_values(by="date", ascending=False)
        st.dataframe(result_df, use_container_width=True)
    else:
        st.info("✅ No signals found across companies.")

# Process individual company
if company_symbol:
    sheet_name = "Daily Price"
    df = get_sheet_data(company_symbol, sheet_name)

    if df.empty:
        st.warning(f"No data found for {company_symbol}")
        st.stop()

    try:
        # Convert column names to lowercase
        df.columns = [col.lower() for col in df.columns]

        # Check required columns
        required_cols = {'date', 'open', 'high', 'low', 'close', 'volume'}
        if not required_cols.issubset(set(df.columns)):
            st.error("❌ Missing required columns: date, open, high, low, close, volume")
            st.stop()

        # Convert and validate dates
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        if df['date'].isnull().any():
            st.error("❌ Invalid date format in some rows")
            st.stop()

        # Validate numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace('[^\d.]', '', regex=True),  # Remove non-numeric chars
                errors='coerce'
            )
            if df[col].isnull().any():
                bad_rows = df[df[col].isnull()][['date', col]].head()
                st.error(f"❌ Found {df[col].isnull().sum()} invalid values in {col} column. Examples:")
                st.dataframe(bad_rows)
                st.stop()

        # Remove any rows with NA values
        df = df.dropna()
        if len(df) == 0:
            st.error("❌ No valid data after cleaning")
            st.stop()

        # Sort and reset index
        df.sort_values('date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Call detect_signals and get both results and processed dataframe
        _, df_with_signals = detect_signals(df)
                
        # --- Visualization ---
        st.subheader(f"{company_symbol} - Smart Money Line Chart")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_with_signals['date'], y=df_with_signals['close'],
            mode='lines', name='Close Price',
            line=dict(color='lightblue', width=2),
            customdata=df_with_signals[['date', 'open', 'high', 'low', 'close', 'point_change']],
            hovertemplate=(
                "📅 Date: %{customdata[0]|%Y-%m-%d}<br>" +
                "🟢 Open: %{customdata[1]:.2f}<br>" +
                "📈 High: %{customdata[2]:.2f}<br>" +
                "📉 Low: %{customdata[3]:.2f}<br>" +
                "💰 LTP: %{customdata[4]:.2f}<br>" +
                "📊 Point Change: %{customdata[5]:.2f}<extra></extra>"
            )
        ))  

        tag_labels = {
            '🟢': '🟢 Aggressive Buyers',
            '🔴': '🔴 Aggressive Sellers',
            '⛔': '⛔ Buyer Absorption',
            '🚀': '🚀 Seller Absorption',
            '💥': '💥 Bullish POR',
            '💣': '💣 Bearish POR',
            '🐂': '🐂 Bullish POI',
            '🐻': '🐻 Bearish POI'
        }

        signals = df_with_signals[df_with_signals['tag'] != '']
        for tag in signals['tag'].unique():
            subset = signals[signals['tag'] == tag]
            fig.add_trace(go.Scatter(
                x=subset['date'], y=subset['close'],
                mode='markers+text',
                name=tag_labels.get(tag, tag),
                text=[tag] * len(subset),
                textposition='top center',
                textfont=dict(size=20),
                marker=dict(size=14, symbol="circle", color='white'),
                customdata=subset[['open', 'high', 'low', 'close', 'point_change']].values,
                hovertemplate=(
                    "📅 Date: %{x|%Y-%m-%d}<br>" +
                    "🟢 Open: %{customdata[0]:.2f}<br>" +
                    "📈 High: %{customdata[1]:.2f}<br>" +
                    "📉 Low: %{customdata[2]:.2f}<br>" +
                    "🔚 Close: %{customdata[3]:.2f}<br>" +
                    "📊 Point Change: %{customdata[4]:.2f}<br>" +
                    f"{tag_labels.get(tag, tag)}<extra></extra>"
                )
            ))

        # Calculate 15 days ahead of the last date
        last_date = df_with_signals['date'].max()
        extended_date = last_date + timedelta(days=15)
        chart_bg = ""
        fig.update_layout(
            height=800,
            width=1800,
            plot_bgcolor="darkslategray",
            paper_bgcolor="darkslategray",
            font_color="white",
            title=chart_bg,
            xaxis=dict(title="Date", tickangle=-45, showgrid=False, range=[df_with_signals['date'].min(),extended_date]), #extend x-axis to show space after latest date
            yaxis=dict(title="Price", showgrid=False, zeroline=True, zerolinecolor="gray", autorange=True),
            margin=dict(l=50, r=50, b=130, t=50),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,  # Adjust this value to move further down if needed
                xanchor="center",
                x=0.5,
                font=dict(size=14),
                bgcolor="rgba(0,0,0,0)"  # Optional: keeps legend background transparent)
            ),
            # Add zoom and pan capabilities
            dragmode="zoom",  # Enable box zoom
            annotations=[
                dict(
                    text=f"{company_symbol} <br> Quantexo",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    xanchor="center", yanchor="middle",
                    font=dict(size=25, color="rgba(59, 59, 59)"),
                    showarrow=False
                )
            ]
        )
        st.plotly_chart(fig, use_container_width=False)      
    except Exception as e:
        st.error(f"⚠️ Processing error: {str(e)}")
else:
    st.info("ℹ👆🏻 Enter a company symbol to get analysed chart 👆🏻")