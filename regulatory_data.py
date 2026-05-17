"""Données et logique réglementaire CoCrypto (V2 obligations → V4 read-through)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

OBLIGATION_STATUS_LABELS: dict[str, str] = {
    "absent": "Absent",
    "proposed": "Proposé / en discussion",
    "adopted": "Adopté (pas encore applicable)",
    "in_force": "En vigueur",
    "sandbox": "Bac à sable / pilote",
}

REGULATORY_NEWS_THEMES: dict[str, tuple[str, ...]] = {
    "Enforcement / sanctions": (
        "enforcement",
        "sanction",
        "fine",
        "penalty",
        "lawsuit",
        "charged",
        "violation",
        "amende",
        "sanction",
        "poursuite",
    ),
    "Licences & agréments": (
        "license",
        "licence",
        "authorisation",
        "authorization",
        "register",
        "agrément",
        "approval",
        "mica",
        "casp",
        "psan",
    ),
    "Stablecoins": (
        "stablecoin",
        "stable coin",
        "usdt",
        "usdc",
        "issuer",
        "reserve",
        "peg",
        "art ",
        "e-money token",
    ),
    "CBDC & monnaie digitale": (
        "cbdc",
        "digital euro",
        "digital pound",
        "central bank digital",
        "monnaie digitale",
        "e-rupee",
        "digital yuan",
    ),
    "Consultations & projets": (
        "consultation",
        "proposal",
        "draft",
        "bill",
        "projet de loi",
        "public comment",
        "consultation publique",
    ),
}


def _read_json(name: str) -> Any:
    path = DATA_DIR / name
    if not path.exists():
        return {} if name.endswith(".json") else []
    return json.loads(path.read_text(encoding="utf-8"))


def load_obligations() -> pd.DataFrame:
    path = DATA_DIR / "regulatory_obligations.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return df
    df["status_label"] = df["status"].map(OBLIGATION_STATUS_LABELS).fillna(df["status"])
    df["effective_date"] = pd.to_datetime(df["effective_date"], errors="coerce")
    return df


def load_timeline() -> list[dict[str, Any]]:
    raw = _read_json("regulatory_timeline.json")
    return raw if isinstance(raw, list) else []


def load_citations() -> dict[str, list[dict[str, Any]]]:
    raw = _read_json("regulatory_citations.json")
    return raw if isinstance(raw, dict) else {}


def load_readthrough() -> dict[str, Any]:
    raw = _read_json("regulatory_readthrough.json")
    return raw if isinstance(raw, dict) else {}


def resolve_jurisdiction_key(iso_a3: str, readthrough: dict[str, Any] | None = None) -> str:
    rt = readthrough or load_readthrough()
    mapping = rt.get("iso_to_jurisdiction") or {}
    return str(mapping.get(iso_a3, iso_a3))


def obligations_for_iso(iso_a3: str, obligations: pd.DataFrame | None = None) -> pd.DataFrame:
    ob = obligations if obligations is not None else load_obligations()
    if ob.empty:
        return ob
    rt = load_readthrough()
    jkeys = {iso_a3, resolve_jurisdiction_key(iso_a3, rt)}
    return ob[ob["iso_a3"].isin(jkeys)].copy()


def timeline_for_iso(iso_a3: str, events: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    ev = events if events is not None else load_timeline()
    rt = load_readthrough()
    jkeys = {iso_a3, resolve_jurisdiction_key(iso_a3, rt)}
    out = [e for e in ev if e.get("iso_a3") in jkeys]
    return sorted(out, key=lambda x: x.get("date", ""), reverse=True)


def citations_for_iso(iso_a3: str, citations: dict[str, list] | None = None) -> list[dict[str, Any]]:
    cit = citations if citations is not None else load_citations()
    rt = load_readthrough()
    jkey = resolve_jurisdiction_key(iso_a3, rt)
    merged: list[dict[str, Any]] = []
    for key in (iso_a3, jkey, "EU"):
        merged.extend(cit.get(key, []))
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for c in merged:
        cid = c.get("id", c.get("label", ""))
        if cid in seen:
            continue
        seen.add(str(cid))
        unique.append(c)
    return unique


def readthrough_for_product(iso_a3: str, product_id: str) -> dict[str, Any] | None:
    rt = load_readthrough()
    jkey = resolve_jurisdiction_key(iso_a3, rt)
    jur = (rt.get("jurisdictions") or {}).get(jkey) or {}
    return jur.get(product_id)


def classify_regulatory_article(title: str, summary: str = "") -> list[str]:
    blob = f"{title} {summary}".lower()
    tags: list[str] = []
    for theme, keywords in REGULATORY_NEWS_THEMES.items():
        if any(kw in blob for kw in keywords):
            tags.append(theme)
    return tags


def score_article_relevance(row: pd.Series, *, jurisdictions: list[str], themes: list[str]) -> int:
    title = str(row.get("title", ""))
    summary = str(row.get("summary", ""))
    blob = f"{title} {summary}".lower()
    score = 0
    for iso in jurisdictions:
        if iso.lower() in blob:
            score += 2
    article_tags = classify_regulatory_article(title, summary)
    for th in themes:
        if th in article_tags:
            score += 3
    return score


def filter_regulatory_watch(
    news: pd.DataFrame,
    *,
    jurisdictions: list[str],
    themes: list[str],
    min_score: int = 1,
) -> pd.DataFrame:
    if news.empty:
        return news
    df = news.copy()
    df["reg_tags"] = df.apply(
        lambda r: ", ".join(classify_regulatory_article(str(r.get("title", "")), str(r.get("summary", "")))),
        axis=1,
    )
    df["reg_score"] = df.apply(
        lambda r: score_article_relevance(r, jurisdictions=jurisdictions, themes=themes),
        axis=1,
    )
    if jurisdictions or themes:
        df = df[df["reg_score"] >= min_score]
    return df.sort_values("reg_score", ascending=False)


def obligation_status_emoji(status: str) -> str:
    return {
        "in_force": "🟢",
        "sandbox": "🔵",
        "adopted": "🟡",
        "proposed": "🟠",
        "absent": "⚪",
    }.get(status, "⚫")
