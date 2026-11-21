# 🔄 SimpliLoop — Real-Time Risk, Potential & Instant Solution Engine

**Built for the CoinMarketCap API Hackathon (#BuildwithCMC)**  
**Track:** Markets and Trading Tools

## 💡 What SimpliLoop Does

Crypto traders often see high potential returns without noticing hidden volatility risk or exit friction (thin liquidity). **SimpliLoop** turns multi-dimensional CoinMarketCap data into a single-screen, self-healing loop:

1. **Scan Potential:** Ranks Blue Chips (`BTC`, `ETH`, `BNB`, `SOL`), Rising Market-Cap Movers, and Safe/RWA reserves using a custom **Net Simplicity Score**.
2. **Detect Risk & Inconvenience:** Monitors real-time 24h/7d volatility, liquidity depth (`volume_24h / market_cap`), and macro sentiment via the **CMC Fear & Greed Index**.
3. **Instant 1-Click Solutions:** Whenever a problem appears (e.g., Extreme Fear or an overheated +10% rally), SimpliLoop flags the risk in plain English and offers immediate 1-click rotation or profit-locking actions.

## 🔌 CoinMarketCap API Endpoints Used

1. `GET /v1/cryptocurrency/listings/latest` — Fetches real-time USD prices, market cap, 24h volume, and 24h/7d percentage changes across the top 50 assets.
2. `GET /v2/cryptocurrency/info` — Resolves any pasted smart contract address (`0x...` or Solana) to its CoinMarketCap ID and chain metadata.
3. `GET /v2/cryptocurrency/quotes/latest` — Fetches real-time market quotes for any searched token symbol or smart contract.
4. `GET /v3/fear-and-greed/latest` — Fetches the live CoinMarketCap Fear & Greed Index (`value` and `value_classification`) to drive macro risk alerts.


### Visible Evidence of Real API Call

```python
headers = {"X-CMC_PRO_API_KEY": API_KEY, "Accept": "application/json"}
response = requests.get(
    "https://coinmarketcap.com",
    params={"start": 1, "limit": 50, "convert": "USD"},
    headers=headers,
    timeout=10,
)
```

### Visible Evidence of Real API Call

```python
headers = {"X-CMC_PRO_API_KEY": API_KEY, "Accept": "application/json"}
response = requests.get(
    "https://coinmarketcap.com",
    params={"start": 1, "limit": 40, "convert": "USD"},
    headers=headers,
    timeout=10,
)
```

**Sample Live Response Payload (Sanitized):**

```json
{
  "fear_and_greed": {
    "value": 10,
    "classification": "Extreme fear"
  },
  "sample_asset": {
    "name": "Ethereum",
    "symbol": "ETH",
    "category": "🏆 Blue Chip",
    "price": 1762.51,
    "mcap_b": 215.85,
    "pct_24h": 1.17,
    "revenue_score": 71.6,
    "risk": "🟢 Low",
    "inconvenience": "⚡ Easy (Deep Liquidity)",
    "net_score": 79.6
  }
}
```

## 🛠️ How to Run Locally

1. Clone this repository and install dependencies:

```bash
pip install -r requirements.txt
```

1. Create a `.env` file in the root directory and add your CoinMarketCap API key:

```env
CMC_API_KEY=your_coinmarketcap_api_key
```

1. Launch the single-screen dashboard:

```bash
python -m streamlit run app.py
```

## 📝 API Feedback (What Worked & Where the API Got in the Way)

* **What the API Made Possible:** Combining `/v1/cryptocurrency/listings/latest` with `/v3/fear-and-greed/latest` in a single Python workflow made it effortless to build real-time macro-aware risk triggers and liquidity friction scores without needing multiple data providers.
* **Where the API Got in the Way:** Keyless public endpoints (`/public-api/...`) use different path structures than authenticated Pro endpoints (`/v1/...`), requiring URL switching when moving from prototyping to Startup-tier keys. Additionally, annualized yield/APY metadata for tokenized Real World Assets (RWAs) is not bundled directly inside `/listings/latest`, requiring separate RWA endpoint lookups to compare treasury yields against spot crypto momentum.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

![SimpliLoop Banner](./banner.png)
