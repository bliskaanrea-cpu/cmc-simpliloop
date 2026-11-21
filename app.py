import os
from typing import TypedDict

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SimpliLoop | CMC Command Center",
    page_icon="logo.png.jpg" if os.path.exists("logo.png.jpg") else "🔄",
    layout="wide",
)

if os.path.exists("banner.png.jpg"):
    col_banner, col_spacer = st.columns([2, 3])
    with col_banner:
        st.image("banner.png.jpg", use_container_width=True)

# --- STRICT DATA MODELS ---
class AssetMetrics(TypedDict):
    name: str
    symbol: str
    category: str
    price: float
    mcap_b: float
    pct_24h: float
    revenue_score: float
    risk: str
    inconvenience: str
    net_score: float


# --- API CONFIGURATION ---
API_KEY = os.getenv("CMC_API_KEY", "").strip()
BASE_HOST = "https://" + "pro-api." + "coinmarketcap.com"
LISTINGS_URL = f"{BASE_HOST}/v1/cryptocurrency/listings/latest"
FNG_URL = f"{BASE_HOST}/v3/fear-and-greed/latest"

BLUE_CHIPS = {"BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "LINK", "TON", "SUI"}
SAFE_RESERVES = {"USDT", "USDC", "DAI", "FDUSD", "USDe", "PAXG", "XAUT", "ONDO"}


@st.cache_data(ttl=60)
def fetch_cmc_listings(key: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    if not key:
        return [], {"error": "CMC_API_KEY is empty. Check your .env file."}

    headers = {
        "X-CMC_PRO_API_KEY": key,
        "Accept": "application/json",
        "User-Agent": "SimpliLoop-CMC-Hackathon/1.0",
    }
    # Fetch top 40 by market cap to capture Blue Chips + Emerging High-Cap Movers
    params: dict[str, str | int] = {"start": 1, "limit": 40, "convert": "USD"}

    try:
        response = requests.get(LISTINGS_URL, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return [], {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
        if not response.text.strip():
            return [], {"error": f"Empty response from {response.url}"}
        payload = response.json()  # pyright: ignore[reportAny]
        if isinstance(payload, dict):
            raw_list = payload.get("data", [])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            status_obj = payload.get("status", {})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            clean_list = [item for item in raw_list if isinstance(item, dict)] if isinstance(raw_list, list) else []  # pyright: ignore[reportUnknownVariableType]
            clean_status = status_obj if isinstance(status_obj, dict) else {}  # pyright: ignore[reportUnknownVariableType]
            return clean_list, clean_status  # pyright: ignore[reportReturnType]
        return [], {}
    except requests.RequestException as err:
        return [], {"error": str(err)}


@st.cache_data(ttl=300)
def fetch_fear_and_greed(key: str) -> tuple[int, str]:
    if not key:
        return 50, "Neutral (No Key)"

    headers = {
        "X-CMC_PRO_API_KEY": key,
        "Accept": "application/json",
        "User-Agent": "SimpliLoop-CMC-Hackathon/1.0",
    }
    try:
        response = requests.get(FNG_URL, headers=headers, timeout=10)
        if response.status_code != 200 or not response.text.strip():
            return 50, f"HTTP {response.status_code}"
        payload = response.json()  # pyright: ignore[reportAny]
        if isinstance(payload, dict):
            data = payload.get("data", {})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            if isinstance(data, dict):
                val = int(data.get("value", 50))  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                label = str(data.get("value_classification", "Neutral"))  # pyright: ignore[reportUnknownMemberType]
                return val, label
        return 50, "Neutral"
    except requests.RequestException:
        return 50, "Unavailable"


def _to_float(val: object) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return 0.0
    return 0.0


# --- ANALYTICAL SCORING ENGINE ---
def analyze_asset(coin: dict[str, object]) -> AssetMetrics:
    symbol = str(coin.get("symbol", "N/A")).upper()
    quote_map = coin.get("quote")
    usd_quote: dict[str, object] = {}
    if isinstance(quote_map, dict):
        usd_raw = quote_map.get("USD")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if isinstance(usd_raw, dict):
            usd_quote = usd_raw  # pyright: ignore[reportUnknownVariableType]

    price = _to_float(usd_quote.get("price"))
    pct_24h = _to_float(usd_quote.get("percent_change_24h"))
    pct_7d = _to_float(usd_quote.get("percent_change_7d"))
    vol_24h = _to_float(usd_quote.get("volume_24h"))
    mcap = _to_float(usd_quote.get("market_cap"))

    # Classify Asset Role in the Ecosystem
    if symbol in SAFE_RESERVES:
        category = "🛡️ Safe / RWA"
    elif symbol in BLUE_CHIPS:
        category = "🏆 Blue Chip"
    else:
        category = "🚀 Rising Mover"

    momentum = max(0.0, min(100.0, 50.0 + (pct_24h * 3.0) + (pct_7d * 1.5)))

    volatility = abs(pct_24h)
    if volatility > 8.0 or pct_24h < -5.0:
        risk = "🔴 High"
    elif volatility > 3.0:
        risk = "🟡 Medium"
    else:
        risk = "🟢 Low"

    liq_ratio = (vol_24h / mcap) * 100.0 if mcap > 0.0 else 0.0
    if liq_ratio > 5.0:
        friction = "⚡ Easy (Deep Liquidity)"
    elif liq_ratio > 1.5:
        friction = "⚖️ Moderate"
    else:
        friction = "🐢 High Friction (Low Vol)"

    net_score = round(momentum - (volatility * 2.0) + min(liq_ratio * 2.0, 20.0), 1)

    return {
        "name": str(coin.get("name", "Unknown")),
        "symbol": symbol,
        "category": category,
        "price": round(price, 4) if price < 1.0 else round(price, 2),
        "mcap_b": round(mcap / 1_000_000_000.0, 2),
        "pct_24h": round(pct_24h, 2),
        "revenue_score": round(momentum, 1),
        "risk": risk,
        "inconvenience": friction,
        "net_score": net_score,
    }


# --- SESSION STATE ---
if "active_coin" not in st.session_state:
    st.session_state.active_coin = "Ethereum"
if "action_log" not in st.session_state:
    st.session_state.action_log = ["Connected to CoinMarketCap Pro API (Top 40 Market Scan)."]
if "simulate_crash" not in st.session_state:
    st.session_state.simulate_crash = False

# --- FETCH LIVE DATA ---
raw_data, api_status = fetch_cmc_listings(API_KEY)
fng_value, fng_label = fetch_fear_and_greed(API_KEY)

assets: list[AssetMetrics] = sorted(
    [analyze_asset(c) for c in raw_data],
    key=lambda x: x["net_score"],
    reverse=True,
)

# --- ZONE 1: TOP BAR (GLOBAL MARKET PULSE) ---
_ = st.title("🔄 SimpliLoop — Autonomous Risk, Yield & Action Engine")

if "error" in api_status:
    _ = st.error(f"CMC API Error: {api_status['error']}. Check your .env file.")
elif assets:
    avg_change = sum(a["pct_24h"] for a in assets) / len(assets)
    if bool(st.session_state.simulate_crash):
        avg_change = -7.4

    top_asset = next(iter(assets))
    pulse_col1, pulse_col2, pulse_col3, pulse_col4 = st.columns(4)
    with pulse_col1:
        regime = "🔴 EXTREME FEAR" if fng_value <= 25 or avg_change < -3.0 else ("🟡 CAUTION" if fng_value < 50 else "🟢 GREED / EARN")
        _ = st.metric("CMC Fear & Greed", f"{fng_value}/100 ({fng_label})", regime)
    with pulse_col2:
        _ = st.metric("Top Radar Pick", f"{top_asset['symbol']} ({top_asset['category']})", f"Net Score: {top_asset['net_score']}")
    with pulse_col3:
        _ = st.metric("Active Loop Position", str(st.session_state.active_coin), f"Avg 24h: {round(avg_change, 2)}%")
    with pulse_col4:
        if st.button("🧪 Simulate Market Drop (Demo)"):
            st.session_state.simulate_crash = not bool(st.session_state.simulate_crash)
            st.rerun()

_ = st.divider()

# --- MAIN 3-COLUMN SINGLE-SCREEN LAYOUT ---
left_col, center_col, right_col = st.columns(3)

# --- ZONE 2: LEFT PANEL (REVENUE RADAR WITH CATEGORY FILTERS) ---
with left_col:
    _ = st.subheader("📡 1. Revenue Radar")
    filter_choice = st.radio(
        "Filter Ecosystem View:",
        ["All Assets", "🏆 Blue Chip", "🚀 Rising Mover", "🛡️ Safe / RWA"],
        horizontal=True,
        label_visibility="collapsed",
    )

    filtered_assets = (
        assets
        if filter_choice == "All Assets"
        else [a for a in assets if a["category"] == filter_choice]
    )

    for item in filtered_assets[:6]:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            _ = c1.markdown(
                f"**{item['name']} ({item['symbol']})** · {item['category']}\n\n"
                f"${item['price']} | MCap: ${item['mcap_b']}B | {item['risk']}"
            )
            if c2.button("Select", key=f"sel_{item['symbol']}"):
                st.session_state.active_coin = item["name"]
                log_list: list[str] = list(st.session_state.action_log)
                log_list.insert(0, f"Switched active loop to {item['name']} ({item['symbol']}) [{item['category']}].")
                st.session_state.action_log = log_list
                st.rerun()

# --- ZONE 3: CENTER STAGE (LOOP SIMULATOR & INSTANT SOLUTIONS) ---
with center_col:
    _ = st.subheader("⚙️ 2. Active Loop & Problem Solver")

    if assets:
        first_asset = next(iter(assets))
        active_name = str(st.session_state.active_coin)
        selected = next((a for a in assets if a["name"] == active_name), first_asset)

        with st.container(border=True):
            _ = st.markdown(f"### Active Asset: **{selected['name']} ({selected['symbol']})**")
            _ = st.caption(f"Role: {selected['category']} · Market Cap: ${selected['mcap_b']}B")
            m1, m2, m3 = st.columns(3)
            _ = m1.metric("Revenue Score", f"{selected['revenue_score']}/100")
            _ = m2.metric("Risk Level", selected["risk"])
            _ = m3.metric("Friction", next(iter(selected["inconvenience"].split()), "Easy"))

        _ = st.markdown("#### 🚨 Immediate Risk & Solution Engine")

# --- ZONE 4: ECOSYSTEM NET SIMPLICITY CHART (ZERO EXTRA API CALLS) ---
if assets:
    st.divider()
    st.subheader("📊 Ecosystem Risk vs. Simplicity Score (Top 10 Live Scan)")
    chart_data = {a["symbol"]: a["net_score"] for a in assets[:10]}
    st.bar_chart(chart_data, color="#2563eb")

# --- ZONE 5: INSTANT SWAP PLAN & FEE ROUTING ENGINE ---
if assets:
    st.divider()
    st.subheader("💱 Instant Swap Plan & Fee Routing Engine")

    first_asset = next(iter(assets))
    active_name = str(st.session_state.active_coin)
    current_asset = next((a for a in assets if a["name"] == active_name), first_asset)

    swap_col1, swap_col2, swap_col3 = st.columns(3)
    with swap_col1:
        trade_usd = st.number_input("Position Size (USD)", min_value=50.0, value=1000.0, step=50.0)
    with swap_col2:
        target_safe = st.selectbox("Target Safe / Hedge Asset", ["USDC", "USDT", "PAXG", "BTC", "ETH"])
    with swap_col3:
        fee_bps = 2  # 0.02% ultra-low partner routing fee (2 bps)
        platform_fee = round(trade_usd * (fee_bps / 10_000), 2)
        net_output = round(trade_usd - platform_fee, 2)
        st.metric(
            "Est. Net Swap Output",
            f"${net_output:,.2f} {target_safe}",
            f"Platform Fee (0.02%): ${platform_fee:.2f}",
        )

    uniswap_url = f"https://uniswap.org{target_safe}"
    st.info(
        f"**Execution Plan:** Rotate **${trade_usd:,.0f}** from **{current_asset['symbol']}** → **{target_safe}** "
        f"via non-custodial DEX Aggregator (0.02% ultra-low SimpliLoop routing fee = **${platform_fee:.2f}**). "
        f"[Open Pre-Filled Swap Route ↗]({uniswap_url})"
    )

