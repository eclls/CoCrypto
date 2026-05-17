"""Surveillance stablecoins, alertes peg et tableaux de risque."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

DEFAULT_DEPEG_THRESHOLD_PB = 50.0
DEFAULT_CONCENTRATION_WARN_PCT = 65.0


def peg_deviation_pb(price_usd: float | None) -> float | None:
    if price_usd is None or pd.isna(price_usd):
        return None
    return abs(float(price_usd) - 1.0) * 10_000


def build_stable_risk_panel(
    stables_df: pd.DataFrame,
    peg_history: pd.DataFrame,
    *,
    top_n: int = 15,
) -> pd.DataFrame:
    """Tableau de surveillance : capi, peg spot, écart 7j max, statut."""
    if stables_df.empty:
        return pd.DataFrame()

    base = stables_df.head(top_n).copy()
    sym_col = "Symbole" if "Symbole" in base.columns else "symbol"
    price_col = "Cours (USD)" if "Cours (USD)" in base.columns else "price"
    cap_col = "Circulation (USD)" if "Circulation (USD)" in base.columns else "market_cap"

    peg_max: dict[str, float] = {}
    peg_last: dict[str, float] = {}
    if not peg_history.empty and "Stablecoin" in peg_history.columns:
        for sym, grp in peg_history.groupby("Stablecoin"):
            prices = grp.sort_values("Date")["Prix (USD)"].dropna()
            if prices.empty:
                continue
            peg_last[str(sym)] = float(prices.iloc[-1])
            peg_max[str(sym)] = float((prices - 1.0).abs().max() * 10_000)

    total_cap = float(base[cap_col].sum()) if cap_col in base.columns else 0.0
    rows: list[dict[str, Any]] = []
    for _, r in base.iterrows():
        sym = str(r.get(sym_col, ""))
        spot = r.get(price_col)
        if spot is None or (isinstance(spot, float) and pd.isna(spot)):
            spot = peg_last.get(sym)
        dev_spot = peg_deviation_pb(spot) if spot is not None else None
        dev_7d = peg_max.get(sym)
        cap = r.get(cap_col)
        share = (float(cap) / total_cap * 100) if total_cap and cap and not pd.isna(cap) else None
        status = _risk_status(dev_spot, dev_7d, share)
        rows.append(
            {
                "Symbole": sym,
                "Circulation (USD)": cap,
                "Part marché stables (%)": share,
                "Peg spot (pb)": dev_spot,
                "Écart max 7j (pb)": dev_7d,
                "Statut": status,
            }
        )
    return pd.DataFrame(rows)


def _risk_status(dev_spot: float | None, dev_7d: float | None, share: float | None) -> str:
    if dev_spot is not None and dev_spot >= 100:
        return "🔴 Stress peg"
    if dev_7d is not None and dev_7d >= 75:
        return "🟠 Vigilance peg"
    if share is not None and share >= DEFAULT_CONCENTRATION_WARN_PCT:
        return "🟠 Concentration"
    if dev_spot is not None and dev_spot >= DEFAULT_DEPEG_THRESHOLD_PB:
        return "🟡 Écart modéré"
    return "🟢 OK"


def evaluate_depeg_alerts(
    peg_history: pd.DataFrame,
    *,
    threshold_pb: float = DEFAULT_DEPEG_THRESHOLD_PB,
) -> pd.DataFrame:
    """Alertes si le dernier peg ou le max 7j dépasse le seuil."""
    if peg_history.empty:
        return pd.DataFrame()
    alerts: list[dict[str, Any]] = []
    for sym, grp in peg_history.groupby("Stablecoin"):
        prices = grp.sort_values("Date")["Prix (USD)"].dropna()
        if prices.empty:
            continue
        last_pb = peg_deviation_pb(float(prices.iloc[-1]))
        max_pb = float((prices - 1.0).abs().max() * 10_000)
        if last_pb is not None and last_pb >= threshold_pb:
            alerts.append(
                {
                    "Symbole": sym,
                    "Type": "Peg spot",
                    "Écart (pb)": round(last_pb, 1),
                    "Seuil (pb)": threshold_pb,
                    "Message": f"{sym} : écart peg actuel {last_pb:.1f} pb (seuil {threshold_pb:.0f} pb).",
                }
            )
        elif max_pb >= threshold_pb:
            alerts.append(
                {
                    "Symbole": sym,
                    "Type": "Max 7j",
                    "Écart (pb)": round(max_pb, 1),
                    "Seuil (pb)": threshold_pb,
                    "Message": f"{sym} : écart max 7j {max_pb:.1f} pb (seuil {threshold_pb:.0f} pb).",
                }
            )
    return pd.DataFrame(alerts)


def stable_concentration_metrics(stables_df: pd.DataFrame) -> dict[str, float | None]:
    if stables_df.empty or "Circulation (USD)" not in stables_df.columns:
        return {"usdt_share_pct": None, "top3_share_pct": None, "hhi": None}
    caps = stables_df["Circulation (USD)"].fillna(0).astype(float)
    total = caps.sum()
    if total <= 0:
        return {"usdt_share_pct": None, "top3_share_pct": None, "hhi": None}
    shares = caps / total
    hhi = float((shares**2).sum() * 10_000)
    usdt_share = None
    if "Symbole" in stables_df.columns and "USDT" in stables_df["Symbole"].values:
        usdt_share = float(stables_df.loc[stables_df["Symbole"] == "USDT", "Circulation (USD)"].iloc[0] / total * 100)
    top3 = float(caps.nlargest(3).sum() / total * 100)
    return {"usdt_share_pct": usdt_share, "top3_share_pct": top3, "hhi": hhi}


def stress_scenario_copy(
    usdt_share_pct: float | None,
    global_stable_to_crypto_pct: float | None,
) -> str:
    """Texte indicatif pour scénario de stress (pédagogique)."""
    parts = []
    if usdt_share_pct is not None and usdt_share_pct > 55:
        parts.append(
            f"Concentration USDT élevée ({usdt_share_pct:.1f} % des stables) : un choc sur Tether "
            "propagerait mécaniquement le stress de peg et de liquidité."
        )
    if global_stable_to_crypto_pct is not None:
        parts.append(
            f"Les stablecoins représentent environ {global_stable_to_crypto_pct:.1f} % du marché crypto global "
            "(ratio indicatif) : une dépréciation large des stables pèserait sur le sentiment risk-on."
        )
    if not parts:
        return "Données insuffisantes pour un scénario chiffré — consulte le radar stablecoins."
    return " ".join(parts)
