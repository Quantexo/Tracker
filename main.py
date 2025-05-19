import pandas as pd
import streamlit as st

st.set_page_config(page_title="Quantexo", layout="wide")
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    """ <style>
    .stApp {
    background-color: darkslategray;} 
    </style> <div class='header-container'> 
    <div class='header-title'>Quantexo🕵️</div> 
    <div class='header-subtitle'>💰 Advanced Insights for Bold Trades</div> </div>
    """,
    unsafe_allow_html=True
)

sector_to_companies = {
    "Commercial Banks": {"ADBL", "CZBIL", "EBL", "GBIME", "HBL", "KBL", "LSL", "MBL", "NABIL", "NBL", "NICA", "NIMB", "NMB", "PCBL", "PRVU", "SANIMA", "SBI", "SBL", "SCB"},
    "Development Banks": {"CORBL", "EDBL", "GBBL", "GRDBL", "JBBL", "KSBBL", "LBBL", "MDB", "MLBL", "MNBBL", "NABBC", "SADBL", "SAPDBL", "SHINE", "SINDU"},
    "Finance": {"BFC", "CFCL", "GFCL", "GMFIL", "GUFL", "ICFC", "JFL", "MFIL", "MPFL", "NFS", "PFL", "PROFL", "RLFL", "SFCL", "SIFC"},
    "Hotels": {"CGH", "CITY", "KDL", "OHL", "SHL", "TRH"},
    "Hydro Power": {"AHPC", "AHL", "AKJCL", "AKPL", "API", "BARUN", "BEDC", "BHDC", "BHPL", "BGWT", "BHL", "BNHC", "BPCL", "CHCL", "CHL", "CKHL", "DHPL", "DOLTI", "DORDI", "EHPL", "GHL", "GLH", "GVL", "HDHPC", "HHL", "HPPL", "HURJA", "IHL", "JOSHI", "KKHC", "KPCL", "KBSH", "LEC", "MAKAR", "MANDU", "MBJC", "MEHL", "MEL", "MEN", "MHCL", "MHNL", "MKHC", "MKHL", "MKJC", "MMKJL", "MHL", "MCHL", "MSHL", "NGPL", "NHDL", "NHPC", "NYADI", "PPL", "PHCL", "PMHPL", "PPCL", "RADHI", "RAWA", "RHGCL", "RFPL", "RIDI", "RHPL", "RURU", "SAHAS", "SHEL", "SGHC", "SHPC", "SIKLES", "SJCL", "SMH", "SMHL", "SMJC", "SPC", "SPDL", "SPHL", "SPL", "SSHL", "TAMOR", "TPC", "TSHL", "TVCL", "UHEWA", "ULHC", "UMHL", "UMRH", "UNHPL", "UPCL", "UPPER", "USHL", "USHEC", "VLUCL"},
    "Investment": {"CHDC", "CIT", "ENL", "HATHY", "HIDCL", "NIFRA", "NRN"},
    "Life Insurance": {"ALICL", "CLI", "CREST", "GMLI", "HLI", "ILI", "LICN", "NLIC", "NLICL", "PMLI", "RNLI", "SJLIC", "SNLI", "SRLI"},
    "Manufacturing and Processing": {"BNL", "BNT", "GCIL", "HDL", "NLO", "OMPL", "SARBTM", "SHIVM", "SONA", "UNL"},
    "Microfinance": {"ACLBSL", "ALBSL", "ANLB", "AVYAN", "CBBL", "CYCL", "DDBL", "DLBS", "FMDBL", "FOWAD", "GBLBS", "GILB", "GLBSL", "GMFBS", "HLBSL", "ILBS", "JBLB", "JSLBB", "KMCDB", "LLBS", "MATRI", "MERO", "MLBBL", "MLBS", "MLBSL", "MSLB", "NADEP", "NESDO", "NICLBSL", "NMBMF", "NMFBS", "NMLBBL", "NUBL", "RSDC", "SAMAJ", "SHLB", "SKBBL", "SLBBL", "SLBSL", "SMATA", "SMB", "SMFBS", "SMPDA", "SWBBL", "SWMF", "ULBSL", "UNLB", "USLB", "VLBS", "WNLB"},
    "Non Life Insurance": {"HEI", "IGI", "NICL", "NIL", "NLG", "NMIC", "PRIN", "RBCL", "SALICO", "SGIC"},
    "Others": {"HRL", "MKCL", "NRIC", "NRM", "NTC", "NWCL"},
    "Trading": {"BBC", "STC"}
}

# --- UI Layout ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    selected_sector = st.selectbox("Select Sector", [""] + list(sector_to_companies.keys()), label_visibility="collapsed")
with col2:
    filtered_companies = sorted(sector_to_companies.get(selected_sector, []))
    selected_dropdown = st.selectbox("Select Company", [""] + filtered_companies, label_visibility="collapsed", key="company")
with col3:
    user_input = st.text_input("🔍 Enter Company Symbol", "", label_visibility="collapsed", placeholder="🔍 Enter Symbol")
with col4:
    search_clicked = st.button("Search")

company_symbol = ""
if search_clicked:
    company_symbol = user_input.strip().upper() if user_input.strip() else selected_dropdown
    if not company_symbol:
        st.warning("⚠️ Please enter or select a company.")

if company_symbol:
    @st.cache_data(ttl=3600)
    def get_sheet_data(symbol, sheet_name="Daily Price"):
        try:
            gid = get_sheet_gid(sheet_name)
            url = f"https://docs.google.com/spreadsheets/d/1Q_En7VGGfifDmn5xuiF-t_02doPpwl4PLzxb4TBCW0Q/export?format=csv&gid={gid}"
            df = pd.read_csv(url).iloc[:,:7]
            df.columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            df['symbol'] = df['symbol'].astype(str).str.strip().str.upper()
            return df[df['symbol'] == symbol.upper()]
        except Exception as e:
            st.error(f"🔴 Error fetching data: {e}")
            return pd.DataFrame()
        
    def get_sheet_gid(sheet_name):
        return {"Daily Price": 0}.get(sheet_name,0)
    
    df = get_sheet_data(company_symbol)
    
    if df.empty:
            st.warning(f"No data found for {company_symbol}")
            st.stop()

    try:
        df.columns = [col.lower() for col in df.columns]
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)

        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
            if df[col].isnull().any():
                st.error(f"❌ Invalid values in {col}.")
                st.dataframe(df[df[col].isnull()][['date', col]].head())
                st.stop()

        df.dropna(inplace=True)
        df.sort_values('date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        df['point_change'] = df['close'].diff().fillna(0)
        df['tag'] = ''

    except Exception as e:
        st.error(f"⚠️ Processing error: {str(e)}")

else:
    st.info("ℹ👆🏻 Enter a company symbol to get analysed chart 👆🏻")