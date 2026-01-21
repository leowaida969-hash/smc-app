import streamlit as st
import streamlit.components.v1 as components
from google import genai
from PIL import Image
import json
import re
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NEXUS SMC // ARCHITECT",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏗️"
)

# --- PRO STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    :root { --bg: #0b0e11; --card: #15191e; --bull: #00b894; --bear: #d63031; --gold: #fdcb6e; }
    html, body, .stApp { background-color: var(--bg); font-family: 'JetBrains Mono', monospace; color: #dfe6e9; }
    
    .smc-card { background-color: var(--card); border: 1px solid #2d3436; border-radius: 4px; padding: 15px; margin-bottom: 10px; }
    
    /* Input Highlight */
    .stNumberInput input { color: #fdcb6e !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 1. CONFIG ---
API_KEY = "AIzaSyCl-vZUsHzGUFKvQU8V5q6icct1X9Xy7yg" 

# --- 2. DATA ENGINE ---
def get_market_data(symbol):
    try:
        # Fetch data (enough for chart and swings)
        df = yf.download(f"{symbol}-USD", period="1mo", interval="1h", progress=False, multi_level_index=False)
        if df.empty: return None
        return df
    except: return None

# --- 3. AUTO-ARCHITECT ENGINE (Mathematical Analysis) ---
def analyze_structure(df):
    """
    Mathematically detects Swings, OBs, and Structure without AI.
    """
    window = 20 # Lookback period
    df['swing_high'] = df['High'].rolling(window=window, center=True).max()
    df['swing_low'] = df['Low'].rolling(window=window, center=True).min()
    
    # Identify Peaks/Valleys
    highs = df[df['High'] == df['swing_high']]
    lows = df[df['Low'] == df['swing_low']]
    
    if highs.empty or lows.empty: return None

    # Get latest significant points
    last_h = highs.iloc[-1]
    prev_h = highs.iloc[-2] if len(highs) > 1 else last_h
    last_l = lows.iloc[-1]
    prev_l = lows.iloc[-2] if len(lows) > 1 else last_l
    
    # Identify Structure (HH/LH/LL/HL)
    structure_type = "NEUTRAL"
    if last_h['High'] > prev_h['High']: structure_type = "BULLISH (HH)"
    if last_l['Low'] < prev_l['Low']: structure_type = "BEARISH (LL)"
    
    # Find Potential OB (Candle before the big move)
    # We approximate OB as the candle before the lowest low (Bullish OB) or highest high (Bearish OB)
    bullish_ob = df.loc[last_l.name - pd.Timedelta(hours=1)] if last_l.name - pd.Timedelta(hours=1) in df.index else last_l
    bearish_ob = df.loc[last_h.name - pd.Timedelta(hours=1)] if last_h.name - pd.Timedelta(hours=1) in df.index else last_h

    return {
        "hh": last_h['High'],
        "ll": last_l['Low'],
        "structure": structure_type,
        "bull_ob": bullish_ob['Low'],
        "bear_ob": bearish_ob['High'],
        "prev_high": prev_h['High'],
        "current_price": df['Close'].iloc[-1]
    }

# --- 4. PLOTLY CHART ENGINE ---
def create_smc_chart(df, levels, symbol):
    df_chart = df.tail(100)
    
    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df_chart.index,
        open=df_chart['Open'], high=df_chart['High'],
        low=df_chart['Low'], close=df_chart['Close'],
        name="Price",
        increasing_line_color='#00b894', decreasing_line_color='#d63031'
    ))

    # Draw Levels if available
    if levels:
        # Swing High (HH/LH)
        fig.add_hline(y=levels['hh'], line_dash="dot", line_color="#d63031", annotation_text=f"Swing High (${levels['hh']:.2f})")
        
        # Swing Low (LL/HL)
        fig.add_hline(y=levels['ll'], line_dash="dot", line_color="#00b894", annotation_text=f"Swing Low (${levels['ll']:.2f})")
        
        # Structure Break Line
        fig.add_hline(y=levels['prev_high'], line_dash="dash", line_color="gray", annotation_text="Break Structure Level")
        
        # Order Blocks (Rectangles)
        # Bullish OB Zone
        fig.add_hrect(y0=levels['bull_ob'], y1=levels['bull_ob']*1.005, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Bullish OB")
        # Bearish OB Zone
        fig.add_hrect(y0=levels['bear_ob'], y1=levels['bear_ob']*0.995, fillcolor="red", opacity=0.1, line_width=0, annotation_text="Bearish OB")

    fig.update_layout(
        template="plotly_dark",
        height=600,
        title=f"{symbol} // SMC STRUCTURE MAP",
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False
    )
    return fig

# --- 5. AI ENGINE ---
def run_ai_analysis(symbol, price, image=None):
    client = genai.Client(api_key=API_KEY)
    prompt = f"ROLE: SMC Trader. ASSET: {symbol} (${price}). IDENTIFY: Order Blocks, FVG. OUTPUT JSON: {{'decision':'LONG/SHORT', 'setup':'Reason', 'plan':{{'entry':'price','sl':'price','tp':'price'}}}}"
    contents = [prompt]
    if image: contents.append(image)
    try:
        res = client.models.generate_content(model="gemini-flash-latest", contents=contents, config={'response_mime_type': 'application/json'})
        return res.text
    except: return None

# --- MAIN APP ---
st.title("🏗️ NEXUS SMC // ARCHITECT")

# 1. INITIALIZE & FETCH DATA
symbol_default = "BTC"
df = get_market_data(symbol_default)
structure_data = analyze_structure(df) if df is not None else None

# === SIDEBAR ===
with st.sidebar:
    st.header("🎮 CONTROL PANEL")
    
    # THE SWITCH
    ai_mode = st.toggle("🤖 AI AUTOPILOT", value=True)
    
    st.markdown("---")
    symbol = st.text_input("SYMBOL", "BTC").upper()
    
    if ai_mode:
        st.success("MODE: AI ANALYST (Auto)")
        uploaded_file = st.file_uploader("Upload Chart", type=["jpg","png"])
    else:
        st.warning("MODE: ARCHITECT (Manual/Auto-Fill)")
        st.caption("Values below are Auto-Detected from Chart Data:")
        
        # AUTO-FILL INPUTS (FIXED TypeError by using floats)
        # We pre-fill these inputs with the math calculated in 'structure_data'
        def_high = float(structure_data['hh']) if structure_data else 0.0
        def_low = float(structure_data['ll']) if structure_data else 0.0
        def_ob = float(structure_data['bull_ob']) if structure_data else 0.0
        
        m_high = st.number_input("Swing High (HH/LH)", value=def_high)
        m_low = st.number_input("Swing Low (LL/HL)", value=def_low)
        m_ob = st.number_input("Order Block Level", value=def_ob)
        
        st.markdown("### ✅ CONFLUENCE CHECK")
        # RENAMED VARIABLES TO FIX TYPE ERROR
        check_bos = st.checkbox("BOS (Break of Structure)")
        check_fvg = st.checkbox("FVG (Fair Value Gap)")
        check_liq = st.checkbox("Liquidity Sweep")
        check_choch = st.checkbox("ChoCH (Change of Character)")

# === DASHBOARD ===
if df is not None:
    current_price = df['Close'].iloc[-1]
    
    # RENAMED COLUMNS TO FIX TYPE ERROR
    d_col1, d_col2, d_col3 = st.columns(3)
    d_col1.metric("PRICE", f"${current_price:,.2f}")
    d_col2.metric("SWING HIGH", f"${structure_data['hh']:,.2f}")
    d_col3.metric("SWING LOW", f"${structure_data['ll']:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# === WORKSPACE ===
c_chart, c_logic = st.columns([2, 1])

with c_chart:
    if ai_mode:
        # TradingView for AI Mode
        components.html(f"""
        <div style="border: 1px solid #333; border-radius: 4px; overflow: hidden;">
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "width": "100%", "height": "600",
          "symbol": "BINANCE:{symbol}USDT",
          "interval": "60", "timezone": "Etc/UTC", "theme": "dark", "style": "1",
          "locale": "en", "toolbar_bg": "#15191e", "enable_publishing": false
        }});
        </script></div>
        """, height=600)
    else:
        # PLOTLY for Manual/Architect Mode (Draws Lines)
        st.markdown("### 📐 LIVE STRUCTURE MAP")
        if df is not None:
            fig = create_smc_chart(df, structure_data, symbol)
            st.plotly_chart(fig, use_container_width=True)

with c_logic:
    st.markdown(f"### {'🤖 AI BRAIN' if ai_mode else '🧠 ARCHITECT ENGINE'}")
    
    # === BRANCH 1: AI MODE ===
    if ai_mode:
        if st.button("RUN AUTO-ANALYSIS", type="primary"):
            with st.spinner("Scanning for OB & FVG..."):
                img = Image.open(uploaded_file) if uploaded_file else None
                raw = run_ai_analysis(symbol, current_price, img)
                try:
                    res = json.loads(re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL).group(1))
                    dec = res.get('decision')
                    col = "#00b894" if dec == "LONG" else "#d63031"
                    st.markdown(f"""
                    <div class="smc-card" style="border-left:5px solid {col};">
                        <h1 style="color:{col}; margin:0;">{dec}</h1>
                        <p>{res.get('setup')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    plan = res.get('plan', {})
                    st.info(f"ENTRY: {plan.get('entry')} | TP: {plan.get('tp')}")
                except: st.error("AI Failed. Try Manual Mode.")

    # === BRANCH 2: ARCHITECT MODE ===
    else:
        # Calculate Logic based on Inputs
        trend = "BULLISH" if current_price > (m_high+m_low)/2 else "BEARISH"
        
        if st.button("CALCULATE SETUP", type="primary"):
            
            # Fibonacci Math
            diff = m_high - m_low
            fib_ote = m_low + (diff * 0.382) if trend == "BULLISH" else m_high - (diff * 0.382)
            
            decision = "LONG" if trend == "BULLISH" else "SHORT"
            color = "#00b894" if decision == "LONG" else "#d63031"
            
            # 1. DECISION
            st.markdown(f"""
            <div class="smc-card" style="border: 2px solid {color}; text-align:center;">
                <h2 style="color:{color}; margin:0;">{decision} SETUP</h2>
                <p>Structure: {structure_data['structure']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. AUTO-GENERATED LEVELS
            st.markdown("#### 📐 GENERATED LEVELS")
            st.code(f"""
            SWING HIGH: ${m_high:,.2f}
            SWING LOW:  ${m_low:,.2f}
            ORDER BLOCK: ${m_ob:,.2f}
            ---------------------
            OTE ENTRY:  ${fib_ote:,.2f}
            """, language="yaml")
            
            # 3. SCORE (FIXED TYPE ERROR HERE)
            # We now sum the boolean values correctly
            score = sum([1 for check in [check_bos, check_fvg, check_liq, check_choch] if check])
            
            st.markdown("#### ✅ CONFLUENCE SCORE")
            st.progress(score / 4)
            st.caption(f"{score}/4 Confirmations Selected")
            
            if score >= 3:
                st.success("💎 A+ Setup Detected")
            elif score == 2:
                st.warning("⚠️ B-Setup (Moderate Risk)")
            else:
                st.error("❌ No Trade (Low Confluence)")
