"""Composants Streamlit — cadre réglementaire V2–V4."""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

import regulatory_data as regdata


def render_obligations_section(iso_a3: str, country_name: str) -> None:
    st.markdown("#### Grille d'obligations (V2)")
    ob = regdata.obligations_for_iso(iso_a3)
    if ob.empty:
        st.caption("Aucune obligation structurée pour cette juridiction — enrichir le fichier d'obligations.")
        return
    show = ob[
        ["obligation_label_fr", "status_label", "effective_date", "source_label", "notes_fr"]
    ].copy()
    show["effective_date"] = pd.to_datetime(show["effective_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    show = show.rename(
        columns={
            "obligation_label_fr": "Obligation",
            "status_label": "Statut",
            "effective_date": "Date d'effet",
            "source_label": "Source",
            "notes_fr": "Notes",
        }
    )
    st.dataframe(show, width="stretch", hide_index=True)


def render_timeline_section(iso_a3: str) -> None:
    st.markdown("#### Chronologie réglementaire (V2)")
    events = regdata.timeline_for_iso(iso_a3)
    if not events:
        st.caption("Aucun jalons horodatés pour cette zone.")
        return
    for ev in events[:12]:
        st.markdown(
            f"- **{ev.get('date', '')}** — {ev.get('title', '')} "
            f"({ev.get('status', '')}) · [{ev.get('source_label', 'Source')}]({ev.get('source_url', '#')})"
        )


def render_citations_section(iso_a3: str) -> None:
    st.markdown("#### Textes & références citables (V3)")
    cites = regdata.citations_for_iso(iso_a3)
    if not cites:
        st.caption("Pas encore de références primaires indexées pour ce pays.")
        return
    for c in cites:
        st.markdown(
            f"**{c.get('label', '')}** — *{c.get('instrument', '')}* "
            f"({c.get('article', '')})  \n"
            f"{c.get('summary_fr', '')}  \n"
            f"[Lien officiel]({c.get('url', '#')})"
        )


def render_readthrough_section(iso_a3: str, country_name: str) -> None:
    rt = regdata.load_readthrough()
    st.markdown(f"### Read-through produit — {country_name} (V4)")
    st.caption(rt.get("disclaimer_fr", ""))
    product_types = rt.get("product_types") or []
    if not product_types:
        st.info("Configuration read-through indisponible.")
        return
    labels = {p["id"]: p["label_fr"] for p in product_types}
    product_id = st.selectbox(
        "Type de produit / service",
        options=list(labels.keys()),
        format_func=lambda k: labels[k],
        key=f"readthrough_product_{iso_a3}",
    )
    block = regdata.readthrough_for_product(iso_a3, product_id)
    if not block:
        jkey = regdata.resolve_jurisdiction_key(iso_a3, rt)
        st.warning(
            f"Pas de checklist détaillée pour **{labels[product_id]}** dans la juridiction "
            f"({jkey}). Utiliser l'UE ou USA comme référence la plus proche."
        )
        return
    perimeter = block.get("perimeter", "n/a")
    st.markdown(f"**Périmètre réglementaire estimé :** `{perimeter}` — {block.get('summary_fr', '')}")
    checklist = block.get("checklist") or []
    if not checklist:
        st.caption("Checklist vide pour cette combinaison.")
        return
    answers: dict[str, bool] = {}
    for item in checklist:
        qid = str(item.get("id", item.get("question", "")))
        required = bool(item.get("required", False))
        label = f"{'[Requis] ' if required else ''}{item.get('question', '')}"
        answers[qid] = st.checkbox(
            label,
            key=f"rt_{iso_a3}_{product_id}_{qid}",
            help=item.get("hint", ""),
        )
    done = sum(answers.values())
    total = len(checklist)
    req_ids = [str(i.get("id")) for i in checklist if i.get("required")]
    req_ok = all(answers.get(rid, False) for rid in req_ids)
    st.progress(done / total if total else 0.0, text=f"{done}/{total} points validés (indicatif)")
    if req_ok and done == total:
        st.success("Tous les points requis sont cochés — revue juridique externe recommandée avant lancement.")
    elif not req_ok:
        st.warning("Des points **requis** ne sont pas encore cochés.")


def render_cadre_juridique_page(atlas_df: pd.DataFrame) -> None:
    st.markdown(
        "**Cadre juridique structuré** : obligations par thème (V2), chronologie (V2), "
        "références citables (V3). Contenu pédagogique avec liens officiels."
    )
    names = atlas_df["name_fr"].tolist()
    pick = st.selectbox("Juridiction", names, key="cadre_country_pick")
    row = atlas_df.loc[atlas_df["name_fr"] == pick].iloc[0]
    iso = str(row["iso_a3"])
    render_obligations_section(iso, pick)
    st.divider()
    render_timeline_section(iso)
    st.divider()
    render_citations_section(iso)


def render_readthrough_page(atlas_df: pd.DataFrame) -> None:
    names = atlas_df["name_fr"].tolist()
    pick = st.selectbox("Juridiction — read-through", names, key="readthrough_country_pick")
    row = atlas_df.loc[atlas_df["name_fr"] == pick].iloc[0]
    render_readthrough_section(str(row["iso_a3"]), pick)
