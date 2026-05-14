from __future__ import annotations

import time as time_module
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

import feedparser
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import yfinance as yf


APP_NAME = "CoCrypto"
COINGECKO = "https://api.coingecko.com/api/v3"
DEFILLAMA_STABLES = "https://stablecoins.llama.fi/stablecoins"
DEFILLAMA_STABLE_CHARTS = "https://stablecoins.llama.fi/stablecoincharts/all"
DEFAULT_ASSET = "bitcoin"

NEWS_FEEDS = {
    "Crypto — CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Crypto — Cointelegraph": "https://cointelegraph.com/rss",
    "Crypto — Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",
    "Régulation — SEC": "https://www.sec.gov/news/pressreleases.rss",
    "Régulation — ESMA": "https://www.esma.europa.eu/rss.xml",
}
BENCHMARKS = {
    "Or — proxy ETF GLD": "GLD",
    "MSCI ACWI IMI Blockchain Economy Index — proxy ETF BLOK": "BLOK",
}
STABLECOIN_PEG_TICKERS = {
    "USDT": "USDT-USD",
    "USDC": "USDC-USD",
    "DAI": "DAI-USD",
    "TUSD": "TUSD-USD",
    "USDP": "USDP-USD",
    "FDUSD": "FDUSD-USD",
    "PYUSD": "PYUSD-USD",
}


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🟦",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
      --co-bg-1: #060b18;
      --co-bg-2: #0a1428;
      --co-panel: rgba(15, 25, 47, 0.92);
      --co-panel-soft: rgba(15, 25, 47, 0.65);
      --co-border: rgba(56, 189, 248, 0.22);
      --co-border-strong: rgba(56, 189, 248, 0.45);
      --co-blue: #38bdf8;
      --co-blue-2: #2563eb;
      --co-blue-3: #1d4ed8;
      --co-text: #d8e1f1;
      --co-text-strong: #f1f5f9;
      --co-muted: #93a3bd;
      --co-up: #4ade80;
      --co-down: #f87171;
    }
    html, body, [class*="css"], .stApp, .stMarkdown, .stMarkdown p,
    .stMarkdown li, label, .stTextInput label, .stSelectbox label,
    .stMultiSelect label, .stRadio label, .stDateInput label {
      color: var(--co-text) !important;
    }
    h1, h2, h3, h4, h5, h6 { color: var(--co-text-strong) !important; }
    .stApp {
      background:
        radial-gradient(1200px 600px at 0% 0%, #122b56 0, transparent 55%),
        radial-gradient(900px 500px at 100% 0%, #0b274d 0, transparent 50%),
        linear-gradient(180deg, #060b18 0%, #02050d 100%);
    }
    header[data-testid="stHeader"], div[data-testid="stHeader"] {
      background: transparent !important;
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      box-shadow: none !important;
      border-bottom: none !important;
    }
    header[data-testid="stHeader"] * { color: var(--co-text) !important; }
    .stApp > header { background: transparent !important; }
    [data-testid="stToolbar"] { background: transparent !important; }
    [data-testid="stDecoration"] { background: transparent !important; }
    [data-testid="stStatusWidget"] { background: rgba(15, 25, 47, 0.6) !important; border: 1px solid var(--co-border) !important; border-radius: 10px !important; }
    [data-testid="stDataFrameResizable"], [data-testid="stDataFrame"] > div {
      background: transparent !important;
    }
    [data-testid="stDataFrame"] [data-testid="stDataFrameContainer"] {
      background: var(--co-panel) !important;
      border-radius: 14px !important;
    }
    [data-testid="stDataFrame"] canvas { background: transparent !important; }
    [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #050a16 0%, #0b1a32 100%);
      border-right: 1px solid var(--co-border);
    }
    [data-testid="stSidebar"] * { color: var(--co-text) !important; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: min(100%, 1680px); }
    /* Métriques : éviter la troncature « … » sur les libellés et les valeurs (Streamlit / flex) */
    div[data-testid="stMetric"] {
      background: var(--co-panel);
      border: 1px solid var(--co-border);
      border-radius: 16px;
      padding: 0.85rem 0.75rem;
      box-shadow: 0 14px 40px rgba(0, 0, 0, 0.35);
      overflow: visible !important;
      min-width: 0;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
      overflow: visible !important;
      text-overflow: clip !important;
      white-space: normal !important;
      word-break: break-word;
      max-width: none !important;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
      font-size: 0.78rem !important;
      line-height: 1.25 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
      color: var(--co-text-strong) !important;
      font-size: clamp(1.05rem, 1.1vw + 0.85rem, 1.45rem) !important;
      line-height: 1.2 !important;
    }
    div[data-testid="stMetricDelta"] { font-weight: 600; overflow: visible !important; text-overflow: clip !important; }
    [data-testid="column"] > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {
      overflow: visible !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"],
    .stMultiSelect div[data-baseweb="select"], .stDateInput input {
      background: var(--co-panel-soft) !important;
      border: 1px solid var(--co-border) !important;
      color: var(--co-text) !important;
      border-radius: 12px !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: .4rem; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
      background: var(--co-panel-soft);
      border: 1px solid var(--co-border);
      border-radius: 999px;
      color: #cbd5f5 !important;
      padding: .5rem 1.1rem;
      font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
      background: linear-gradient(95deg, var(--co-blue-3) 0%, var(--co-blue) 100%);
      color: #ffffff !important;
      border-color: transparent;
      box-shadow: 0 8px 20px rgba(37, 99, 235, 0.45);
    }
    .stDataFrame, [data-testid="stDataFrame"] {
      background: var(--co-panel) !important;
      border-radius: 14px;
      border: 1px solid var(--co-border);
      padding: 4px;
    }
    .stProgress > div > div > div > div {
      background: linear-gradient(90deg, var(--co-blue-3), var(--co-blue)) !important;
    }
    .co-hero {
      background: linear-gradient(135deg, rgba(29, 78, 216, 0.25) 0%, rgba(15, 25, 47, 0.85) 60%, rgba(15, 25, 47, 0.55) 100%);
      border: 1px solid var(--co-border-strong);
      border-radius: 22px;
      padding: 1.4rem 1.6rem;
      margin-bottom: 1.2rem;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
    }
    .co-hero h1 {
      font-size: 2.2rem;
      letter-spacing: -0.03em;
      margin: 0 0 0.3rem 0;
      background: linear-gradient(90deg, #ffffff 0%, #93c5fd 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .co-hero p { color: var(--co-muted) !important; margin: 0; }
    .co-card {
      background: var(--co-panel);
      border: 1px solid var(--co-border);
      border-radius: 18px;
      padding: 1.1rem 1.3rem;
      margin-bottom: 1rem;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
    }
    .co-card h4 {
      margin: 0 0 0.7rem 0;
      font-size: 1rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: #93c5fd !important;
    }
    .co-kv { display: grid; grid-template-columns: 1fr auto; gap: 0.45rem 1rem; }
    .co-kv .k { color: var(--co-muted); font-size: 0.86rem; }
    .co-kv .v { color: var(--co-text-strong); font-weight: 600; text-align: right; font-size: 0.92rem; }
    .co-badge {
      display: inline-block;
      padding: 0.18rem 0.6rem;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .co-badge.bull { background: rgba(74, 222, 128, 0.18); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.4); }
    .co-badge.bear { background: rgba(248, 113, 113, 0.18); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.4); }
    .co-badge.transition { background: rgba(56, 189, 248, 0.16); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); }
    .co-badge.neutral { background: rgba(148, 163, 184, 0.18); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.4); }
    .co-tag {
      display: inline-block;
      margin: 0.15rem 0.25rem 0.15rem 0;
      padding: 0.15rem 0.55rem;
      background: rgba(37, 99, 235, 0.18);
      color: #bfdbfe;
      border: 1px solid rgba(37, 99, 235, 0.4);
      border-radius: 999px;
      font-size: 0.78rem;
    }
    .co-news {
      background: var(--co-panel);
      border: 1px solid var(--co-border);
      border-radius: 14px;
      padding: 0.9rem 1.1rem;
      margin-bottom: 0.7rem;
    }
    .co-news a { color: #bfdbfe !important; text-decoration: none; font-weight: 700; }
    .co-news .meta { color: var(--co-muted); font-size: 0.82rem; margin-top: 0.15rem; }
    div[data-testid="stExpander"] {
      background: var(--co-panel-soft);
      border: 1px solid var(--co-border);
      border-radius: 12px;
    }
    div[data-testid="stExpander"] summary { color: #bfdbfe !important; }
    .stAlert { border-radius: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_money(value: float | int | None, decimals: int | None = None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    value = float(value)
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    if abs_value >= 1_000_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000_000:.{decimals if decimals is not None else 2}f} T"
    if abs_value >= 1_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000:.{decimals if decimals is not None else 2}f} Md"
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.{decimals if decimals is not None else 2}f} M"
    if abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.{decimals if decimals is not None else 2}f} k"
    if decimals is None:
        decimals = 4 if abs_value < 10 else 2
    return f"{sign}${abs_value:,.{decimals}f}"


def format_quantity(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} Md"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f} M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f} k"
    return f"{value:,.2f}"


def format_pct(value: float | int | None, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):+.{decimals}f} %"


def to_unix(day: date, end_of_day: bool = False) -> int:
    clock = time(23, 59, 59) if end_of_day else time(0, 0, 0)
    return int(datetime.combine(day, clock, tzinfo=timezone.utc).timestamp())


def request_json(url: str, params: dict[str, Any] | None = None, retries: int = 3) -> Any:
    headers = {
        "accept": "application/json",
        "user-agent": "CoCrypto/0.2 local streamlit app",
    }
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=25)
            if response.status_code == 429:
                time_module.sleep(1.5 * (attempt + 1))
                last_exc = requests.HTTPError("429 Too Many Requests")
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_exc = exc
            time_module.sleep(0.6 * (attempt + 1))
    raise last_exc if last_exc else RuntimeError("Requête impossible")


@st.cache_data(ttl=90, show_spinner=False)
def get_markets(vs_currency: str = "usd", per_page: int = 250) -> pd.DataFrame:
    rows = request_json(
        f"{COINGECKO}/coins/markets",
        {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d,30d,1y",
        },
    )
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def get_global() -> dict[str, Any]:
    return request_json(f"{COINGECKO}/global").get("data", {})


@st.cache_data(ttl=600, show_spinner=False)
def get_categories() -> pd.DataFrame:
    rows = request_json(f"{COINGECKO}/coins/categories")
    return pd.DataFrame(rows)


@st.cache_data(ttl=600, show_spinner=False)
def get_coin_details(coin_id: str) -> dict[str, Any]:
    return request_json(
        f"{COINGECKO}/coins/{coin_id}",
        {
            "localization": "false",
            "tickers": "true",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true",
            "sparkline": "false",
        },
    )


@st.cache_data(ttl=300, show_spinner=False)
def get_coin_history(coin_id: str, start: date, end: date) -> pd.DataFrame:
    data = request_json(
        f"{COINGECKO}/coins/{coin_id}/market_chart/range",
        {
            "vs_currency": "usd",
            "from": to_unix(start),
            "to": to_unix(end, end_of_day=True),
        },
    )
    prices = pd.DataFrame(data.get("prices", []), columns=["timestamp", "price"])
    market_caps = pd.DataFrame(data.get("market_caps", []), columns=["timestamp", "market_cap"])
    volumes = pd.DataFrame(data.get("total_volumes", []), columns=["timestamp", "volume"])
    if prices.empty:
        return pd.DataFrame(columns=["date", "price", "market_cap", "volume"])
    frame = prices.merge(market_caps, on="timestamp", how="left").merge(volumes, on="timestamp", how="left")
    frame["date"] = pd.to_datetime(frame["timestamp"], unit="ms").dt.tz_localize("UTC")
    return frame.drop(columns=["timestamp"]).sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=900, show_spinner=False)
def get_benchmark(symbol: str, start: date, end: date) -> pd.DataFrame:
    data = yf.download(symbol, start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(), progress=False, auto_adjust=True)
    if data.empty:
        return pd.DataFrame(columns=["date", "benchmark"])
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return pd.DataFrame({"date": pd.to_datetime(close.index).tz_localize(None), "benchmark": close.values})


@st.cache_data(ttl=900, show_spinner=False)
def get_news() -> pd.DataFrame:
    articles: list[dict[str, Any]] = []
    for source, url in NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:12]:
                published = entry.get("published") or entry.get("updated") or ""
                articles.append(
                    {
                        "source": source,
                        "title": entry.get("title", "Sans titre"),
                        "published": published,
                        "summary": entry.get("summary", ""),
                        "link": entry.get("link", ""),
                    }
                )
        except Exception:
            continue
    return pd.DataFrame(articles)


@st.cache_data(ttl=900, show_spinner=False)
def get_stablecoins_defillama() -> pd.DataFrame:
    try:
        data = request_json(DEFILLAMA_STABLES, {"includePrices": "true"})
    except Exception:
        return pd.DataFrame()
    coins = data.get("peggedAssets") or []
    rows: list[dict[str, Any]] = []
    for c in coins:
        circ = c.get("circulating") or {}
        if isinstance(circ, dict):
            circ_usd = circ.get("peggedUSD")
            if circ_usd is None:
                circ_usd = sum(v for v in circ.values() if isinstance(v, (int, float)))
        else:
            circ_usd = float(circ) if isinstance(circ, (int, float)) else None
        chains = c.get("chains") or []
        rows.append(
            {
                "Symbole": c.get("symbol"),
                "Nom": c.get("name"),
                "Type de peg": c.get("pegType"),
                "Mécanisme": c.get("pegMechanism"),
                "Cours (USD)": c.get("price"),
                "Circulation (USD)": circ_usd,
                "Chaînes principales": ", ".join(chains[:5]) if chains else "n/a",
                "Nombre de chaînes": len(chains),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Circulation (USD)", ascending=False, na_position="last").reset_index(drop=True)
    return df


STABLECOIN_FALLBACK_IDS: dict[str, str] = {
    "USDT": "tether",
    "USDC": "usd-coin",
    "DAI": "dai",
    "USDE": "ethena-usde",
    "FDUSD": "first-digital-usd",
    "PYUSD": "paypal-usd",
    "TUSD": "true-usd",
    "USDP": "paxos-standard",
    "USDS": "usds",
    "GUSD": "gemini-dollar",
    "FRAX": "frax",
    "BUSD": "binance-usd",
    "LUSD": "liquity-usd",
    "USDD": "usdd",
    "MIM": "magic-internet-money",
    "CRVUSD": "crvusd",
    "GHO": "gho",
    "EURS": "stasis-eurs",
    "EURT": "tether-eurt",
    "RLUSD": "ripple-usd",
    "PYUSDT": "paypal-usd",
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_stablecoin_id_map() -> dict[str, str]:
    """Mapping symbole majuscule -> identifiant CoinGecko.

    Combine la liste vivante CoinGecko (catégorie « stablecoins ») et un repli statique pour
    rester opérationnel même en cas de 429 ou de panne réseau.
    """
    mapping: dict[str, str] = dict(STABLECOIN_FALLBACK_IDS)
    try:
        rows = request_json(
            f"{COINGECKO}/coins/markets",
            {
                "vs_currency": "usd",
                "category": "stablecoins",
                "order": "market_cap_desc",
                "per_page": 100,
                "page": 1,
                "sparkline": "false",
            },
        )
    except Exception:
        return mapping
    for row in rows or []:
        sym = (row.get("symbol") or "").upper()
        cg_id = row.get("id")
        if sym and cg_id:
            mapping[sym] = cg_id
    return mapping


@st.cache_data(ttl=1800, show_spinner=False)
def get_stable_marketcap_sparkline(coin_id: str, start: date, end: date, points: int = 60) -> list[float]:
    """Capitalisation historique simplifiée (sparkline) pour un stablecoin donné."""
    try:
        hist = get_coin_history(coin_id, start, end)
    except Exception:
        return []
    if hist.empty or "market_cap" not in hist.columns:
        return []
    series = hist.dropna(subset=["market_cap"]).sort_values("date")["market_cap"].tolist()
    if not series:
        return []
    if len(series) <= points:
        return [float(v) for v in series]
    step = max(1, len(series) // points)
    return [float(v) for v in series[::step]]


@st.cache_data(ttl=1800, show_spinner=False)
def get_stable_peg_history(days: int = 45) -> pd.DataFrame:
    end = date.today()
    start = end - timedelta(days=days)
    rows: list[dict[str, Any]] = []
    for sym, ticker in STABLECOIN_PEG_TICKERS.items():
        try:
            data = yf.download(ticker, start=start.isoformat(), end=end.isoformat(), progress=False, auto_adjust=True)
            if data.empty:
                continue
            close = data["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            for ts, value in close.items():
                if value is None or pd.isna(value):
                    continue
                rows.append({"Stablecoin": sym, "Date": pd.to_datetime(ts), "Prix (USD)": float(value)})
        except Exception:
            continue
    return pd.DataFrame(rows)


@st.cache_data(ttl=1800, show_spinner=False)
def get_stable_total_history(days: int = 365) -> pd.DataFrame:
    try:
        data = request_json(DEFILLAMA_STABLE_CHARTS)
    except Exception:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for point in data or []:
        ts = point.get("date")
        circ = point.get("totalCirculatingUSD") or {}
        if isinstance(circ, dict):
            value = circ.get("peggedUSD") or sum(v for v in circ.values() if isinstance(v, (int, float)))
        else:
            value = float(circ) if isinstance(circ, (int, float)) else None
        if ts and value:
            rows.append({"Date": pd.to_datetime(int(ts), unit="s"), "Capitalisation totale (USD)": float(value)})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(days=days)
    return df[df["Date"] >= cutoff].reset_index(drop=True)


def normalize_series(df: pd.DataFrame, value_col: str, name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "performance", "Série"])
    clean = df[["date", value_col]].dropna().copy()
    if clean.empty or clean[value_col].iloc[0] == 0:
        return pd.DataFrame(columns=["date", "performance", "Série"])
    clean["performance"] = clean[value_col] / clean[value_col].iloc[0] * 100
    clean["Série"] = name
    return clean[["date", "performance", "Série"]].rename(columns={"date": "Date"})


def cycle_model(history: pd.DataFrame) -> tuple[str, str, float | None, float | None, int, int]:
    if history.empty or len(history) < 30:
        return "Indéterminé", "Historique insuffisant pour calculer un cycle.", None, None, 0, 0
    daily = history.set_index("date")["price"].resample("1D").last().dropna()
    if len(daily) < 30:
        return "Indéterminé", "Historique journalier insuffisant.", None, None, 0, 0
    sma_window = min(200, max(30, len(daily) // 2))
    momentum_window = min(90, max(14, len(daily) // 3))
    latest = float(daily.iloc[-1])
    sma_value = daily.rolling(sma_window).mean().iloc[-1]
    sma = float(sma_value) if not pd.isna(sma_value) else None
    past_value = daily.iloc[-momentum_window]
    momentum: float | None = None
    if past_value and not pd.isna(past_value):
        momentum = (latest / float(past_value) - 1) * 100
    if sma is None or momentum is None:
        return "Indéterminé", "Données incomplètes pour le calcul.", momentum, sma, sma_window, momentum_window
    if latest > sma and momentum > 0:
        return "Bull", f"Cours au-dessus de la moyenne mobile {sma_window} j et momentum {momentum_window} j positif.", momentum, sma, sma_window, momentum_window
    if latest < sma and momentum < 0:
        return "Bear", f"Cours sous la moyenne mobile {sma_window} j et momentum {momentum_window} j négatif.", momentum, sma, sma_window, momentum_window
    return "Transition", f"Signal mixte entre tendance longue ({sma_window} j) et momentum court ({momentum_window} j).", momentum, sma, sma_window, momentum_window


def supply_progress(row: pd.Series) -> tuple[float | None, str]:
    circulating = row.get("circulating_supply")
    maximum = row.get("max_supply")
    total = row.get("total_supply")
    denominator = maximum if maximum and not pd.isna(maximum) else total
    if not denominator or pd.isna(denominator) or not circulating or pd.isna(circulating):
        return None, "Stock total ou plafond d'émission indisponible chez le fournisseur."
    ratio = min(max(float(circulating) / float(denominator), 0), 1)
    label = "miné / émis vs plafond" if maximum else "en circulation vs stock total déclaré"
    return ratio, label


def article_matches(row: pd.Series, query: str) -> bool:
    if not query:
        return True
    blob = f"{row.get('title', '')} {row.get('summary', '')} {row.get('source', '')}".lower()
    return query.lower() in blob


PLOTLY_CONFIG: dict[str, Any] = {
    "displaylogo": False,
    "displayModeBar": "hover",
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
}


def apply_plotly_style(
    fig: go.Figure,
    *,
    title: str | None = None,
    y_title: str | None = None,
    x_title: str | None = None,
    legend_below: bool = True,
) -> go.Figure:
    bottom_margin = 110 if legend_below else 60
    layout: dict[str, Any] = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, sans-serif", size=13, color="#dbe3f4"),
        margin=dict(t=90, l=60, r=30, b=bottom_margin),
        hoverlabel=dict(bgcolor="#0f172a", bordercolor="#38bdf8", font=dict(color="#f1f5f9")),
        legend=dict(
            bgcolor="rgba(15,23,42,0.55)",
            bordercolor="rgba(56,189,248,0.3)",
            borderwidth=1,
            font=dict(color="#e2e8f0", size=11),
            orientation="h",
            yanchor="top",
            y=-0.22 if legend_below else 1.08,
            xanchor="center",
            x=0.5,
        ),
    )
    if title:
        layout["title"] = dict(
            text=f"<b>{title}</b>",
            x=0.0,
            xanchor="left",
            y=0.97,
            yanchor="top",
            pad=dict(l=10, t=10),
            font=dict(size=17, color="#f1f5f9"),
        )
    fig.update_layout(**layout)
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.10)", zerolinecolor="rgba(148,163,184,0.18)", title_font=dict(color="#cbd5e1", size=13), tickfont=dict(color="#cbd5e1"))
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.10)", zerolinecolor="rgba(148,163,184,0.18)", title_font=dict(color="#cbd5e1", size=13), tickfont=dict(color="#cbd5e1"))
    if y_title:
        fig.update_yaxes(title=y_title)
    if x_title:
        fig.update_xaxes(title=x_title)
    return fig


def render_kv_card(title: str, items: list[tuple[str, str]]) -> None:
    rows = "".join(
        f'<div class="k">{k}</div><div class="v">{v}</div>' for k, v in items
    )
    st.markdown(
        f'<div class="co-card"><h4>{title}</h4><div class="co-kv">{rows}</div></div>',
        unsafe_allow_html=True,
    )


def render_tag_card(title: str, tags: list[str], extra: str | None = None) -> None:
    chips = "".join(f'<span class="co-tag">{t}</span>' for t in tags) if tags else '<span class="co-tag">n/a</span>'
    extra_html = f'<p style="color: var(--co-muted); margin-top: 0.5rem; font-size: 0.85rem;">{extra}</p>' if extra else ""
    st.markdown(
        f'<div class="co-card"><h4>{title}</h4><div>{chips}</div>{extra_html}</div>',
        unsafe_allow_html=True,
    )


def _strip_html(value: Any) -> str:
    if value is None:
        return "n/a"
    text = str(value)
    if not text:
        return "n/a"
    import re
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "n/a"


def build_crypto_pdf_report(
    asset_name: str,
    asset_symbol: str,
    market_row: pd.Series,
    details: dict[str, Any],
    history: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> bytes:
    from io import BytesIO

    from reportlab.lib import colors as rl_colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image as RLImage,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    NAVY = HexColor("#0a1428")
    DARK_BLUE = HexColor("#1d4ed8")
    BLUE = HexColor("#2563eb")
    BLUE_LIGHT = HexColor("#38bdf8")
    INK = HexColor("#0f172a")
    MUTED = HexColor("#64748b")
    BORDER = HexColor("#cbd5e1")
    PANEL = HexColor("#f1f5f9")
    WHITE = HexColor("#ffffff")
    SUCCESS = HexColor("#16a34a")
    DANGER = HexColor("#dc2626")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
        title=f"Rapport CoCrypto — {asset_name} ({asset_symbol})",
        author="CoCrypto",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=26,
        textColor=NAVY,
        leading=30,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=MUTED,
        leading=14,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=BLUE,
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=INK,
        leading=14,
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        textColor=MUTED,
        leading=11,
    )

    market_data = details.get("market_data") or {}

    def _usd_field(key: str) -> Any:
        block = market_data.get(key) or {}
        return block.get("usd") if isinstance(block, dict) else None

    elements: list[Any] = []

    header_table = Table(
        [
            [
                Paragraph("<b>CoCrypto</b>", ParagraphStyle("Brand", parent=body_style, textColor=WHITE, fontSize=14, fontName="Helvetica-Bold")),
                Paragraph(
                    f"Rapport généré le <b>{date.today().strftime('%d/%m/%Y')}</b><br/>"
                    f"Période d'analyse : <b>{start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}</b>",
                    ParagraphStyle("Meta", parent=body_style, textColor=WHITE, fontSize=9, alignment=2),
                ),
            ]
        ],
        colWidths=[8 * cm, 9.5 * cm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 0.6 * cm))

    elements.append(Paragraph(f"{asset_name} <font color='#2563eb'>({asset_symbol})</font>", title_style))
    rank = market_row.get("market_cap_rank")
    rank_str = f"#{int(rank)}" if rank is not None and not pd.isna(rank) else "n/a"
    cats = details.get("categories") or []
    cats_str = ", ".join([c for c in cats[:5] if c]) if cats else "n/a"
    elements.append(
        Paragraph(
            f"Rang capi : <b>{rank_str}</b> • Pays d'origine : <b>{details.get('country_origin') or 'n/a'}</b> • "
            f"Date de genèse : <b>{details.get('genesis_date') or 'n/a'}</b><br/>"
            f"Catégories : <b>{cats_str}</b>",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 0.4 * cm))

    # Indicateurs clés
    elements.append(Paragraph("Indicateurs clés", h2_style))
    perf_24h = market_row.get("price_change_percentage_24h")
    perf_7d = market_row.get("price_change_percentage_7d_in_currency")
    perf_30d = market_row.get("price_change_percentage_30d_in_currency")
    perf_1y = market_row.get("price_change_percentage_1y_in_currency")
    kpi_rows = [
        ["Métrique", "Valeur"],
        ["Cours (USD)", format_money(market_row.get("current_price"))],
        ["Capitalisation (USD)", format_money(market_row.get("market_cap"))],
        ["Volume 24 h (USD)", format_money(market_row.get("total_volume"))],
        ["Plus haut 24 h (USD)", format_money(_usd_field("high_24h"))],
        ["Plus bas 24 h (USD)", format_money(_usd_field("low_24h"))],
        ["FDV — Fully Diluted Valuation (USD)", format_money(_usd_field("fully_diluted_valuation"))],
        ["ATH — All-Time High (USD)", format_money(_usd_field("ath"))],
        ["ATL — All-Time Low (USD)", format_money(_usd_field("atl"))],
        ["Performance 24 h (%)", format_pct(perf_24h)],
        ["Performance 7 j (%)", format_pct(perf_7d)],
        ["Performance 30 j (%)", format_pct(perf_30d)],
        ["Performance 1 an (%)", format_pct(perf_1y)],
    ]
    kpi_table = Table(kpi_rows, colWidths=[9 * cm, 8.5 * cm])
    kpi_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
            ("TOPPADDING", (0, 0), (-1, 0), 7),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9.5),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("TEXTCOLOR", (0, 1), (-1, -1), INK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PANEL]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )
    for idx, perf in enumerate([perf_24h, perf_7d, perf_30d, perf_1y], start=9):
        if perf is None or pd.isna(perf):
            continue
        color = SUCCESS if perf >= 0 else DANGER
        kpi_style.add("TEXTCOLOR", (1, idx), (1, idx), color)
        kpi_style.add("FONTNAME", (1, idx), (1, idx), "Helvetica-Bold")
    kpi_table.setStyle(kpi_style)
    elements.append(kpi_table)

    # Émission / minage
    elements.append(Paragraph("Émission, minage et offre", h2_style))
    ratio, ratio_label = supply_progress(market_row)
    if ratio is not None:
        ratio_text = f"<b>{ratio * 100:.2f} %</b> {ratio_label}"
    else:
        ratio_text = ratio_label
    elements.append(Paragraph(ratio_text, body_style))
    elements.append(Spacer(1, 0.2 * cm))
    supply_rows = [
        ["Champ", "Valeur"],
        ["Stock circulant (quantité)", format_quantity(market_row.get("circulating_supply"))],
        ["Stock total déclaré (quantité)", format_quantity(market_row.get("total_supply"))],
        ["Stock maximum (quantité)", format_quantity(market_row.get("max_supply"))],
        ["Algorithme de hachage", str(details.get("hashing_algorithm") or "n/a")],
        ["Temps de bloc moyen (min)", str(details.get("block_time_in_minutes") or "n/a")],
        ["Date de genèse", str(details.get("genesis_date") or "n/a")],
    ]
    supply_table = Table(supply_rows, colWidths=[9 * cm, 8.5 * cm])
    supply_table.setStyle(kpi_style)
    elements.append(supply_table)

    elements.append(PageBreak())

    # Chart history via matplotlib
    if not history.empty:
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8.6, 3.7), facecolor="#ffffff")
            ax.set_facecolor("#f8fafc")
            ax.plot(history["date"], history["price"], color="#1d4ed8", linewidth=1.6)
            ax.fill_between(history["date"], history["price"], color="#2563eb", alpha=0.10)
            ax.set_title(f"Cours {asset_symbol} (USD) — du {start_date:%d/%m/%Y} au {end_date:%d/%m/%Y}", color="#0f172a", fontsize=11, fontweight="bold", loc="left")
            ax.tick_params(colors="#475569", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#cbd5e1")
            ax.grid(color="#e2e8f0", alpha=0.7, linewidth=0.6)
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
            ax.set_xlabel("Date", color="#475569", fontsize=9)
            ax.set_ylabel("Cours (USD)", color="#475569", fontsize=9)
            fig.tight_layout()
            chart_buf = BytesIO()
            fig.savefig(chart_buf, format="png", dpi=160, bbox_inches="tight", facecolor="#ffffff")
            plt.close(fig)
            chart_buf.seek(0)
            elements.append(Paragraph("Historique du cours sur la période", h2_style))
            elements.append(RLImage(chart_buf, width=17.5 * cm, height=7.4 * cm))
            elements.append(Spacer(1, 0.2 * cm))
            stats = history["price"].describe()
            stats_rows = [
                ["Indicateur", "Valeur (USD)"],
                ["Cours d'ouverture (1er point)", format_money(history["price"].iloc[0])],
                ["Cours de clôture (dernier point)", format_money(history["price"].iloc[-1])],
                ["Plus haut sur la période", format_money(stats.get("max"))],
                ["Plus bas sur la période", format_money(stats.get("min"))],
                ["Moyenne arithmétique", format_money(stats.get("mean"))],
                ["Médiane", format_money(history["price"].median())],
                ["Écart-type (volatilité absolue)", format_money(stats.get("std"))],
                ["Nombre d'observations", f"{int(stats.get('count') or 0):,}".replace(",", " ")],
            ]
            stats_table = Table(stats_rows, colWidths=[9 * cm, 8.5 * cm])
            stats_table.setStyle(kpi_style)
            elements.append(stats_table)
        except Exception as exc:
            elements.append(Paragraph(f"Graphique indisponible ({exc}).", caption_style))

    elements.append(PageBreak())

    # Communauté & développement
    elements.append(Paragraph("Communauté et développement", h2_style))
    community = details.get("community_data") or {}
    developer = details.get("developer_data") or {}
    cd_rows = [
        ["Champ", "Valeur"],
        ["Twitter — abonnés", format_quantity(community.get("twitter_followers"))],
        ["Reddit — abonnés", format_quantity(community.get("reddit_subscribers"))],
        ["Telegram — utilisateurs", format_quantity(community.get("telegram_channel_user_count"))],
        ["GitHub — stars", format_quantity(developer.get("stars"))],
        ["GitHub — forks", format_quantity(developer.get("forks"))],
        ["GitHub — commits 4 sem.", format_quantity(developer.get("commit_count_4_weeks"))],
        ["GitHub — contributeurs", format_quantity(developer.get("pull_request_contributors"))],
    ]
    cd_table = Table(cd_rows, colWidths=[9 * cm, 8.5 * cm])
    cd_table.setStyle(kpi_style)
    elements.append(cd_table)

    # Liens utiles
    elements.append(Paragraph("Liens utiles", h2_style))
    links = details.get("links") or {}
    homepage = (links.get("homepage") or [""])[0]
    twitter = links.get("twitter_screen_name")
    subreddit = links.get("subreddit_url")
    github_repos = (links.get("repos_url", {}) or {}).get("github", [])
    link_rows = [
        ["Type", "URL / Compte"],
        ["Site officiel", homepage or "n/a"],
        ["Twitter / X", f"https://x.com/{twitter}" if twitter else "n/a"],
        ["Subreddit", subreddit or "n/a"],
        ["Repos GitHub principaux", "\n".join(github_repos[:3]) if github_repos else "n/a"],
    ]
    link_table = Table(link_rows, colWidths=[5 * cm, 12.5 * cm])
    link_table.setStyle(kpi_style)
    elements.append(link_table)

    # Description
    description_block = details.get("description") or {}
    description_en = _strip_html(description_block.get("en"))
    if description_en and description_en != "n/a":
        if len(description_en) > 1800:
            description_en = description_en[:1800].rsplit(" ", 1)[0] + "…"
        elements.append(Paragraph("Description (source : CoinGecko)", h2_style))
        elements.append(Paragraph(description_en, body_style))

    elements.append(Spacer(1, 0.4 * cm))
    elements.append(
        Paragraph(
            "<b>Sources</b> : CoinGecko (cours, capitalisation, volumes, métadonnées), DefiLlama (stablecoins), Yahoo Finance (benchmarks et peg). "
            "Toutes les valeurs sont indicatives et fournies sans garantie d'exhaustivité ni d'exactitude.<br/>"
            f"Rapport généré automatiquement par CoCrypto le {datetime.now().strftime('%d/%m/%Y à %H:%M')}.",
            caption_style,
        )
    )

    def _draw_footer(canvas, doc_ref):
        canvas.saveState()
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(1.8 * cm, 1 * cm, f"CoCrypto • {asset_name} ({asset_symbol})")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1 * cm, f"Page {doc_ref.page}")
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.4)
        canvas.line(1.8 * cm, 1.3 * cm, A4[0] - 1.8 * cm, 1.3 * cm)
        canvas.restoreState()

    doc.build(elements, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    buf.seek(0)
    return buf.getvalue()


try:
    markets = get_markets()
    global_data = get_global()
except Exception as exc:
    st.error(
        f"Impossible de charger les données CoinGecko pour le moment ({exc}). "
        "CoinGecko applique un plafond gratuit, réessaie dans quelques secondes."
    )
    st.stop()


if markets.empty:
    st.error("Aucune donnée de marché n'a été retournée.")
    st.stop()


st.sidebar.markdown("### Paramètres")
st.sidebar.caption("Réglages d'analyse et benchmarks.")

today = date.today()
date_range = st.sidebar.date_input(
    "Période d'analyse",
    value=(today - timedelta(days=365), today),
    min_value=date(2013, 1, 1),
    max_value=today,
    help="Sélectionne une date de début et de fin pour les graphes historiques, comparaisons, cycles et flux.",
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = today - timedelta(days=365)
    end_date = today
if start_date >= end_date:
    st.sidebar.warning("La date de début doit être antérieure à la date de fin.")
    start_date = end_date - timedelta(days=30)

benchmark_name = st.sidebar.radio(
    "Benchmark de comparaison",
    list(BENCHMARKS.keys()),
    help=(
        "Or via le proxy GLD (ETF physique adossé à l'or). "
        "Indice MSCI ACWI IMI Blockchain Economy via le proxy BLOK (ETF thématique blockchain), "
        "car l'indice MSCI exact est sous licence."
    ),
)

st.sidebar.markdown("---")
st.sidebar.caption("Sources : CoinGecko, Yahoo Finance, DefiLlama, RSS publics. Toutes les valeurs sont indicatives.")

st.markdown(
    f"""
    <div class="co-hero">
      <h1>{APP_NAME}</h1>
      <p>Agrégateur orienté <strong>analyse</strong> et <strong>stablecoins</strong> : cours, capitalisation, volumes,
      pegs multi-sources, comparaisons benchmarkées, cycles, flux, actualités et réglementation.
      Les données sont croisées (CoinGecko, DefiLlama, Yahoo Finance, RSS) — pas une simple copie d'un agrégateur unique.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

header_cols = st.columns([3, 2, 1])
with header_cols[0]:
    search = st.text_input(
        "Rechercher une crypto",
        placeholder="Tape un nom, un symbole ou un identifiant : bitcoin, ETH, solana…",
        help="Filtre la liste déroulante par nom, symbole ou identifiant CoinGecko.",
    )
with header_cols[1]:
    filtered_assets = markets.copy()
    if search:
        mask = (
            filtered_assets["name"].str.contains(search, case=False, na=False)
            | filtered_assets["symbol"].str.contains(search, case=False, na=False)
            | filtered_assets["id"].str.contains(search, case=False, na=False)
        )
        filtered_assets = filtered_assets[mask]
    asset_options = filtered_assets["id"].tolist() or markets["id"].tolist()
    default_index = asset_options.index(DEFAULT_ASSET) if DEFAULT_ASSET in asset_options else 0
    selected_id = st.selectbox(
        "Crypto suivie",
        asset_options,
        index=default_index,
        format_func=lambda coin_id: f"{markets.loc[markets['id'] == coin_id, 'name'].iloc[0]} ({markets.loc[markets['id'] == coin_id, 'symbol'].iloc[0].upper()})",
        help="Cette crypto alimente la fiche détaillée, les flux et cycles, et sert d'actif principal en comparaison.",
    )
with header_cols[2]:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.caption(f"{len(asset_options)} résultats")

selected_row = markets.loc[markets["id"] == selected_id].iloc[0]
asset_name = selected_row["name"]
asset_symbol = selected_row["symbol"].upper()

top_cols = st.columns([1.35, 1.12, 1.12, 0.62, 0.79])
top_cols[0].metric(
    asset_symbol,
    format_money(selected_row.get("current_price"), decimals=2),
    format_pct(selected_row.get("price_change_percentage_24h")),
    help=f"{asset_name} ({asset_symbol}) — cours spot agrégé multi-exchanges (USD). Variation = perf 24 h en %.",
)
top_cols[1].metric(
    "Capi (USD)",
    format_money(selected_row.get("market_cap")),
    format_pct(selected_row.get("price_change_percentage_7d_in_currency")),
    help="Capitalisation = cours × stock circulant. Variation affichée = perf 7 j en %.",
)
top_cols[2].metric(
    "Vol. 24 h (USD)",
    format_money(selected_row.get("total_volume")),
    format_pct(selected_row.get("price_change_percentage_1h_in_currency")),
    help="Volume d'échange agrégé sur 24 h en USD. Variation = perf 1 h en %.",
)
top_cols[3].metric(
    "Rang",
    f"#{int(selected_row.get('market_cap_rank'))}" if not pd.isna(selected_row.get("market_cap_rank")) else "n/a",
    help="Rang capitalisation parmi les actifs suivis par CoinGecko.",
)
top_cols[4].metric(
    "Dom. BTC",
    format_pct(global_data.get("market_cap_percentage", {}).get("btc"), decimals=2),
    help="Dominance : part de Bitcoin dans la capitalisation totale du marché crypto.",
)

_df_strip = get_stablecoins_defillama()
_strip_total_mcap = float(global_data.get("total_market_cap", {}).get("usd") or 0)
strip_cols = st.columns(4)
if not _df_strip.empty:
    _st_sum = float(_df_strip["Circulation (USD)"].sum())
    _share_mkt = (_st_sum / _strip_total_mcap * 100) if _strip_total_mcap > 0 else float("nan")
    _usdt_share = float("nan")
    if "USDT" in _df_strip["Symbole"].values:
        _usdt_share = float(
            _df_strip.loc[_df_strip["Symbole"] == "USDT", "Circulation (USD)"].iloc[0]
        ) / max(_st_sum, 1) * 100
    strip_cols[0].metric(
        "Stables — capi totale",
        format_money(_st_sum),
        help="Somme DefiLlama des stablecoins suivis (USD).",
    )
    strip_cols[1].metric(
        "Stables / marché crypto",
        format_pct(_share_mkt) if pd.notna(_share_mkt) else "n/a",
        help="Capitalisation stablecoins ÷ capitalisation totale crypto (CoinGecko global).",
    )
    strip_cols[2].metric(
        "USDT / stables",
        format_pct(_usdt_share) if pd.notna(_usdt_share) else "n/a",
        help="Part de Tether dans la capitalisation stablecoins DefiLlama.",
    )
    _peg_df = get_stable_peg_history(days=7)
    if not _peg_df.empty:
        _last = _peg_df.sort_values("Date").groupby("Stablecoin").tail(1)
        _dev_pb = ((_last["Prix (USD)"] - 1.0).abs() * 10_000).max()
        strip_cols[3].metric(
            "Peg — écart max (7 j)",
            f"{float(_dev_pb):.1f} pb",
            help="Plus grand écart absolu au peg 1 USD (points de base) sur les stablecoins suivis via Yahoo, 7 derniers jours.",
        )
    else:
        strip_cols[3].metric("Peg — écart max (7 j)", "n/a", help="Yahoo Finance indisponible.")
else:
    strip_cols[0].metric("Stables — capi totale", "n/a", help="DefiLlama indisponible.")
    strip_cols[1].metric("Stables / marché crypto", "n/a", help="—")
    strip_cols[2].metric("USDT / stables", "n/a", help="—")
    strip_cols[3].metric("Peg — écart max (7 j)", "n/a", help="—")
st.caption("Bandeau stablecoins : vue synthétique DefiLlama + stress de peg court terme (Yahoo). Détail dans l'onglet *Stablecoins*.")

tab_market, tab_stables, tab_asset, tab_compare, tab_flows, tab_news, tab_method = st.tabs(
    [
        "Marché",
        "Stablecoins",
        "Fiche crypto",
        "Comparaisons",
        "Flux & cycles",
        "Actualités & Réglementation",
        "Méthode & limites",
    ]
)

with tab_market:
    st.subheader("Vue d'ensemble du marché")
    with st.expander("ℹ️ Comment lire ces indicateurs", expanded=False):
        st.markdown(
            "- **Capitalisation globale** = somme des capitalisations des cryptos suivies, en USD.\n"
            "- **Volume global 24 h** = somme des volumes d'échange agrégés sur 24 h, en USD.\n"
            "- **Cryptos suivies** = nombre d'actifs référencés par CoinGecko.\n"
            "- Le **tableau** liste les actifs triés par capitalisation, avec toutes les colonnes utiles.\n"
            "- La **cartographie** sous le tableau est paramétrable : critère de classement, secteur, top N."
        )

    market_kpis = st.columns(3)
    market_kpis[0].metric(
        "Capitalisation crypto globale (USD)",
        format_money(global_data.get("total_market_cap", {}).get("usd")),
        help="Somme des capitalisations en dollars de l'ensemble des cryptos suivies par CoinGecko.",
    )
    market_kpis[1].metric(
        "Volume global 24 h (USD)",
        format_money(global_data.get("total_volume", {}).get("usd")),
        help="Volume agrégé d'échange sur 24 h en dollars, toutes cryptos confondues.",
    )
    market_kpis[2].metric(
        "Cryptos suivies (quantité)",
        f"{global_data.get('active_cryptocurrencies', 'n/a'):,}".replace(",", " ") if isinstance(global_data.get('active_cryptocurrencies'), int) else "n/a",
        help="Nombre d'actifs actifs référencés par la source.",
    )

    st.markdown("#### Tableau marché")
    st.caption("Tri par capitalisation décroissante. Toutes les valeurs sont en dollars US, sauf les pourcentages et les quantités explicitement notés.")
    table = markets[
        [
            "market_cap_rank",
            "name",
            "symbol",
            "current_price",
            "market_cap",
            "total_volume",
            "price_change_percentage_24h",
            "price_change_percentage_7d_in_currency",
            "circulating_supply",
            "max_supply",
        ]
    ].copy()
    table["symbol"] = table["symbol"].str.upper()
    table["market_cap_rank"] = table["market_cap_rank"].astype("Int64")
    table["pct_mined"] = (
        table["circulating_supply"] / table["max_supply"] * 100
    ).where(table["max_supply"].notna() & (table["max_supply"] > 0))
    table["remaining_to_mine"] = (
        table["max_supply"] - table["circulating_supply"]
    ).where(table["max_supply"].notna() & (table["max_supply"] > 0))
    table = table.rename(
        columns={
            "market_cap_rank": "Rang",
            "name": "Crypto",
            "symbol": "Symbole",
            "current_price": "Cours (USD)",
            "market_cap": "Capitalisation (USD)",
            "total_volume": "Volume 24 h (USD)",
            "price_change_percentage_24h": "Perf 24 h (%)",
            "price_change_percentage_7d_in_currency": "Perf 7 j (%)",
            "circulating_supply": "Stock circulant (quantité)",
            "max_supply": "Stock max (quantité)",
            "pct_mined": "Miné / Émis (%)",
            "remaining_to_mine": "Stock restant (quantité)",
        }
    )
    st.dataframe(
        table,
        width="stretch",
        height=560,
        hide_index=True,
        column_config={
            "Rang": st.column_config.NumberColumn("Rang", format="%d", help="Classement par capitalisation."),
            "Crypto": st.column_config.TextColumn("Crypto", help="Nom long de l'actif."),
            "Symbole": st.column_config.TextColumn("Symbole", help="Ticker (BTC, ETH, …)."),
            "Cours (USD)": st.column_config.NumberColumn("Cours (USD)", format="$ %.4f", help="Cours spot moyen multi-exchanges en dollars US."),
            "Capitalisation (USD)": st.column_config.NumberColumn("Capitalisation (USD)", format="$ %.0f", help="Capitalisation boursière en dollars US."),
            "Volume 24 h (USD)": st.column_config.NumberColumn("Volume 24 h (USD)", format="$ %.0f", help="Volume d'échange agrégé sur 24 h en dollars US."),
            "Perf 24 h (%)": st.column_config.NumberColumn("Perf 24 h (%)", format="%+.2f %%", help="Variation du cours sur 24 h en pourcentage."),
            "Perf 7 j (%)": st.column_config.NumberColumn("Perf 7 j (%)", format="%+.2f %%", help="Variation du cours sur 7 jours en pourcentage."),
            "Stock circulant (quantité)": st.column_config.NumberColumn("Stock circulant (quantité)", format="%.0f", help="Nombre d'unités en circulation."),
            "Stock max (quantité)": st.column_config.NumberColumn("Stock max (quantité)", format="%.0f", help="Plafond maximum d'émission, si défini par le protocole."),
            "Miné / Émis (%)": st.column_config.NumberColumn("Miné / Émis (%)", format="%.2f %%", help="Part de l'offre déjà émise par rapport au plafond, en pourcentage."),
            "Stock restant (quantité)": st.column_config.NumberColumn("Stock restant (quantité)", format="%.0f", help="Différence stock max − stock circulant, lorsque le plafond existe."),
        },
    )

    st.markdown("---")
    st.markdown("#### Cartographie paramétrable du marché")
    st.caption("Le treemap dimensionne chaque actif selon le critère retenu et le colorise par perf 24 h.")

    try:
        cats_df = get_categories()
    except Exception:
        cats_df = pd.DataFrame()
    category_options: list[tuple[str, str | None]] = [("Toutes catégories", None)]
    if not cats_df.empty and "name" in cats_df.columns and "id" in cats_df.columns:
        for _, cat_row in cats_df.sort_values("market_cap", ascending=False, na_position="last").iterrows():
            cat_name = cat_row.get("name")
            cat_slug = cat_row.get("id")
            if cat_name and cat_slug:
                category_options.append((str(cat_name), str(cat_slug)))

    filter_cols = st.columns([1.5, 1.4, 1, 1])
    with filter_cols[0]:
        category_label = st.selectbox(
            "Secteur / catégorie",
            [c[0] for c in category_options],
            help="Filtre par catégorie thématique CoinGecko (DeFi, AI, Layer 2, Meme, RWA, …).",
        )
        category_slug = next((c[1] for c in category_options if c[0] == category_label), None)
    with filter_cols[1]:
        criterion = st.selectbox(
            "Classement par",
            [
                "Capitalisation (USD)",
                "Volume 24 h (USD)",
                "Perf 24 h (%)",
                "Perf 7 j (%)",
                "Miné / Émis (%)",
                "Stock restant à miner (quantité)",
                "Cours (USD)",
            ],
            help="Variable qui définit la surface du treemap et le tri. La couleur reste la perf 24 h.",
        )
    with filter_cols[2]:
        top_n = st.selectbox("Top N", [10, 25, 50, 75, 100], index=1, help="Nombre d'actifs affichés sur la cartographie.")
    with filter_cols[3]:
        show_full_names = st.toggle("Étiquettes complètes", value=False, help="Afficher le nom complet en plus du symbole.")

    if category_slug:
        try:
            cat_rows = request_json(
                f"{COINGECKO}/coins/markets",
                {
                    "vs_currency": "usd",
                    "category": category_slug,
                    "order": "market_cap_desc",
                    "per_page": max(top_n, 50),
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "24h,7d",
                },
            )
            base_df = pd.DataFrame(cat_rows)
        except Exception as exc:
            st.warning(f"Catégorie indisponible ({exc}). Repli sur le top global.")
            base_df = markets.copy()
    else:
        base_df = markets.copy()

    if base_df.empty:
        st.info("Aucun actif à afficher pour ce filtre.")
    else:
        base_df = base_df.copy()
        base_df["pct_mined"] = (
            base_df["circulating_supply"] / base_df["max_supply"] * 100
        ).where(base_df.get("max_supply", pd.Series(dtype=float)).notna() & (base_df.get("max_supply", pd.Series(dtype=float)) > 0))
        base_df["remaining_to_mine"] = (
            base_df["max_supply"] - base_df["circulating_supply"]
        ).where(base_df.get("max_supply", pd.Series(dtype=float)).notna() & (base_df.get("max_supply", pd.Series(dtype=float)) > 0))

        criterion_map = {
            "Capitalisation (USD)": ("market_cap", "$"),
            "Volume 24 h (USD)": ("total_volume", "$"),
            "Perf 24 h (%)": ("price_change_percentage_24h", "%"),
            "Perf 7 j (%)": ("price_change_percentage_7d_in_currency", "%"),
            "Miné / Émis (%)": ("pct_mined", "%"),
            "Stock restant à miner (quantité)": ("remaining_to_mine", "qty"),
            "Cours (USD)": ("current_price", "$"),
        }
        crit_col, crit_unit = criterion_map[criterion]
        if crit_col not in base_df.columns:
            st.warning(f"Critère « {criterion} » indisponible pour ce filtre.")
        else:
            plot_df = (
                base_df.dropna(subset=[crit_col])
                .sort_values(crit_col, ascending=False)
                .head(top_n)
                .copy()
            )
            if plot_df.empty:
                st.info("Aucune donnée disponible pour ce critère sur ce filtre.")
            else:
                plot_df["Symbole"] = plot_df["symbol"].str.upper()
                plot_df["Label"] = plot_df["Symbole"] + (" — " + plot_df["name"] if show_full_names else "")
                plot_df["__abs"] = plot_df[crit_col].abs()
                plot_df["Capi (USD)"] = plot_df["market_cap"].apply(format_money)
                plot_df["Volume 24 h (USD)"] = plot_df["total_volume"].apply(format_money)
                plot_df["Perf 24 h"] = plot_df["price_change_percentage_24h"].apply(lambda v: format_pct(v) if pd.notna(v) else "n/a")
                plot_df["Critère"] = plot_df[crit_col].apply(
                    lambda v: (
                        format_money(v)
                        if crit_unit == "$"
                        else (format_pct(v) if crit_unit == "%" else format_quantity(v))
                    )
                )
                tm = px.treemap(
                    plot_df,
                    path=["Label"],
                    values="__abs",
                    color="price_change_percentage_24h",
                    color_continuous_scale=["#1e3a8a", "#2563eb", "#38bdf8", "#bae6fd"],
                    custom_data=["name", "Capi (USD)", "Volume 24 h (USD)", "Perf 24 h", "Critère"],
                )
                tm.update_traces(
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Nom : %{customdata[0]}<br>"
                        f"{criterion} : %{{customdata[4]}}<br>"
                        "Capitalisation : %{customdata[1]}<br>"
                        "Volume 24 h : %{customdata[2]}<br>"
                        "Perf 24 h : %{customdata[3]}<extra></extra>"
                    ),
                    textfont=dict(color="#f8fafc", size=14),
                    marker=dict(line=dict(color="#0b1226", width=2)),
                )
                apply_plotly_style(
                    tm,
                    title=f"Top {min(top_n, len(plot_df))} — {criterion}{' • ' + category_label if category_slug else ''}",
                )
                tm.update_layout(
                    height=620,
                    coloraxis_colorbar=dict(
                        title=dict(text="Perf 24 h (%)", font=dict(color="#cbd5e1")),
                        tickfont=dict(color="#cbd5e1"),
                    ),
                )
                st.plotly_chart(tm, width="stretch", config=PLOTLY_CONFIG)


with tab_stables:
    st.subheader("Stablecoins — capitalisation, peg, mécanismes")
    with st.expander("ℹ️ Données et limites", expanded=False):
        st.markdown(
            "- **Sources** : DefiLlama (capitalisations, peg, mécanisme, chaînes) + Yahoo Finance (suivi de peg quotidien via tickers USD).\n"
            "- **Peg deviation** : écart à 1 USD ; au-delà de quelques dizaines de points de base, c'est un signal de stress de peg.\n"
            "- **Mécanisme** : *Fiat-backed* (réserves bancaires), *Crypto-backed* (sur-collatéralisé), *Algorithmic* (offre/demande), *Hybrid*.\n"
            "- Les valeurs sont déclarées par les émetteurs ou estimées par les agrégateurs : marge d'erreur inévitable."
        )

    df_llama = get_stablecoins_defillama()
    if df_llama.empty:
        st.info("Données DefiLlama momentanément indisponibles. Repli sur CoinGecko ci-dessous.")
        try:
            stable_rows = request_json(
                f"{COINGECKO}/coins/markets",
                {
                    "vs_currency": "usd",
                    "category": "stablecoins",
                    "order": "market_cap_desc",
                    "per_page": 80,
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "24h,7d,30d",
                },
            )
            df_fallback = pd.DataFrame(stable_rows)
        except Exception as exc:
            df_fallback = pd.DataFrame()
            st.warning(f"Repli CoinGecko également indisponible ({exc}).")
        if not df_fallback.empty:
            kpis = st.columns(3)
            kpis[0].metric("Capitalisation stablecoins (USD)", format_money(df_fallback["market_cap"].sum()))
            kpis[1].metric("Volume 24 h stablecoins (USD)", format_money(df_fallback["total_volume"].sum()))
            kpis[2].metric("Stablecoins suivis (quantité)", f"{len(df_fallback)}")
            st.dataframe(df_fallback, width="stretch", height=420, hide_index=True)
    else:
        kpis = st.columns(4)
        kpis[0].metric("Capitalisation stablecoins (USD)", format_money(df_llama["Circulation (USD)"].sum()))
        kpis[1].metric("Stablecoins suivis (quantité)", f"{len(df_llama):,}".replace(",", " "))
        if "USDT" in df_llama["Symbole"].values:
            usdt_mc = df_llama.loc[df_llama["Symbole"] == "USDT", "Circulation (USD)"].iloc[0]
            kpis[2].metric("Capitalisation USDT (USD)", format_money(usdt_mc))
        else:
            kpis[2].metric("Capitalisation USDT (USD)", "n/a")
        top_share = df_llama.head(3)["Circulation (USD)"].sum() / max(df_llama["Circulation (USD)"].sum(), 1) * 100
        kpis[3].metric("Concentration top 3 (%)", format_pct(top_share), help="Part des trois premiers stablecoins dans la capitalisation totale.")

        st.markdown("#### Top stablecoins (DefiLlama)")
        st.caption(
            "Capitalisations en USD, mécanisme et chaînes principales. La colonne *Tendance capi* est une mini-courbe "
            "de la capitalisation sur la période d'analyse — survole-la pour voir la valeur à chaque date. La colonne "
            "*Nombre de chaînes* indique sur combien de blockchains distinctes le stablecoin est émis (Ethereum, Tron, "
            "BSC, Solana, Avalanche, Arbitrum, etc.)."
        )
        stable_id_map = get_stablecoin_id_map()
        top_stables = df_llama.head(40).copy()
        sparkline_data: dict[str, list[float]] = {}
        sparkline_targets = top_stables.head(8)["Symbole"].tolist()
        with st.spinner("Chargement des mini-courbes de tendance…"):
            for sym in sparkline_targets:
                cg_id = stable_id_map.get(str(sym).upper())
                if not cg_id:
                    continue
                try:
                    series = get_stable_marketcap_sparkline(cg_id, start_date, end_date)
                except Exception:
                    series = []
                if series:
                    sparkline_data[sym] = series
        top_stables["Tendance capi"] = top_stables["Symbole"].map(sparkline_data)
        column_order = [
            "Symbole", "Nom", "Tendance capi", "Cours (USD)", "Circulation (USD)",
            "Type de peg", "Mécanisme", "Nombre de chaînes", "Chaînes principales",
        ]
        column_order = [c for c in column_order if c in top_stables.columns]
        st.dataframe(
            top_stables[column_order],
            width="stretch",
            height=420,
            hide_index=True,
            column_config={
                "Cours (USD)": st.column_config.NumberColumn("Cours (USD)", format="$ %.4f", help="Cours observé vs USD (proche de 1 si peg respecté)."),
                "Circulation (USD)": st.column_config.NumberColumn("Circulation (USD)", format="$ %.0f", help="Valeur déclarée des unités émises."),
                "Nombre de chaînes": st.column_config.NumberColumn(
                    "Nombre de chaînes",
                    format="%d",
                    help="Nombre de blockchains distinctes sur lesquelles le stablecoin est déployé (Ethereum, Tron, Solana, BSC, Arbitrum, etc.). Une présence multi-chaînes améliore la liquidité et la résilience opérationnelle.",
                ),
                "Chaînes principales": st.column_config.TextColumn(
                    "Chaînes principales",
                    help="Cinq premières blockchains où le stablecoin est le plus présent (par circulation).",
                ),
                "Tendance capi": st.column_config.LineChartColumn(
                    "Tendance capi",
                    width="medium",
                    help=(
                        "Mini-graphique de la capitalisation sur la période d'analyse sélectionnée dans la barre latérale. "
                        "Survole la sparkline pour faire apparaître la valeur ponctuelle ; pour un graphique plein écran, "
                        "utilise le moteur de recherche « Zoom sur un stablecoin » plus bas."
                    ),
                ),
            },
        )

        st.markdown("#### Parts de marché — top stablecoins")
        share_df_full = df_llama.head(20).copy()
        share_df_full["Part de marché (%)"] = share_df_full["Circulation (USD)"] / df_llama["Circulation (USD)"].sum() * 100
        top_n_share = share_df_full.head(8).copy()
        autres = share_df_full.iloc[8:]
        if not autres.empty:
            autres_row = pd.DataFrame(
                [
                    {
                        "Symbole": "Autres",
                        "Nom": f"{len(autres)} autres stablecoins",
                        "Circulation (USD)": autres["Circulation (USD)"].sum(),
                        "Part de marché (%)": autres["Part de marché (%)"].sum(),
                    }
                ]
            )
            share_pie = pd.concat([top_n_share, autres_row], ignore_index=True)
        else:
            share_pie = top_n_share
        share_pie["Capitalisation (USD)"] = share_pie["Circulation (USD)"].apply(format_money)

        bar_fig = px.bar(
            share_pie.sort_values("Circulation (USD)", ascending=True),
            x="Part de marché (%)",
            y="Symbole",
            orientation="h",
            color="Part de marché (%)",
            color_continuous_scale=["#1e3a8a", "#2563eb", "#38bdf8", "#bae6fd"],
            text="Part de marché (%)",
            custom_data=["Nom", "Capitalisation (USD)"],
        )
        bar_fig.update_traces(
            texttemplate="%{x:.2f} %",
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>Part : %{x:.2f} %<br>Capitalisation : %{customdata[1]}<extra></extra>",
        )
        apply_plotly_style(
            bar_fig,
            title="Parts de marché — top 8 + agrégat « Autres »",
            x_title="Part de la capitalisation totale (%)",
            y_title=None,
            legend_below=False,
        )
        bar_fig.update_layout(showlegend=False, coloraxis_showscale=False, height=420)
        st.plotly_chart(bar_fig, width="stretch", config=PLOTLY_CONFIG)

        st.markdown("##### Vue circulaire détaillée")
        st.caption("Graphique pleine largeur : les libellés et la légende disposent de plus d'espace, ce qui évite l'empilement observé en colonne.")
        donut_fig = px.pie(
            share_pie,
            names="Symbole",
            values="Circulation (USD)",
            hole=0.62,
            color_discrete_sequence=["#38bdf8", "#2563eb", "#a78bfa", "#22d3ee", "#60a5fa", "#818cf8", "#f472b6", "#facc15", "#94a3b8"],
        )
        donut_fig.update_traces(
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(color="#f1f5f9", size=14),
            marker=dict(line=dict(color="#0b1226", width=2)),
            pull=[0.015] * len(share_pie),
            automargin=True,
            hovertemplate="<b>%{label}</b><br>Capitalisation : %{value:$,.0f}<br>Part : %{percent}<extra></extra>",
        )
        apply_plotly_style(donut_fig, title="Vue circulaire — part de capitalisation des stablecoins", legend_below=True)
        donut_fig.update_layout(
            height=720,
            margin=dict(t=95, l=100, r=100, b=150),
            uniformtext_minsize=11,
            uniformtext_mode="hide",
        )
        st.plotly_chart(donut_fig, width="stretch", config=PLOTLY_CONFIG)

    st.markdown("#### Suivi de peg via Yahoo Finance")
    peg_df = get_stable_peg_history(days=45)
    if peg_df.empty:
        st.info("Suivi de peg via Yahoo Finance indisponible pour le moment.")
    else:
        peg_fig = px.line(
            peg_df,
            x="Date",
            y="Prix (USD)",
            color="Stablecoin",
            color_discrete_sequence=["#38bdf8", "#2563eb", "#a78bfa", "#22d3ee", "#60a5fa", "#818cf8", "#f472b6"],
        )
        peg_fig.update_traces(line=dict(width=1.6))
        peg_fig.add_hline(y=1.0, line=dict(color="rgba(148,163,184,0.55)", dash="dot"))
        apply_plotly_style(peg_fig, title="Peg observé vs 1 USD — 45 derniers jours (Yahoo Finance)", y_title="Prix (USD)", x_title="Date")
        st.plotly_chart(peg_fig, width="stretch", config=PLOTLY_CONFIG)

        latest = peg_df.sort_values("Date").groupby("Stablecoin").tail(1).copy()
        latest["Écart au peg (pb)"] = (latest["Prix (USD)"] - 1) * 10_000
        st.markdown("##### Dernière observation par stablecoin")
        st.dataframe(
            latest[["Stablecoin", "Date", "Prix (USD)", "Écart au peg (pb)"]],
            width="stretch",
            hide_index=True,
            column_config={
                "Prix (USD)": st.column_config.NumberColumn("Prix (USD)", format="$ %.4f"),
                "Écart au peg (pb)": st.column_config.NumberColumn("Écart au peg (pb)", format="%+.1f", help="Écart au peg en points de base (1 pb = 0,01 %). >100 pb = stress significatif."),
            },
        )

    st.markdown("#### Capitalisation totale stablecoins — historique DefiLlama")
    period_days = max((end_date - start_date).days, 30)
    total_hist = get_stable_total_history(days=period_days)
    if total_hist.empty:
        st.info("Historique total DefiLlama momentanément indisponible.")
    else:
        total_fig = go.Figure()
        total_fig.add_trace(
            go.Scatter(
                x=total_hist["Date"],
                y=total_hist["Capitalisation totale (USD)"],
                mode="lines",
                fill="tozeroy",
                line=dict(color="#38bdf8", width=2),
                fillcolor="rgba(56, 189, 248, 0.20)",
                name="Capitalisation totale (DefiLlama)",
                hovertemplate="<b>Total stablecoins</b><br>%{x|%d %b %Y}<br>%{y:$,.0f}<extra></extra>",
            )
        )
        apply_plotly_style(
            total_fig,
            title=f"Capitalisation totale des stablecoins — {period_days} derniers jours (USD)",
            y_title="Capitalisation (USD)",
            x_title="Date",
        )
        total_fig.update_layout(height=440, hovermode="x unified", showlegend=False)
        st.plotly_chart(total_fig, width="stretch", config=PLOTLY_CONFIG)
        st.caption(
            "Trace la capitalisation cumulée de l'ensemble des stablecoins suivis par DefiLlama sur la période "
            "d'analyse définie dans la barre latérale. Pour zoomer sur un stablecoin précis, utilise le moteur "
            "de recherche ci-dessous (ou survole la mini-courbe *Tendance capi* du tableau plus haut)."
        )

    st.markdown("#### Zoom sur un stablecoin")
    st.caption(
        "Saisis quelques lettres pour filtrer la liste : la recherche couvre tous les stablecoins disposant d'un "
        "historique CoinGecko. Le graphique affiche la capitalisation et le cours sur la période d'analyse sélectionnée."
    )

    detail_id_map = get_stablecoin_id_map()
    df_llama_norm = df_llama.copy()
    df_llama_norm["__sym"] = df_llama_norm["Symbole"].astype(str).str.upper()
    candidates = df_llama_norm[df_llama_norm["__sym"].isin(detail_id_map.keys())].copy()

    if candidates.empty and detail_id_map:
        candidates = pd.DataFrame(
            [
                {"Symbole": sym, "__sym": sym, "Nom": sym, "Circulation (USD)": float("nan")}
                for sym in detail_id_map.keys()
            ]
        )

    if candidates.empty:
        st.info("Aucun stablecoin avec historique CoinGecko exploitable pour le moment.")
    else:
        candidates["__label"] = candidates.apply(
            lambda r: f"{r['__sym']} — {r.get('Nom') or r['__sym']}".strip(" —"),
            axis=1,
        )
        candidates = candidates.drop_duplicates(subset="__label").reset_index(drop=True)
        labels = candidates["__label"].tolist()
        default_idx = 0
        for i, sym in enumerate(candidates["__sym"]):
            if sym == "USDT":
                default_idx = i
                break
        selected_label = st.selectbox(
            "Rechercher un stablecoin",
            options=labels,
            index=default_idx,
            help="Recherche libre par symbole ou nom (filtrage intégré de Streamlit).",
        )
        row = candidates.loc[candidates["__label"] == selected_label].iloc[0]
        selected_symbol = row["__sym"]
        coin_id = detail_id_map.get(selected_symbol)
        if not coin_id:
            st.info("Identifiant CoinGecko introuvable pour ce stablecoin.")
        else:
            try:
                detail_hist = get_coin_history(coin_id, start_date, end_date)
            except Exception as exc:
                detail_hist = pd.DataFrame()
                st.warning(f"Historique indisponible ({exc}).")
            if detail_hist.empty:
                st.info("Historique indisponible pour ce stablecoin sur la période sélectionnée.")
            else:
                kpi_cols = st.columns(4)
                last_cap = float(detail_hist["market_cap"].dropna().iloc[-1]) if "market_cap" in detail_hist else float("nan")
                first_cap = float(detail_hist["market_cap"].dropna().iloc[0]) if "market_cap" in detail_hist else float("nan")
                last_price = float(detail_hist["price"].dropna().iloc[-1]) if "price" in detail_hist else float("nan")
                cap_change = ((last_cap / first_cap) - 1) * 100 if first_cap else float("nan")
                kpi_cols[0].metric("Capitalisation actuelle (USD)", format_money(last_cap))
                kpi_cols[1].metric("Capitalisation au début (USD)", format_money(first_cap))
                kpi_cols[2].metric("Variation sur la période", format_pct(cap_change) if pd.notna(cap_change) else "n/a")
                if pd.notna(last_price):
                    kpi_cols[3].metric(
                        "Cours actuel (USD)",
                        f"$ {last_price:,.4f}".replace(",", " "),
                        delta=f"{(last_price - 1) * 10_000:+.1f} pb vs peg" if last_price else None,
                        help="Écart au peg exprimé en points de base (1 pb = 0,01 %).",
                    )

                detail_fig = make_subplots(
                    rows=2,
                    cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.10,
                    row_heights=[0.62, 0.38],
                    subplot_titles=("Capitalisation (USD)", "Cours vs 1 USD"),
                )
                detail_fig.add_trace(
                    go.Scatter(
                        x=detail_hist["date"],
                        y=detail_hist["market_cap"],
                        mode="lines",
                        line=dict(color="#38bdf8", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(56, 189, 248, 0.18)",
                        name="Capitalisation",
                        hovertemplate="%{x|%d %b %Y}<br>Capi : %{y:$,.0f}<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )
                detail_fig.add_trace(
                    go.Scatter(
                        x=detail_hist["date"],
                        y=detail_hist["price"],
                        mode="lines",
                        line=dict(color="#facc15", width=1.6),
                        name="Cours",
                        hovertemplate="%{x|%d %b %Y}<br>Cours : %{y:$.4f}<extra></extra>",
                    ),
                    row=2,
                    col=1,
                )
                detail_fig.add_hline(
                    y=1.0,
                    line=dict(color="rgba(148,163,184,0.6)", dash="dot"),
                    row=2,
                    col=1,
                )
                apply_plotly_style(
                    detail_fig,
                    title=f"{selected_symbol} — {row.get('Nom') or ''} ({period_days} jours)",
                )
                detail_fig.update_layout(
                    height=620,
                    hovermode="x unified",
                    showlegend=False,
                    margin=dict(t=90, l=70, r=40, b=60),
                )
                detail_fig.update_yaxes(title_text="Capitalisation (USD)", row=1, col=1)
                detail_fig.update_yaxes(title_text="Cours (USD)", row=2, col=1)
                detail_fig.update_xaxes(title_text="Date", row=2, col=1)
                st.plotly_chart(detail_fig, width="stretch", config=PLOTLY_CONFIG)
                st.caption(
                    f"Source : CoinGecko (`{coin_id}`). La ligne pointillée à 1 USD sert de repère de peg ; "
                    "tout écart durable au-delà de quelques dizaines de points de base est un signal de stress."
                )

with tab_asset:
    head_left, head_right = st.columns([3, 1])
    with head_left:
        st.subheader(f"Fiche détaillée — {asset_name} ({asset_symbol})")
    with st.expander("ℹ️ Que contient cette fiche ?", expanded=False):
        st.markdown(
            "- **Indicateurs clés** : cours, capitalisation, volume, plus haut / plus bas 24 h.\n"
            "- **Émission** : ratio stock circulant / plafond (PoW) ou stock total (PoS).\n"
            "- **Métadonnées** : origine, catégories, communauté, développement.\n"
            "- **Historique** : cours, capitalisation et volume sur la période sélectionnée dans la barre latérale.\n"
            "- **Rapport PDF** : bouton en haut à droite pour télécharger un rapport prêt à diffuser."
        )

    detail_error: str | None = None
    try:
        details = get_coin_details(selected_id)
    except Exception as exc:
        details = {}
        detail_error = str(exc)
    if detail_error:
        st.warning(f"Métadonnées détaillées partiellement indisponibles ({detail_error}).")

    history_for_report = pd.DataFrame()
    try:
        history_for_report = get_coin_history(selected_id, start_date, end_date)
    except Exception:
        pass

    with head_right:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        try:
            pdf_bytes = build_crypto_pdf_report(
                asset_name=asset_name,
                asset_symbol=asset_symbol,
                market_row=selected_row,
                details=details,
                history=history_for_report,
                start_date=start_date,
                end_date=end_date,
            )
            st.download_button(
                "📄 Télécharger le rapport PDF",
                data=pdf_bytes,
                file_name=f"CoCrypto_{asset_symbol}_{date.today().isoformat()}.pdf",
                mime="application/pdf",
                width="stretch",
                help="Génère un rapport PDF mis en forme (logo, indicateurs clés, émission, historique, communauté, liens). Compatible impression Chrome.",
            )
        except Exception as exc:
            st.warning(f"Rapport PDF indisponible ({exc}).")

    market_data = details.get("market_data") or {}
    high_24 = (market_data.get("high_24h") or {}).get("usd") if isinstance(market_data.get("high_24h"), dict) else None
    low_24 = (market_data.get("low_24h") or {}).get("usd") if isinstance(market_data.get("low_24h"), dict) else None
    ath = (market_data.get("ath") or {}).get("usd") if isinstance(market_data.get("ath"), dict) else None
    atl = (market_data.get("atl") or {}).get("usd") if isinstance(market_data.get("atl"), dict) else None
    fdv = (market_data.get("fully_diluted_valuation") or {}).get("usd") if isinstance(market_data.get("fully_diluted_valuation"), dict) else None

    kpi_cols = st.columns(4)
    kpi_cols[0].metric(
        "Cours (USD)",
        format_money(selected_row.get("current_price")),
        format_pct(selected_row.get("price_change_percentage_24h")),
        help="Cours spot moyen multi-exchanges. Variation = perf 24 h.",
    )
    kpi_cols[1].metric(
        "Plus haut / Plus bas 24 h (USD)",
        f"{format_money(high_24)} / {format_money(low_24)}",
        help="Bornes de variation du cours sur les dernières 24 h.",
    )
    kpi_cols[2].metric(
        "FDV (USD)",
        format_money(fdv),
        help="Fully Diluted Valuation : cours × stock max si toutes les unités étaient en circulation.",
    )
    kpi_cols[3].metric(
        "ATH / ATL (USD)",
        f"{format_money(ath)} / {format_money(atl)}",
        help="All-Time High / All-Time Low : extrêmes historiques observés.",
    )

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        ratio, ratio_label = supply_progress(selected_row)
        if ratio is None:
            st.markdown(
                f'<div class="co-card"><h4>Émission / Minage</h4>'
                f'<p style="color: var(--co-muted); margin: 0;">{ratio_label}</p></div>',
                unsafe_allow_html=True,
            )
        else:
            bar_width = ratio * 100
            st.markdown(
                f"""
                <div class="co-card">
                  <h4>Émission / Minage</h4>
                  <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                    <span style="color: var(--co-muted); font-size: 0.85rem;">{ratio_label}</span>
                    <span style="color: var(--co-text-strong); font-weight: 700;">{bar_width:.2f} %</span>
                  </div>
                  <div style="height: 12px; background: rgba(56,189,248,0.12); border-radius: 8px; overflow: hidden;">
                    <div style="height: 100%; width: {bar_width:.2f}%; background: linear-gradient(90deg, #1d4ed8, #38bdf8);"></div>
                  </div>
                  <p style="color: var(--co-muted); font-size: 0.78rem; margin-top: 0.6rem;">
                    PoW : approximation du minage réalisé. PoS : approximation de l'émission distribuée.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        render_kv_card(
            "Offre & technologie",
            [
                ("Stock circulant (quantité)", format_quantity(selected_row.get("circulating_supply"))),
                ("Stock total déclaré (quantité)", format_quantity(selected_row.get("total_supply"))),
                ("Stock maximum (quantité)", format_quantity(selected_row.get("max_supply"))),
                ("Algorithme de hachage", details.get("hashing_algorithm") or "n/a"),
                ("Temps de bloc moyen (min)", str(details.get("block_time_in_minutes") or "n/a")),
                ("Date de genèse", details.get("genesis_date") or "n/a"),
            ],
        )
    with col_b:
        community = details.get("community_data") or {}
        developer = details.get("developer_data") or {}
        render_kv_card(
            "Communauté & développement",
            [
                ("Twitter (abonnés)", format_quantity(community.get("twitter_followers"))),
                ("Reddit (abonnés)", format_quantity(community.get("reddit_subscribers"))),
                ("Telegram (utilisateurs)", format_quantity(community.get("telegram_channel_user_count"))),
                ("GitHub — stars", format_quantity(developer.get("stars"))),
                ("GitHub — forks", format_quantity(developer.get("forks"))),
                ("GitHub — commits 4 sem.", format_quantity(developer.get("commit_count_4_weeks"))),
            ],
        )
    with col_c:
        categories_list = details.get("categories") or []
        country = details.get("country_origin") or "n/a"
        homepage = (details.get("links", {}).get("homepage") or [""])[0] or "n/a"
        twitter = details.get("links", {}).get("twitter_screen_name") or "n/a"
        github_repos = (details.get("links", {}).get("repos_url", {}) or {}).get("github", []) or []
        render_tag_card(
            "Catégories & secteurs",
            [c for c in categories_list[:12] if c],
            extra=f"Origine déclarée : {country} • Site : {homepage} • X : @{twitter} • Repos GitHub : {len(github_repos)}",
        )

    history = history_for_report

    if history.empty:
        st.info("Pas assez d'historique sur la période choisie.")
    else:
        price_fig = go.Figure()
        price_fig.add_trace(
            go.Scatter(
                x=history["date"],
                y=history["price"],
                mode="lines",
                line=dict(color="#38bdf8", width=2),
                fill="tozeroy",
                fillcolor="rgba(56, 189, 248, 0.10)",
                name=f"{asset_symbol} cours (USD)",
            )
        )
        apply_plotly_style(
            price_fig,
            title=f"Cours {asset_symbol} sur la période sélectionnée (USD)",
            y_title="Cours (USD)",
            x_title="Date",
        )
        st.plotly_chart(price_fig, width="stretch", config=PLOTLY_CONFIG)

        mv = history.melt(id_vars="date", value_vars=["market_cap", "volume"], var_name="Série", value_name="Montant (USD)")
        mv["Série"] = mv["Série"].map({"market_cap": "Capitalisation (USD)", "volume": "Volume (USD)"})
        mv_fig = px.area(mv, x="date", y="Montant (USD)", color="Série", color_discrete_sequence=["#2563eb", "#38bdf8"])
        apply_plotly_style(mv_fig, title="Capitalisation et volume historiques (USD)", y_title="Montant (USD)", x_title="Date")
        st.plotly_chart(mv_fig, width="stretch", config=PLOTLY_CONFIG)

with tab_compare:
    st.subheader("Comparaisons crypto & benchmark")
    with st.expander("ℹ️ Lecture des graphiques de comparaison", expanded=False):
        st.markdown(
            "- **Base 100** : chaque série démarre à 100 sur la première date commune ; on lit la performance relative.\n"
            "- **Drawdown (%)** : recul depuis le plus haut atteint sur la période ; mesure de risque baissier.\n"
            "- **Corrélation glissante 30 j** : corrélation de Pearson sur les variations journalières, fenêtre 30 j.\n"
            "- **Distribution des rendements** : histogramme des variations journalières — épaisseur des queues = risque de chocs.\n"
            "- **Benchmarks via proxy** : MSCI ACWI IMI Blockchain Economy ≈ ETF BLOK (sous licence MSCI), Or ≈ ETF GLD."
        )

    peers = st.multiselect(
        "Comparer avec d'autres cryptos",
        markets["id"].tolist(),
        default=[coin for coin in ["ethereum", "solana"] if coin in markets["id"].tolist()],
        format_func=lambda coin_id: f"{markets.loc[markets['id'] == coin_id, 'name'].iloc[0]} ({markets.loc[markets['id'] == coin_id, 'symbol'].iloc[0].upper()})",
        help="Sélectionne jusqu'à plusieurs cryptos pour les confronter à l'actif principal et au benchmark.",
    )
    benchmark_symbol = BENCHMARKS[benchmark_name]
    st.info(
        f"Benchmark **{benchmark_name}** : l'indice MSCI exact est propriétaire (sous licence), "
        f"on utilise donc l'ETF **{benchmark_symbol}** comme proxy public coté. Pour l'or, l'ETF **GLD** sert de proxy liquide. "
        "Les performances sont ainsi indicatives.",
        icon="ℹ️",
    )

    series_perf: list[pd.DataFrame] = []
    series_raw: dict[str, pd.Series] = {}
    label_map: dict[str, str] = {}
    for coin_id in [selected_id] + peers:
        try:
            h = get_coin_history(coin_id, start_date, end_date)
            label = markets.loc[markets["id"] == coin_id, "symbol"].iloc[0].upper()
            label_map[coin_id] = label
            if h.empty:
                continue
            series_perf.append(normalize_series(h, "price", label))
            indexed = h.set_index("date")["price"].resample("1D").last().dropna()
            indexed.index = indexed.index.tz_localize(None)
            series_raw[label] = indexed
        except Exception:
            continue
    try:
        bench = get_benchmark(benchmark_symbol, start_date, end_date)
        series_perf.append(normalize_series(bench, "benchmark", benchmark_name))
        bench_indexed = bench.set_index("date")["benchmark"].dropna()
        bench_indexed.index = pd.to_datetime(bench_indexed.index).tz_localize(None) if bench_indexed.index.tz is None else bench_indexed.index.tz_convert(None)
        series_raw[benchmark_name] = bench_indexed
    except Exception as exc:
        st.warning(f"Benchmark indisponible pour le moment ({exc}).")

    comparison = pd.concat([s for s in series_perf if not s.empty], ignore_index=True) if series_perf else pd.DataFrame()
    if comparison.empty:
        st.warning("Aucune série n'a pu être normalisée pour la comparaison.")
    else:
        perf_fig = px.line(
            comparison,
            x="Date",
            y="performance",
            color="Série",
            color_discrete_sequence=["#38bdf8", "#a78bfa", "#f472b6", "#facc15", "#4ade80", "#f97316"],
        )
        perf_fig.update_traces(line=dict(width=2.2))
        apply_plotly_style(perf_fig, title="Performance normalisée — base 100 au début de la période", y_title="Indice (base 100)", x_title="Date")
        st.plotly_chart(perf_fig, width="stretch", config=PLOTLY_CONFIG)

        # Drawdown
        dd_rows: list[pd.DataFrame] = []
        for label, serie in series_raw.items():
            if serie.empty:
                continue
            rolling_max = serie.cummax()
            drawdown = (serie / rolling_max - 1) * 100
            dd_rows.append(pd.DataFrame({"Date": drawdown.index, "Drawdown (%)": drawdown.values, "Série": label}))
        if dd_rows:
            dd_df = pd.concat(dd_rows, ignore_index=True)
            dd_fig = px.line(
                dd_df,
                x="Date",
                y="Drawdown (%)",
                color="Série",
                color_discrete_sequence=["#38bdf8", "#a78bfa", "#f472b6", "#facc15", "#4ade80", "#f97316"],
            )
            dd_fig.update_traces(line=dict(width=1.8))
            apply_plotly_style(dd_fig, title="Drawdown (%) — recul depuis le plus haut sur la période", y_title="Drawdown (%)", x_title="Date")
            st.plotly_chart(dd_fig, width="stretch", config=PLOTLY_CONFIG)

        # Rolling correlation between selected asset and others
        main_label = label_map.get(selected_id, asset_symbol)
        if main_label in series_raw:
            main_returns = series_raw[main_label].pct_change()
            corr_rows: list[pd.DataFrame] = []
            for label, serie in series_raw.items():
                if label == main_label or serie.empty:
                    continue
                other_returns = serie.pct_change()
                aligned = pd.concat([main_returns, other_returns], axis=1, keys=["a", "b"]).dropna()
                if aligned.empty or len(aligned) < 30:
                    continue
                rolling_corr = aligned["a"].rolling(30).corr(aligned["b"])
                corr_rows.append(pd.DataFrame({"Date": rolling_corr.index, f"Corrélation 30 j (Pearson)": rolling_corr.values, "Série": f"{main_label} vs {label}"}))
            if corr_rows:
                corr_df = pd.concat(corr_rows, ignore_index=True).dropna(subset=[f"Corrélation 30 j (Pearson)"])
                corr_fig = px.line(
                    corr_df,
                    x="Date",
                    y="Corrélation 30 j (Pearson)",
                    color="Série",
                    color_discrete_sequence=["#38bdf8", "#a78bfa", "#f472b6", "#facc15", "#4ade80", "#f97316"],
                )
                apply_plotly_style(corr_fig, title=f"Corrélation glissante 30 j — {main_label} vs autres séries", y_title="Coefficient de corrélation", x_title="Date")
                corr_fig.add_hline(y=0, line=dict(color="rgba(148,163,184,0.4)", dash="dot"))
                st.plotly_chart(corr_fig, width="stretch", config=PLOTLY_CONFIG)

        # Distribution of returns
        ret_rows: list[pd.DataFrame] = []
        for label, serie in series_raw.items():
            if serie.empty:
                continue
            returns = serie.pct_change().dropna() * 100
            ret_rows.append(pd.DataFrame({"Variation journalière (%)": returns.values, "Série": label}))
        if ret_rows:
            ret_df = pd.concat(ret_rows, ignore_index=True)
            dist_fig = px.histogram(
                ret_df,
                x="Variation journalière (%)",
                color="Série",
                nbins=60,
                barmode="overlay",
                opacity=0.55,
                color_discrete_sequence=["#38bdf8", "#a78bfa", "#f472b6", "#facc15", "#4ade80", "#f97316"],
            )
            apply_plotly_style(dist_fig, title="Distribution des variations journalières (%)", y_title="Fréquence (nombre de jours)", x_title="Variation journalière (%)")
            st.plotly_chart(dist_fig, width="stretch", config=PLOTLY_CONFIG)
            with st.expander("ℹ️ Comment lire la distribution des variations journalières", expanded=False):
                st.markdown(
                    """
                    - **Axe horizontal** : variation quotidienne du cours en pourcentage. Une barre à `+5 %` rassemble les
                      journées où l'actif a gagné entre 4 % et 5 % (ou 5 % et 6 %, selon la résolution).
                    - **Axe vertical** : nombre de jours observés sur la période sélectionnée à cette amplitude.
                    - **Centrage** : si le pic est légèrement à droite de 0, l'actif a tendance à monter ; à gauche, à baisser.
                    - **Largeur de la cloche** (volatilité) : plus l'histogramme est étalé, plus la volatilité est élevée.
                    - **Queues de distribution** : barres isolées loin du centre (±10 %, ±20 %) = jours de choc. Des queues
                      épaisses signalent un risque d'événements extrêmes (krach, pump) supérieur à une loi normale.
                    - **Comparaison de séries** : superposition en mode *overlay*, plus une cloche est étroite et centrée, plus le
                      profil de risque est sage. Or et benchmarks actions ont en général des queues bien plus fines que les cryptos.
                    """
                )

with tab_flows:
    st.subheader("Flux, cycles et tendances")
    with st.expander("ℹ️ Méthodologie des indicateurs de cycle et de flux", expanded=False):
        st.markdown(
            "- **Cycle modèle** : règle simple. *Bull* si cours > moyenne mobile longue **et** momentum positif. *Bear* si cours < moyenne mobile longue **et** momentum négatif. Sinon *Transition*.\n"
            "- **Moyenne mobile** : fenêtre adaptée à la période sélectionnée, plafonnée à 200 jours.\n"
            "- **Momentum** : variation du cours sur une fenêtre courte (≤ 90 j) en pourcentage.\n"
            "- **Flux proxy** : variation glissante de la capitalisation sur 7 jours, faute d'accès direct aux flux on-chain et exchange. C'est une **approximation**, à raffiner avec TVL, stablecoin inflows, ETF flows et open interest pour une lecture institutionnelle."
        )

    try:
        history = get_coin_history(selected_id, start_date, end_date)
    except Exception as exc:
        history = pd.DataFrame()
        st.warning(f"Historique indisponible ({exc}).")
    cycle_label, cycle_explanation, momentum, sma, sma_window, momentum_window = cycle_model(history)
    badge_class = {"Bull": "bull", "Bear": "bear", "Transition": "transition"}.get(cycle_label, "neutral")

    cycle_cols = st.columns([1.4, 1, 1, 1])
    with cycle_cols[0]:
        st.markdown(
            f"""
            <div class="co-card">
              <h4>Cycle modèle</h4>
              <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem;">
                <span class="co-badge {badge_class}">{cycle_label}</span>
                <span style="color: var(--co-muted); font-size: 0.85rem;">SMA {sma_window} j • momentum {momentum_window} j</span>
              </div>
              <p style="margin: 0; color: var(--co-text); font-size: 0.9rem;">{cycle_explanation}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    cycle_cols[1].metric(
        "Momentum (%)",
        format_pct(momentum) if momentum is not None else "n/a",
        help=f"Variation du cours sur la fenêtre {momentum_window} j sélectionnée.",
    )
    cycle_cols[2].metric(
        f"SMA {sma_window} j (USD)",
        format_money(sma),
        help="Moyenne mobile simple longue : signal de tendance structurelle.",
    )
    cycle_cols[3].metric(
        "Volume / Capi (%)",
        format_pct((selected_row.get("total_volume") / selected_row.get("market_cap") * 100) if selected_row.get("market_cap") else None),
        help="Volume 24 h rapporté à la capitalisation. Au-dessus de 10 % → forte rotation, sous 1 % → liquidité réduite.",
    )

    if not history.empty:
        flow = history.copy()
        flow["market_cap_change"] = flow["market_cap"].diff()
        flow["flux_proxy"] = flow["market_cap_change"].rolling(7, min_periods=1).sum()
        colors = ["#4ade80" if v >= 0 else "#f87171" for v in flow["flux_proxy"].fillna(0)]
        flow_fig = go.Figure()
        flow_fig.add_bar(x=flow["date"], y=flow["flux_proxy"], name="Flux proxy 7 j (USD)", marker=dict(color=colors))
        apply_plotly_style(flow_fig, title="Flux proxy — variation glissante 7 j de la capitalisation (USD)", y_title="Variation 7 j (USD)", x_title="Date")
        flow_fig.add_hline(y=0, line=dict(color="rgba(148,163,184,0.5)", dash="dot"))
        st.plotly_chart(flow_fig, width="stretch", config=PLOTLY_CONFIG)

        price_sma_fig = go.Figure()
        price_sma_fig.add_trace(go.Scatter(x=history["date"], y=history["price"], mode="lines", name=f"{asset_symbol} cours (USD)", line=dict(color="#38bdf8", width=2)))
        sma_series = history.set_index("date")["price"].resample("1D").last().rolling(sma_window).mean()
        price_sma_fig.add_trace(go.Scatter(x=sma_series.index, y=sma_series.values, mode="lines", name=f"SMA {sma_window} j", line=dict(color="#f472b6", width=1.6, dash="dash")))
        apply_plotly_style(price_sma_fig, title=f"Cours vs SMA {sma_window} j — repère visuel du régime de cycle", y_title="Cours (USD)", x_title="Date")
        st.plotly_chart(price_sma_fig, width="stretch", config=PLOTLY_CONFIG)

    st.markdown("##### Répartition sectorielle")
    st.caption(
        "Source : endpoint `/coins/categories` de CoinGecko — chaque crypto est rattachée par CoinGecko à une ou plusieurs catégories "
        "thématiques (DeFi, Layer 1, Layer 2, AI, Meme, RWA, Gaming, …). Pour chaque catégorie, CoinGecko agrège la capitalisation, "
        "le volume et la variation 24 h de l'ensemble des actifs membres. C'est une vue *macro* du marché crypto, à compléter par "
        "des taxonomies internes pour un usage institutionnel."
    )
    try:
        categories = get_categories()
        if not categories.empty:
            sector = categories[["name", "market_cap", "market_cap_change_24h", "volume_24h"]].dropna(subset=["market_cap"]).head(40)
            sector_top = sector.sort_values("market_cap_change_24h", ascending=False).head(20)
            sector_fig = px.bar(
                sector_top,
                x="market_cap_change_24h",
                y="name",
                orientation="h",
                color="market_cap_change_24h",
                color_continuous_scale=["#1e3a8a", "#2563eb", "#38bdf8", "#bae6fd"],
            )
            apply_plotly_style(sector_fig, title="Répartition sectorielle — variation 24 h des catégories (%)", x_title="Variation 24 h (%)", y_title="Catégorie", legend_below=False)
            sector_fig.update_layout(showlegend=False, yaxis=dict(autorange="reversed"), coloraxis_colorbar=dict(title=dict(text="Var. 24 h (%)", font=dict(color="#cbd5e1")), tickfont=dict(color="#cbd5e1")))
            st.plotly_chart(sector_fig, width="stretch", config=PLOTLY_CONFIG)
            with st.expander("ℹ️ Méthode et limites de la répartition sectorielle", expanded=False):
                st.markdown(
                    """
                    - **Comment c'est construit** : CoinGecko maintient un référentiel de catégories. Chaque actif est tagué
                      par leur équipe (DeFi, Layer 2, AI Tokens, etc.). L'agrégation se fait sur l'ensemble des actifs d'une catégorie.
                    - **Recoupements** : un actif peut appartenir à plusieurs catégories (par exemple `Ethereum` est dans
                      « Layer 1 » **et** « Smart Contract Platform »). La somme des capitalisations de catégories peut donc dépasser
                      la capitalisation totale crypto — ce n'est pas une partition, c'est un classement multi-étiquettes.
                    - **Top 20 affiché** : variation 24 h la plus positive en tête (filtré pour exclure les catégories trop petites).
                    - **Pour aller plus loin** : on peut filtrer par catégorie dans l'onglet *Marché* via la cartographie paramétrable.
                    """
                )
    except Exception as exc:
        st.warning(f"Catégories indisponibles : {exc}")

with tab_news:
    st.subheader("Actualités & Réglementation")
    news_query = st.text_input(
        "Filtrer les articles",
        placeholder="Ex. ETF, MiCA, SEC, stablecoin, AMF, BCE…",
        help="Filtrage texte (insensible à la casse) sur titre, résumé et source.",
    )
    try:
        news = get_news()
        if news.empty:
            st.info("Aucun article disponible pour le moment.")
        else:
            visible = news[news.apply(article_matches, axis=1, query=news_query)].head(40)
            for _, row in visible.iterrows():
                summary = str(row.get("summary", ""))
                summary_short = summary[:380] + ("…" if len(summary) > 380 else "")
                st.markdown(
                    f"""
                    <div class="co-news">
                      <a href="{row['link']}" target="_blank">{row['title']}</a>
                      <div class="meta">{row['source']} — {row['published']}</div>
                      <div style="margin-top: 0.4rem; color: var(--co-text);">{summary_short}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    except Exception as exc:
        st.warning(f"Flux RSS indisponibles : {exc}")

with tab_method:
    st.subheader("Méthode, sources et limites")
    with st.expander("🎯 Vision produit — aller au-delà de CoinGecko & focus stablecoins", expanded=False):
        st.markdown(
            """
            **CoinGecko** excelle comme référentiel grand public (prix, capi, métadonnées). Pour être *plus puissant*,
            CoCrypto doit **croiser des sources**, **documenter la méthode**, et **répondre à des questions de risque**
            que CoinGecko ne traite pas nativement — surtout sur les **stablecoins** (peg, réserves, chaînes, concentration).

            **Axes possibles (roadmap)** :
            - **Données & couverture** : agréger Dune / Arkham / Nansen (flux on-chain), CoinMetrics, Glassnode, TVL DefiLlama,
              open interest & funding (exchanges), ETF flows, carnets d’ordres (si abonnement).
            - **Qualité** : base locale (DuckDB), jobs planifiés, SLA, alerting peg / capi, historique non tronqué, audit des gaps.
            - **Stablecoins** : panel de stress (écart peg, volatilité implicite, corrélation USDT–USDC), alertes « depeg »,
              répartition par *peg mechanism* / chaîne, **bridged vs native supply**, liste des réserves attestées (liens PDF),
              courbe *stable dominance* vs risk-on, **MIM + crvusd + GHO** dans le suivi peg.
            - **Risque & conformité** : scoring MiCA/SEC read-through, tagging actualités + extraction entités (régulateur, actif).
            - **UX pro** : watchlists, exports CSV/PDF planifiés, thèmes sauvegardés, comparaison multi-stable sur une grille.
            - **Gouvernance** : taxonomies versionnées, changelog des définitions (cycles, flux proxy), reproducibilité des graphiques.

            *Objectif honnête* : ne pas « battre » CoinGecko sur le catalogue d’actifs, mais **dépasser** sur **l’analyse multi-sources,
            la transparence méthodologique et le sujet stablecoin / risque** — là où un terminal crypto apporte de la valeur.
            """
        )
    st.markdown(
        """
        ### Sources de données
        - **CoinGecko (public API)** — cours, capitalisations, volumes, offre, catégories, métadonnées riches (origine, communauté, GitHub).
        - **DefiLlama (`stablecoins.llama.fi`)** — capitalisations, mécanismes, chaînes, historique des stablecoins.
        - **Yahoo Finance (via `yfinance`)** — benchmarks (`GLD`, `BLOK`) et suivi du peg des stablecoins (`USDT-USD`, `USDC-USD`, …).
        - **Flux RSS publics** — CoinDesk, Cointelegraph, Bitcoin Magazine, SEC, ESMA.

        Tout est gratuit, sans clé API. CoinGecko applique un plafond de requêtes : un message d'erreur 429
        peut apparaître temporairement, il suffit de rafraîchir quelques secondes plus tard.

        ### Pourquoi les VL ne sont pas affichées comme une donnée native crypto
        Une **VL** (valeur liquidative) est calculée pour un fonds, un ETF, un ETP ou un produit structuré. Bitcoin,
        Ethereum ou Solana n'ont pas de VL : ce sont des actifs au cours de marché. Pour afficher des VL pertinentes,
        il faut cibler des véhicules précis (ETF spot BTC, ETP européens, fonds crypto régulés). Ces données sont
        publiées par les **émetteurs**, les **places de cotation** ou des **fournisseurs payants** (Refinitiv, Bloomberg, Morningstar).
        Une intégration sérieuse nécessite donc soit un abonnement, soit la mise en place d'un connecteur dédié
        vers les pages réglementaires de chaque émetteur.

        ### Comment maximiser l'information temps réel sur les montants
        Le MVP expose déjà : cours spot, capitalisation, volume 24 h, plus haut/plus bas 24 h, ATH/ATL, FDV, stock circulant,
        stock total, stock max, parts de marché, perfs multi-horizon.

        Pour aller plus loin et viser une vraie expérience « terminal » :
        - **WebSockets** des grands exchanges (Binance, Coinbase, Kraken) pour le tick par tick.
        - **APIs on-chain** (Blockchair, Mempool.space, Etherscan, Glassnode, CoinMetrics) pour hashrate, frais, transactions.
        - **DefiLlama** pour TVL DeFi et flux de stablecoins.
        - **Open interest, funding rates** sur les exchanges de dérivés.
        - **Flux ETF** (Farside, Bloomberg) pour les ETF spot BTC/ETH.

        ### Benchmarks via proxy — pourquoi et avec quelles réserves
        - **Or** → ETF **GLD** : adossé physiquement à l'or, très liquide, prix coté sans frais cachés majeurs.
        - **MSCI ACWI IMI Blockchain Economy Index** → ETF **BLOK** : indice **sous licence** non redistribuable
          gratuitement, donc on utilise un ETF thématique blockchain comme proxy. Compositions et pondérations
          ne sont pas identiques à l'indice MSCI : la performance affichée est **indicative**.
        - Pour la production, prévoir un connecteur licencié MSCI ou un fournisseur d'indices financiers.

        ### Cycles bull / bear / transition — modèle assumé simple
        Définition utilisée :
        - *Bull* : cours > SMA longue **et** momentum > 0.
        - *Bear* : cours < SMA longue **et** momentum < 0.
        - *Transition* : signal mixte.

        La fenêtre **SMA** est plafonnée à 200 jours, le **momentum** à 90 jours, les deux s'adaptent à la période sélectionnée.
        Ce modèle est volontairement basique, parfaitement reproductible et **non prédictif**. Pour une version
        professionnelle, il faudra figer : seuils, fenêtres, sources, pondérations, traitement des stablecoins,
        gestion des données manquantes et procédures de backtest documentées.

        ### Flux — proxy par variation de capitalisation
        Faute d'accès direct aux flux on-chain et exchange dans le MVP, on utilise la variation glissante 7 j de
        la capitalisation comme **approximation directionnelle** des flux nets. Cette mesure mélange effet de prix
        et effet de quantité ; à raffiner avec : entrées/sorties stablecoins, ETF flows nets, TVL DeFi, open interest.

        ### Minage / staking / émission
        Le pourcentage affiché en fiche détaillée est un **ratio offre circulante / plafond ou stock total**.
        - **PoW** (Bitcoin, Litecoin) : on peut le lire comme une progression d'émission/minage.
        - **PoS** (Ethereum, Solana, Cardano) : il s'agit d'une **distribution/émission**, pas d'un minage. Le concept
          réellement pertinent est le **staking ratio**, le nombre de validateurs, l'inflation, les unlocks et les rewards.
        - Pour pousser la granularité, ajouter : hashrate, difficulté, récompenses de bloc (PoW) ; staking ratio,
          inflation annualisée, queue de validateurs, unlocks programmés (PoS).

        ### Stablecoins
        Le MVP croise **DefiLlama** (capitalisations, mécanismes, chaînes) et **Yahoo Finance** (suivi de peg via
        les tickers USDT-USD, USDC-USD, etc.). On dérive : capitalisation totale, parts de marché du top 8, écart
        au peg en points de base, capitalisation totale glissante. En cas d'indisponibilité, repli automatique sur
        la catégorie *stablecoins* de CoinGecko.

        ### Architecture & roadmap
        Le fichier unique `app.py` est assumé pour démarrer vite. Étapes naturelles ensuite :
        1. Extraire `data_providers.py`, `models.py`, `ui.py`, `settings.py`.
        2. Ajouter une **base locale** (`SQLite` ou `DuckDB`) pour historiser et accélérer l'app.
        3. Ajouter une **couche jobs** (cron / Prefect) pour rafraîchir en tâche de fond.
        4. Migrer vers un **front React / TypeScript** lorsque le besoin produit dépassera Streamlit.
        5. Gouvernance taxonomique : qui valide les catégories, secteurs, pays, métadonnées.
        """
    )
