"""Composants Streamlit — suivi & surveillance."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import regulatory_data as regdata
import surveillance_logic as surv


def render_surveillance_tab(
    *,
    get_stablecoins_defillama,
    get_stable_peg_history,
    get_news_regulation,
    global_data: dict,
    apply_plotly_style,
    plotly_config: dict,
) -> None:
    st.subheader("Suivi & surveillance")
    st.caption(
        "Radar stablecoins, alertes de peg configurables et veille réglementaire personnalisée. "
        "Les seuils sont indicatifs — pas d'envoi d'email dans cette version."
    )

    peg_days = st.slider("Historique peg (jours)", 3, 45, 7, key="surv_peg_days")
    threshold_pb = st.number_input(
        "Seuil d'alerte peg (points de base)",
        min_value=10.0,
        max_value=500.0,
        value=surv.DEFAULT_DEPEG_THRESHOLD_PB,
        step=5.0,
        key="surv_depeg_threshold",
        help="1 pb = 0,01 % d'écart au peg 1 USD. 50 pb = 0,50 %.",
    )

    df_stables = get_stablecoins_defillama()
    peg_hist = get_stable_peg_history(days=int(peg_days))

    st.markdown("#### Radar stablecoins")
    if df_stables.empty:
        st.warning("Données DefiLlama indisponibles — radar stablecoins non calculable.")
    else:
        panel = surv.build_stable_risk_panel(df_stables, peg_hist, top_n=15)
        if not panel.empty:
            st.dataframe(panel, width="stretch", hide_index=True)
            stress_count = panel["Statut"].astype(str).str.contains("Stress|Vigilance").sum()
            if stress_count:
                st.error(f"{stress_count} stablecoin(s) en statut stress ou vigilance sur le panel top 15.")
        conc = surv.stable_concentration_metrics(df_stables)
        c1, c2, c3 = st.columns(3)
        c1.metric("Part USDT (stables)", f"{conc['usdt_share_pct']:.1f} %" if conc["usdt_share_pct"] else "n/a")
        c2.metric("Top 3 (stables)", f"{conc['top3_share_pct']:.1f} %" if conc["top3_share_pct"] else "n/a")
        c3.metric("HHI (×10⁴)", f"{conc['hhi']:.0f}" if conc["hhi"] else "n/a", help="Indice de concentration ; plus c'est élevé, plus le marché est concentré.")

        if not peg_hist.empty:
            last = peg_hist.sort_values("Date").groupby("Stablecoin").tail(1)
            last["Écart (pb)"] = (last["Prix (USD)"] - 1.0).abs() * 10_000
            fig = px.bar(
                last.sort_values("Écart (pb)", ascending=True),
                x="Écart (pb)",
                y="Stablecoin",
                orientation="h",
                color="Écart (pb)",
                color_continuous_scale=["#4ade80", "#fbbf24", "#f87171"],
            )
            apply_plotly_style(fig, title=f"Écart au peg 1 USD — dernier point ({peg_days} j)", x_title="Points de base")
            fig.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig, width="stretch", config=plotly_config)

    st.markdown("#### Alertes peg")
    alerts = surv.evaluate_depeg_alerts(peg_hist, threshold_pb=float(threshold_pb))
    if alerts.empty:
        st.success(f"Aucune alerte au-dessus de {threshold_pb:.0f} pb sur la période.")
    else:
        for _, a in alerts.iterrows():
            st.warning(a["Message"])

    st.markdown("#### Scénario de stress (indicatif)")
    gmc = global_data.get("total_market_cap", {}).get("usd") if global_data else None
    stable_total = float(df_stables["Circulation (USD)"].sum()) if not df_stables.empty else None
    ratio = (stable_total / float(gmc) * 100) if stable_total and gmc else None
    conc = surv.stable_concentration_metrics(df_stables) if not df_stables.empty else {}
    st.info(surv.stress_scenario_copy(conc.get("usdt_share_pct"), ratio))

    st.divider()
    st.markdown("#### Veille réglementaire personnalisée")
    atlas_iso_options = st.multiselect(
        "Juridictions suivies (codes ISO)",
        ["EU", "FRA", "USA", "GBR", "DEU", "SGP", "JPN", "CHE"],
        default=["EU", "FRA", "USA"],
        key="surv_reg_jurisdictions",
    )
    theme_options = list(regdata.REGULATORY_NEWS_THEMES.keys())
    themes_pick = st.multiselect(
        "Thèmes",
        theme_options,
        default=["Stablecoins", "Licences & agréments", "Enforcement / sanctions"],
        key="surv_reg_themes",
    )
    try:
        reg_news = get_news_regulation()
        watched = regdata.filter_regulatory_watch(
            reg_news,
            jurisdictions=atlas_iso_options,
            themes=themes_pick,
            min_score=1 if (atlas_iso_options or themes_pick) else 0,
        )
        if watched.empty:
            st.info("Aucun article ne correspond aux filtres — élargir juridictions ou thèmes.")
        else:
            st.caption(f"{len(watched)} article(s) pertinents (score ≥ 1).")
            for _, row in watched.head(25).iterrows():
                tags = row.get("reg_tags", "")
                st.markdown(
                    f"**[{row['title']}]({row['link']})**  \n"
                    f"{row['source']} — {row['published']} · score {row.get('reg_score', 0)}  \n"
                    f"*Tags : {tags or '—'}*"
                )
    except Exception as exc:
        st.warning(f"Veille réglementaire indisponible : {exc}")
