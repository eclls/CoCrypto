# CoCrypto

> Agrégateur local et hébergeable de la sphère crypto : cours, capitalisations, volumes,
> comparaisons benchmarkées, cycles, flux, stablecoins, actualités et réglementation.

Le projet est livré sous la forme d'une application **Streamlit** monofichier (`app.py`)
qui s'alimente uniquement via des API publiques **sans clé** (CoinGecko, DefiLlama,
Yahoo Finance via `yfinance`, flux RSS).

## Fonctionnalités

- **Marché** : capitalisation globale, volume 24 h, tableau marché complet, cartographie
  paramétrable (treemap par capitalisation / volume / perf / âge / pourcentage miné).
- **Fiche crypto** : indicateurs clés, émission/minage, métadonnées riches, historique
  cours/capi/volume sur période sélectionnée, **export PDF prêt à diffuser**.
- **Comparaisons** : base 100, drawdown, corrélation glissante 30 j, distribution des
  rendements, benchmarks Or (proxy GLD) ou MSCI ACWI IMI Blockchain (proxy BLOK).
- **Flux & cycles** : modèle de cycle (Bull / Bear / Transition), flux proxy (variation
  glissante 7 j de capitalisation), répartition sectorielle par catégorie CoinGecko.
- **Stablecoins** : capitalisation totale DefiLlama, parts de marché, suivi du peg via
  Yahoo Finance, mini-courbes inline « Tendance capi » dans le tableau, et moteur de
  recherche dédié pour zoomer sur un stablecoin précis.
- **Actualités & Réglementation** : flux RSS CoinDesk, Cointelegraph, Bitcoin Magazine,
  SEC, ESMA, filtrables par mots-clés.
- **Méthode & limites** : documentation in-app des sources, modèles et hypothèses.

## Lancer en local

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows
# ou : source .venv/bin/activate # macOS / Linux

pip install -r requirements.txt
streamlit run app.py
```

L'app est ensuite accessible sur <http://localhost:8501>.

Aucune clé d'API n'est nécessaire. CoinGecko applique un plafond de requêtes : en cas
d'erreur 429, attendre quelques secondes et rafraîchir.

## Déployer sur Streamlit Community Cloud

L'app est conçue pour fonctionner directement sur
[Streamlit Community Cloud](https://share.streamlit.io) (hébergement gratuit, accessible
depuis n'importe quel navigateur, y compris mobile).

1. Ouvrir <https://share.streamlit.io> et se connecter avec le compte GitHub propriétaire
   de ce dépôt.
2. Cliquer sur **Create app** → **Deploy a public app from GitHub**.
3. Renseigner :
   - **Repository** : `eclls/CoCrypto`
   - **Branch** : `main`
   - **Main file path** : `app.py`
   - **App URL** : un sous-domaine `*.streamlit.app` libre (ex. `cocrypto-eclls`).
4. Cliquer sur **Deploy**. Le premier build prend 2 à 4 minutes.
5. Une fois déployée, l'URL publique fonctionne sur n'importe quel mobile / desktop.
   Ajouter l'URL en favori sur le téléphone pour un accès en un tap.

Aucun secret à configurer : toutes les sources sont publiques.

## Structure

```
.
├── app.py                # Application Streamlit monofichier
├── requirements.txt      # Dépendances Python
├── .streamlit/
│   └── config.toml       # Thème sombre CoCrypto
├── README.md
└── .gitignore
```

## Limitations connues

- Granularité limitée par les API publiques (résolution journalière au-delà de 90 jours
  pour CoinGecko, daily pour DefiLlama).
- Les benchmarks Or / MSCI ACWI IMI Blockchain Economy sont des **proxys** via ETF
  (GLD et BLOK) car les indices originaux sont sous licence.
- Les flux sont approximés par la variation glissante de capitalisation (proxy directionnel
  faute d'accès direct aux flux on-chain / exchange / ETF).

Voir l'onglet **Méthode & limites** dans l'app pour le détail complet.
