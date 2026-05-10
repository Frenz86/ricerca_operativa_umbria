"""Dashboard Streamlit: Demo Prima/Dopo Ottimizzazione Trasporti Sanitari AUSL Umbria 1.
Avvia con: streamlit run app.py"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys, os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.synthetic_data import (
    build_nodes, build_carriers, generate_daily_requests,
    generate_dialysis_patients, haversine_km, ZONES, ZONE_NAMES,
    DISTRICTS, DISTRICT_CENTERS, HOSPITALS, DIALYSIS_CENTERS, MUNICIPALITIES
)
from models.strategic_allocation import solve_strategic, compute_carrier_zone_distances, get_baseline_assignment
from models.tactical_assignment import solve_tactical, simulate_baseline_assignment
from models.operational_dispatch import simulate_operational_day
from models.dialysis_routing import optimize_dialysis

# --- LOGIN ---
def check_password():
    def login_form():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("---")
            st.image("https://upload.wikimedia.org/wikipedia/it/thumb/4/47/Azienda_USL_Umbria_1.svg/1200px-Azienda_USL_Umbria_1.svg.png",
                     width=200) if False else None
            st.markdown("<h1 style='text-align: center; color: #2c3e50;'>AUSL Umbria 1</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: #7f8c8d;'>Sistema di Ottimizzazione Trasporti Sanitari</h3>", unsafe_allow_html=True)
            st.markdown("---")

            with st.form("login"):
                st.markdown("#### Accesso")
                username = st.text_input("Utente", placeholder="Inserisci nome utente")
                password = st.text_input("Password", type="password", placeholder="Inserisci password")
                submitted = st.form_submit_button("Accedi", use_container_width=True)

                if submitted:
                    if username == "umbria" and password == "password":
                        st.session_state["authenticated"] = True
                        st.rerun()
                    else:
                        st.error("Credenziali non valide. Riprova.")

            st.caption("Demo applicativa — utente: umbria / password: password")
            st.markdown("---")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login_form()
        return False
    return True

if not check_password():
    st.stop()

# Bottone logout nella sidebar
with st.sidebar:
    if st.button("🔒 Esci", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.markdown("---")

st.set_page_config(
    page_title="Ottimizzazione Trasporti - AUSL Umbria 1",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Cache pesanti ---
@st.cache_data
def run_all_models():
    np.random.seed(42)
    carriers = build_carriers()
    nodes = build_nodes()
    requests = generate_daily_requests(n_planned=55, n_urgent=12)
    patients = generate_dialysis_patients()

    district_centers = {
        "Alto Tevere": (43.40, 12.27), "Alto Chiascio": (43.30, 12.68),
        "Perugino": (43.08, 12.37), "Trasimeno": (43.05, 12.05),
        "Assisano": (43.04, 12.60), "Media Valle": (42.85, 12.43),
    }
    dist_cz = compute_carrier_zone_distances(carriers, ZONES, district_centers)

    # Strategico
    strategic = solve_strategic(carriers, ZONES, None, dist_cz)
    baseline_strategic = get_baseline_assignment(carriers, ZONES, dist_cz)

    # Tattico
    baseline_tactical = simulate_baseline_assignment(requests, carriers)
    optimized_tactical = solve_tactical(requests, carriers)

    # Operativo
    operational = simulate_operational_day(12)

    # Dialisi
    dialysis = optimize_dialysis(patients, carriers)

    return {
        "carriers": carriers, "nodes": nodes, "requests": requests, "patients": patients,
        "strategic": strategic, "baseline_strategic": baseline_strategic,
        "baseline_tactical": baseline_tactical, "optimized_tactical": optimized_tactical,
        "operational": operational, "dialysis": dialysis, "dist_cz": dist_cz,
    }

data = run_all_models()

# --- Sidebar ---
st.sidebar.title("🚑 AUSL Umbria 1")
st.sidebar.markdown("**Ottimizzazione Trasporti Sanitari Secondari**")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigazione", [
    "🏠 Cos'è questa App",
    "📊 Dashboard Principale",
    "🗺️ Mappa Territorio",
    "📋 Strategico (Livello 1)",
    "📅 Tattico (Livello 2)",
    "🚨 Operativo (Livello 3)",
    "🩺 Dialisi (Quick Win)",
    "📈 KPI & Confronto",
])

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
**Dati simulazione:**
- {len(data['carriers'])} vettori
- {len(data['nodes'])} nodi territoriali
- {len(data['requests'])} richieste/giorno
- {len(data['patients'])} pazienti dialisi
""")

# --- PAGINA: Cos'è questa App ---
if page == "🏠 Cos'è questa App":
    st.title("Ottimizzazione Trasporti Sanitari")
    st.markdown("## AUSL Umbria 1 — Sistema di Ricerca Operativa")

    st.markdown("---")

    st.markdown("""
    ### Il Problema

    L'AUSL Umbria 1 gestisce i **trasporti sanitari secondari** (dimissioni ospedaliere, trasferimenti tra strutture,
    consulenze specialistiche, trasporti dialisi) su un territorio di **4.298 km²** con **38 comuni** e **6 distretti**.

    Ogni giorno partono circa **70-80 richieste di trasporto**, gestite da oltre **24 associazioni di volontariato**
    (Croce Rossa, Misericordie, ANPAS) con convenzioni diverse tra loro.

    **Le criticità emerse dall'analisi dei dati 2024-2025:**

    - Il **15% dei trasporti** viene effettuato da vettori fuori territorio, generando km e costi inutili
    - Il **2% delle richieste** non viene evaso per mancanza di vettori disponibili
    - La gestione è **frammentata**: ogni distretto/ospedale contatta autonomamente i vettori
    - Esistono **24 tipi di contratti diversi** con tariffe disomogenee
    - Nessun coordinamento centrale per ottimizzare percorsi e risorse
    """)

    st.markdown("---")

    st.markdown("""
    ### La Soluzione

    Questa applicazione implementa un **sistema di Linear Programming (LP)** su 3 livelli che ottimizza
    l'assegnazione dei trasporti sanitari attraverso modelli matematici di ricerca operativa:

    | Livello | Quando | Cosa fa |
    |---------|--------|---------|
    | **1. Strategico** | Ogni trimestre | Assegna ogni vettore alle zone territoriali dove è più efficiente |
    | **2. Tattico** | Ogni notte | Assegna i trasporti pianificati del giorno dopo al vettore ottimale |
    | **3. Operativo** | In tempo reale | Gestisce le richieste urgenti dispatchando il vettore più vicino |

    Inoltre, un **sotto-modello dedicato alla dialisi** ottimizza le rotte ricorrenti dei pazienti
    dializzati (che percorrono lo stesso tragitto 2-3 volte a settimana).
    """)

    st.markdown("---")

    st.markdown("""
    ### Come Usare Questa Demo

    Usa il menu di navigazione sulla **sidebar sinistra** per esplorare:

    1. **Dashboard Principale** — Il confronto visivo prima/dopo con tutti i KPI principali
    2. **Mappa Territorio** — La mappa interattiva con ospedali, vettori, centri dialisi
    3. **Strategico** — Il modello LP di livello 1: come vengono allocati i vettori alle zone
    4. **Tattico** — Il modello LP di livello 2: assegnamento giornaliero delle richieste
    5. **Operativo** — Il dispatch in tempo reale per le urgenze
    6. **Dialisi** — Il quick win con più impatto immediato
    7. **KPI & Confronto** — Tabella riepilogativa completa e roadmap di implementazione
    """)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### I Dati

        I numeri reali dall'Excel 2025:
        - **8.052** trasporti ospedalieri
        - **8.924** trasporti distrettuali
        - **487.991 km** ordinari ospedalieri
        - **688.235 km** ordinari distrettuali
        - **362.987 km** dialisi (7.007 sedute)
        """)
    with col2:
        st.markdown("""
        ### I Risultati Attesi

        Con l'ottimizzazione LP:
        - **-15% km** annuali (~232.000 km risparmiati)
        - Fuori territorio da **15% a <3%**
        - Non evase da **2% a <0.5%**
        - Risparmio **230-350k euro/anno**
        """)
    with col3:
        st.markdown("""
        ### La Tecnologia

        I modelli sono risolti con:
        - **PuLP + CBC** (solver gratuito)
        - **Python 3.13**
        - Modelli MIP (Mixed-Integer Programming)
        - Euristica greedy per il real-time
        """)

    st.markdown("---")
    st.info("Seleziona **'Dashboard Principale'** dal menu a sinistra per vedere il confronto prima/dopo.")


# --- PAGINA: Dashboard Principale ---
if page == "📊 Dashboard Principale":
    st.title("Dashboard Trasporti Sanitari - Confronto Prima/Dopo")
    st.markdown("### AUSL Umbria 1 | Sistema di Ottimizzazione LP")

    st.info("Questa pagina mostra il confronto tra la gestione attuale dei trasporti (AS-IS) e quella ottimizzata dal sistema di LP (TO-BE). Le tre colonne riassumono i numeri chiave: i km percorsi, le percentuali di errori, e i risparmi stimati.")

    # Metriche principali in 3 colonne
    col1, col2, col3 = st.columns(3)

    bt = data["baseline_tactical"]
    ot = data["optimized_tactical"]
    km_saved = bt["total_km"] - ot["total_km"]
    km_saved_pct = (km_saved / bt["total_km"] * 100) if bt["total_km"] > 0 else 0

    with col1:
        st.markdown("#### ❌ SITUAZIONE ATTUALE (AS-IS)")
        st.caption("Come funzionano oggi i trasporti: ogni distretto chiama i vettori autonomamente, senza coordinamento centrale.")
        st.metric("km/giorno", f"{bt['total_km']:,.0f}")
        st.metric("% Fuori Territorio", f"{bt['pct_out_territory']:.1f}%")
        st.metric("Richieste Non Evase", f"{bt['n_unassigned']}")
        st.metric("km/giorno Dialisi (stimato)", f"{data['dialysis']['weekly_km_baseline'] // 5:,}")

    with col2:
        st.markdown("#### ✅ DOPO OTTIMAZIONE (TO-BE)")
        st.caption("Con il sistema LP: una Centrale Unica assegna ogni trasporto al vettore più vicino ed efficiente.")
        st.metric("km/giorno", f"{ot['total_km']:,.0f}", f"-{km_saved:,.0f}")
        st.metric("% Fuori Territorio", f"{ot['pct_out_territory']:.1f}%",
                   f"-{bt['pct_out_territory'] - ot['pct_out_territory']:.1f}%")
        st.metric("Richieste Non Evase", f"{ot['n_unassigned']}",
                   f"-{bt['n_unassigned'] - ot['n_unassigned']}")
        st.metric("km/giorno Dialisi (ottimizzato)", f"{data['dialysis']['weekly_km_optimized'] // 5:,}")

    with col3:
        st.markdown("#### 💰 RISPARMI STIMATI")
        st.caption("Differenza tra situazione attuale e ottimizzata, annualizzata su 260 giorni lavorativi.")
        annual_km_saved = km_saved * 260
        dialysis_annual_saved = data["dialysis"]["annual_savings_km"]
        total_annual_saved = annual_km_saved + dialysis_annual_saved
        euro_saved = total_annual_saved * 1.20  # ~1.20 euro/km medio

        st.metric("km risparmiati/giorno", f"{km_saved:,.0f} ({km_saved_pct:.1f}%)")
        st.metric("km risparmiati/anno", f"{total_annual_saved:,.0f}")
        st.metric("Risparmio economico/anno", f"{euro_saved:,.0f} euro",
                   f"~{euro_saved/1000:.0f}k euro")
        st.metric("Pazienti serviti meglio", f"+{bt['n_unassigned'] - ot['n_unassigned']}/giorno")

    st.markdown("---")

    # Grafico confronto km per distretto
    st.markdown("### Confronto km per Distretto (una giornata tipo)")
    st.caption("Le barre rosse mostrano i km percorsi oggi in ogni distretto, quelle verdi i km dopo l'ottimizzazione. Un distretto con barre più corte significa meno strada percorsa = meno costi.")
    district_comparison = {}
    for a in bt["assignments"]:
        d = a.get("district", "N/D")
        district_comparison.setdefault(d, {"baseline": 0, "optimized": 0})
        district_comparison[d]["baseline"] += a.get("km", 0)
    for a in ot["assignments"]:
        d = a.get("district", "N/D")
        if d not in district_comparison:
            district_comparison.setdefault(d, {"baseline": 0, "optimized": 0})
        district_comparison[d]["optimized"] += a.get("km", 0)

    dist_names = sorted(district_comparison.keys())
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dist_names, y=[district_comparison[d]["baseline"] for d in dist_names],
                         name="AS-IS (Attuale)", marker_color="#e74c3c"))
    fig.add_trace(go.Bar(x=dist_names, y=[district_comparison[d]["optimized"] for d in dist_names],
                         name="TO-BE (Ottimizzato)", marker_color="#27ae60"))
    fig.update_layout(barmode="group", height=400,
                      title="km per Distretto: Prima vs Dopo Ottimizzazione",
                      yaxis_title="km totali")
    st.plotly_chart(fig, use_container_width=True)

    # Colonne con grafici
    col_left, col_right = st.columns(2)

    with col_left:
        # Fuori territorio per federazione
        st.markdown("### Fuori Territorio per Federazione")
        st.caption("Un trasporto 'fuori territorio' significa che l'ambulanza ha dovuto percorrere molti km in più perché nella zona non c'era un vettore disponibile. Le barre verdi (quasi zero) mostrano che l'ottimizzazione risolve questo problema.")
        fed_oos_base = {}
        for a in bt["assignments"]:
            if a.get("is_out_of_territory"):
                fed_oos_base[a.get("federation", "N/D")] = fed_oos_base.get(a.get("federation", "N/D"), 0) + 1
        fed_oos_opt = {}
        for a in ot["assignments"]:
            if a.get("is_out_of_territory"):
                fed_oos_opt[a.get("federation", "N/D")] = fed_oos_opt.get(a.get("federation", "N/D"), 0) + 1

        feds = sorted(set(list(fed_oos_base.keys()) + list(fed_oos_opt.keys())))
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=feds, y=[fed_oos_base.get(f, 0) for f in feds],
                              name="AS-IS", marker_color="#e74c3c"))
        fig2.add_trace(go.Bar(x=feds, y=[fed_oos_opt.get(f, 0) for f in feds],
                              name="TO-BE", marker_color="#27ae60"))
        fig2.update_layout(barmode="group", height=350, title="Viaggi Fuori Territorio")
        st.plotly_chart(fig2, use_container_width=True)

    with col_right:
        # Distribuzione carico vettori
        st.markdown("### Carico Vettori")
        st.caption("Ogni barra rappresenta quante richieste vengono assegnate a ciascun vettore. Nella situazione attuale (rosso) il carico è sbilanciato: alcuni vettori sono sovraccarichi, altri sottoutilizzati. Dopo l'ottimizzazione (verde) il lavoro è distribuito meglio.")
        carrier_load_base = {}
        for a in bt["assignments"]:
            cn = a.get("carrier_name", "N/D")
            carrier_load_base[cn] = carrier_load_base.get(cn, 0) + 1
        carrier_load_opt = {}
        for a in ot["assignments"]:
            cn = a.get("carrier_name", "N/D")
            carrier_load_opt[cn] = carrier_load_opt.get(cn, 0) + 1

        top_carriers = sorted(carrier_load_opt, key=carrier_load_opt.get, reverse=True)[:10]
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=top_carriers,
                              y=[carrier_load_base.get(c, 0) for c in top_carriers],
                              name="AS-IS", marker_color="#e74c3c"))
        fig3.add_trace(go.Bar(x=top_carriers,
                              y=[carrier_load_opt.get(c, 0) for c in top_carriers],
                              name="TO-BE", marker_color="#27ae60"))
        fig3.update_layout(barmode="group", height=350, title="Viaggi per Vettore (Top 10)",
                           xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)


# --- PAGINA: Mappa Territorio ---
elif page == "🗺️ Mappa Territorio":
    st.title("Mappa Territoriale - AUSL Umbria 1")
    st.markdown("### Nodi, Vettori e Zone di Servizio")

    st.info("Questa mappa mostra il territorio coperto dall'AUSL Umbria 1. Puoi zoomare e trascinare con il mouse. Passa il cursore su ogni punto per vedere i dettagli.")

    st.markdown("""
    **Cosa rappresentano i punti sulla mappa:**
    - **Cerchi colorati** = Comuni (i 38 comuni del territorio, colorati per distretto di appartenenza)
    - **Croci rosse grandi** = Ospedali e Presidi (da dove partono o arrivano i pazienti)
    - **Punti blu** = Centri Dialisi (dove i pazienti vanno 2-3 volte a settimana)
    - **Triangoli** = Basi dei vettori (le sedi delle 24+ associazioni di volontariato con le loro ambulanze)
    """)

    nodes = data["nodes"]
    carriers = data["carriers"]

    colors_district = {
        "Alto Tevere": "#e74c3c", "Alto Chiascio": "#3498db", "Perugino": "#2ecc71",
        "Trasimeno": "#f39c12", "Assisano": "#9b59b6", "Media Valle": "#1abc9c",
    }

    fig = go.Figure()

    # Comuni
    for nid, n in nodes.items():
        if n["type"] == "municipality":
            fig.add_trace(go.Scattermapbox(
                lat=[n["lat"]], lon=[n["lon"]],
                mode="markers",
                marker=dict(size=8, color=colors_district.get(n["district"], "#95a5a6")),
                text=f"{n['name']}<br>Distretto: {n['district']}<br>Pop: {n.get('pop', 'N/D'):,}",
                name="", hovertemplate="%{text}<extra></extra>",
            ))

    # Ospedali
    for nid, n in nodes.items():
        if n["type"] == "hospital":
            fig.add_trace(go.Scattermapbox(
                lat=[n["lat"]], lon=[n["lon"]],
                mode="markers",
                marker=dict(size=15, color="red", symbol="hospital"),
                text=f"🏥 {n['name']}<br>Distretto: {n['district']}",
                name="", hovertemplate="%{text}<extra></extra>",
            ))

    # Centri dialisi
    for nid, n in nodes.items():
        if n["type"] == "dialysis_center":
            fig.add_trace(go.Scattermapbox(
                lat=[n["lat"]], lon=[n["lon"]],
                mode="markers",
                marker=dict(size=12, color="blue", symbol="circle"),
                text=f"🩺 {n['name']}",
                name="", hovertemplate="%{text}<extra></extra>",
            ))

    # Basi vettori
    for c in carriers:
        fig.add_trace(go.Scattermapbox(
            lat=[c["base_lat"]], lon=[c["base_lon"]],
            mode="markers",
            marker=dict(size=10, color=colors_district.get(c["base_district"], "#95a5a6"),
                        symbol="triangle-up"),
            text=f"🚐 {c['name']}<br>Fed: {c['federation']}<br>Amb: {c['n_ambulance']}, Attr: {c['n_attrezzato']}",
            name="", hovertemplate="%{text}<extra></extra>",
        ))

    fig.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=43.1, lon=12.4), zoom=8),
        height=650, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Legenda
    st.markdown("**Legenda:** 🔴 Ospedali | 🔵 Centri Dialisi | ▲ Basi Vettori | ● Comuni")
    cols = st.columns(6)
    for i, (dist, color) in enumerate(colors_district.items()):
        with cols[i]:
            st.markdown(f"<span style='color:{color}'>■</span> {dist}", unsafe_allow_html=True)


# --- PAGINA: Strategico ---
elif page == "📋 Strategico (Livello 1)":
    st.title("Livello 1: Allocazione Strategica Territorio")
    st.markdown("### Modello Transportation Problem (MIP) - Risolto Trimestralmente")

    st.info("Questo è il primo dei tre livelli del sistema. Ogni trimestre, il modello decide quali vettori (ambulanze) assegnare a quali zone del territorio. L'obiettivo è assicurarsi che ogni zona abbia abbastanza ambulanze vicine, riducendo i km inutili.")

    st.markdown("""
    **Come funziona in parole semplici:**
    Immagina di avere 25 squadre di ambulanzieri e 9 zone da coprire. Il modello matematico decide come distribuire le squadre in modo che:
    - Ogni zona abbia sempre almeno 2 squadre disponibili (per sicurezza)
    - Le squadre siano il più vicino possibile alla zona che servono
    - Nessuna squadra debba viaggiare troppo per raggiungere la propria zona
    - Le tre federazioni (CRI, Misericordie, ANPAS) siano bilanciate in ogni zona
    """)

    st.markdown("Confronta l'allocazione attuale (a sinistra) con quella ottimizzata dal modello (a destra):")

    strategic = data["strategic"]
    baseline = data["baseline_strategic"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ❌ AS-IS: Allocazione Attuale")
        df_base = pd.DataFrame(baseline)
        if not df_base.empty:
            st.dataframe(df_base[["carrier_name", "federation", "zone_name", "vehicle_type", "n_vehicles", "avg_km"]],
                         height=400, use_container_width=True)
            base_total_km = sum(r["avg_km"] * r["n_vehicles"] * 2 * 260 for r in baseline)
            st.metric("Costo km annuo stimato", f"{base_total_km:,.0f} km-equivalenti")

    with col2:
        st.markdown("#### ✅ TO-BE: Allocazione Ottimizzata")
        df_opt = pd.DataFrame(strategic["assignments"])
        if not df_opt.empty:
            st.dataframe(df_opt[["carrier_name", "federation", "zone_name", "vehicle_type", "n_vehicles", "avg_km"]],
                         height=400, use_container_width=True)
            opt_total_km = sum(r["avg_km"] * r["n_vehicles"] * 2 * 260 for r in strategic["assignments"])
            st.metric("Costo km annuo stimato", f"{opt_total_km:,.0f} km-equivalenti",
                       f"-{base_total_km - opt_total_km:,.0f}")

    st.markdown("---")
    st.markdown("### Formulazione del Modello LP")
    st.caption("Questa sezione descrive in dettaglio come funziona il modello matematico che calcola l'allocazione ottimale. E' divisa in tre parti: cosa decide il modello (variabili), cosa cerca di minimizzare (obiettivo), e quali regole deve rispettare (vincoli).")

    st.markdown("""
    #### 1. Cosa decide il modello (Variabili Decisionali)

    Il modello prende **due decisioni** per ogni combinazione vettore-zona:

    | Variabile | Significato | Esempio |
    |-----------|-------------|---------|
    | **x[c][z][v]** = numero intero | Quanti veicoli di tipo *v* il vettore *c* destina alla zona *z* | "La CRI Perugia destina 2 ambulanze al Distretto Perugino" |
    | **y[c][z]** = 0 oppure 1 | Se il vettore *c* opera nella zona *z* (0 = no, 1 = sì) | "La CRI Perugia opera nel Distretto Perugino? Sì (1)" |

    In pratica: prima decide *se* un vettore serve una zona (y), poi decide *quanti* mezzi ci destina (x).

    #### 2. Cosa cerca di ottenere (Funzione Obiettivo)

    Il modello vuole **minimizzare il costo totale giornaliero** di tutti i trasporti:

    `Minimizzare: Σ (distanza vettore→zona) × (costo per km / affidabilità) × (numero veicoli) × 2`

    **Cosa significa pezzo per pezzo:**
    - **Distanza**: quanti km deve fare il vettore per arrivare nella sua zona. Più è vicina la base, meno costa.
    - **Costo per km**: ogni vettore ha una tariffa contrattuale diversa (da 1,10 a 1,40 euro/km)
    - **Affidabilità** (è al denominatore!): un vettore affidabile al 96% costa "di meno" nel modello rispetto a uno all'85%, perché le sue missioni falliscono meno spesso. Questo premio l'affidabilità rispetto al solo prezzo.
    - **× 2**: l'ambulanza fa andata e ritorno, quindi i km si contano doppio.

    In sintesi: il modello preferisce vettori **vicini, economici e affidabili**.

    #### 3. Le regole da rispettare (Vincoli)

    Il modello non può assegnare i vettori a caso. Deve rispettare queste 7 regole:

    | # | Regola | Traduzione | Perché esiste |
    |---|--------|------------|---------------|
    | 1 | **Copertura domanda** | Ogni zona deve avere almeno N veicoli per tipo | Nessun distretto può restare senza ambulanze |
    | 2 | **Capacità vettore** | Nessun vettore può destinare più veicoli di quanti ne ha | Non puoi assegnare 5 ambulanze a chi ne ha 2 |
    | 3 | **Collegamento x-y** | Puoi destinare veicoli solo alle zone dove il vettore è attivo | Non ha senso assegnare veicoli a una zona che il vettore non serve |
    | 4 | **Limite zone** | Ogni vettore può coprire al massimo 3 zone | I volontari non possono sparpagliarsi su tutto il territorio |
    | 5 | **Prossimità** | Nessun vettore può servire una zona a più di 60 km dalla sua base | Non ha senso mandare un'ambulanza da Perugia a Città di Castello ogni giorno |
    | 6 | **Ridondanza** | Ogni zona deve essere coperta da almeno 2 vettori diversi | Se un vettore ha un problema, c'è sempre un piano B |
    | 7 | **Bilanciamento federazioni** | In ogni zona, nessuna federazione (CRI/Misericordie/ANPAS) può avere più del 60% dei vettori | Evitare che un solo gruppo controlli tutto il servizio in un'area |

    #### Dimensioni del problema

    Questo modello ha circa **432 variabili intere** + **216 variabili binarie** (25 vettori × 9 zone × 2 tipi veicolo).
    Il solver CBC (gratuito, open-source) lo risolve in **meno di 1 secondo**.
    """)


# --- PAGINA: Tattico ---
elif page == "📅 Tattico (Livello 2)":
    st.title("Livello 2: Assegnamento Tattico Giornaliero")
    st.markdown("### Modello Assignment Problem con Time Windows - Risolto ogni notte")

    st.info("Ogni notte, prima dell'inizio della giornata lavorativa, questo modello riceve tutte le richieste di trasporto pianificate per il giorno dopo (dimissioni programmate, trasferimenti, consulenze) e decide quale ambulanza assegnare a ciascuna. L'obiettivo: minimizzare i km totali e azzerare i viaggi fuori territorio.")

    st.markdown("""
    **Cosa significa in pratica:**
    - Ieri sera il sistema ha ricevuto ~55 richieste di trasporto per oggi
    - Per ogni richiesta, il modello ha calcolato quale vettore è il più vicino e disponibile
    - Ha assegnato ogni paziente all'ambulanza che percorre meno km per andarlo a prendere
    - Ha anche rispettato le fasce orarie (un paziente dimesso alle 10:00 non può aspettare fino alle 17:00)

    **La differenza chiave:** senza il modello (rosso), l'operatore chiama il primo vettore che trova, spesso quello sbagliato. Con il modello (verde), la scelta è ottimizzata matematicamente.
    """)

    bt = data["baseline_tactical"]
    ot = data["optimized_tactical"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ❌ AS-IS: Assegnamento Attuale")
        st.metric("km totali/giorno", f"{bt['total_km']:,.0f}")
        st.metric("Assegnati", bt["n_assigned"])
        st.metric("Non assegnati", bt["n_unassigned"])
        st.metric("% Fuori territorio", f"{bt['pct_out_territory']:.1f}%")

        df_base = pd.DataFrame(bt["assignments"])
        if not df_base.empty:
            st.dataframe(df_base[["request_id", "origin_name", "dest_name", "carrier_name", "km", "is_out_of_territory"]]
                         .head(20), height=350, use_container_width=True)

    with col2:
        st.markdown("#### ✅ TO-BE: Assegnamento Ottimizzato")
        km_delta = bt["total_km"] - ot["total_km"]
        st.metric("km totali/giorno", f"{ot['total_km']:,.0f}", f"-{km_delta:,.0f}")
        st.metric("Assegnati", ot["n_assigned"])
        st.metric("Non assegnati", ot["n_unassigned"],
                   f"-{bt['n_unassigned'] - ot['n_unassigned']}")
        st.metric("% Fuori territorio", f"{ot['pct_out_territory']:.1f}%",
                   f"-{bt['pct_out_territory'] - ot['pct_out_territory']:.1f}%")

        df_opt = pd.DataFrame(ot["assignments"])
        if not df_opt.empty:
            st.dataframe(df_opt[["request_id", "origin_name", "dest_name", "carrier_name", "km", "is_out_of_territory"]]
                         .head(20), height=350, use_container_width=True)

    st.markdown("---")
    st.markdown("### Distribuzione km per Richiesta")
    st.caption("Questo grafico mostra quanti km costa ogni singola richiesta di trasporto. Se la curva verde è più a sinistra della rossa, significa che in media ogni trasporto percorre meno km. Le barre molto a destra nella distribuzione rossa sono i trasporti 'fuori territorio' — quelli più costosi.")
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=[a["km"] for a in bt["assignments"]],
                               name="AS-IS", opacity=0.7, marker_color="#e74c3c"))
    fig.add_trace(go.Histogram(x=[a["km"] for a in ot["assignments"]],
                               name="TO-BE", opacity=0.7, marker_color="#27ae60"))
    fig.update_layout(barmode="overlay", height=350,
                      title="Distribuzione km per singola richiesta")
    st.plotly_chart(fig, use_container_width=True)


# --- PAGINA: Operativo ---
elif page == "🚨 Operativo (Livello 3)":
    st.title("Livello 3: Dispatch Operativo Real-Time")
    st.markdown("### Euristica Greedy per richieste urgenti/impreviste")

    st.info("Non tutte le richieste possono essere pianificate la notte prima. Ogni giorno arrivano richieste urgenti (un paziente che deve essere trasferito subito, una dimissione imprevista). Questo modulo risponde in tempo reale, trovando l'ambulanza più vicina disponibile in pochi secondi.")

    st.markdown("""
    **Come funziona il dispatch in tempo reale:**
    1. Arriva una richiesta urgente (es. "trasferire paziente da Gubbio a Perugia entro 1 ora")
    2. Il sistema controlla quali ambulanze sono disponibili in quel momento
    3. Per ogni ambulanza disponibile, calcola un punteggio basato su:
       - **Distanza**: quanto è lontana dal punto di partenza del paziente (più vicina = meglio)
       - **Affidabilità**: quanto è puntuale e affidabile quella squadra (più affidabile = meglio)
       - **Carico di lavoro**: quante richieste sta già gestendo oggi (più scarica = meglio)
    4. Assegna la richiesta all'ambulanza con il punteggio più alto
    """)

    op = data["operational"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Richieste Urgenti", op["n_total"])
    with col2:
        st.metric("Assegnate", op["n_assigned"],
                   delta=f"{op['n_assigned'] - op['n_unassigned']}")
    with col3:
        st.metric("km medi risposta", f"{op['avg_km_response']:.1f}")

    st.markdown("### Dettaglio Assegnamenti Urgenti")
    st.caption("La tabella mostra ogni richiesta urgente e quale vettore è stato assegnato. 'km to origin' = km dall'ambulanza al paziente. 'Reliability' = affidabilità storica del vettore (da 0 a 1). 'Current load' = quanti trasporti sta già facendo oggi.")
    df_op = pd.DataFrame(op["assignments"])
    if not df_op.empty:
        st.dataframe(df_op[["request_id", "origin_name", "dest_name", "carrier_name",
                            "km_to_origin", "reliability", "current_load"]],
                     height=400, use_container_width=True)

    st.markdown("---")
    st.markdown("### Algoritmo di Dispatch")
    st.caption("Per gli utenti tecnici, ecco lo pseudocodice dell'algoritmo che gira in tempo reale:")
    st.code("""
def dispatch_urgent(request, carriers, carrier_schedule):
    eligible = filter(carriers,
        vehicle_type_match AND within_radius AND has_capacity)
    for each eligible carrier c:
        score[c] = -km * 1.0 + reliability * 30 - (load/capacity) * 20
    return carrier with highest score
    """, language="python")


# --- PAGINA: Dialisi ---
elif page == "🩺 Dialisi (Quick Win)":
    st.title("Sotto-Problema Dialisi: Quick Win")
    st.markdown("### Periodic VRP - Ottimizzazione rotte ricorrenti")

    st.info("La dialisi è il problema più facile da ottimizzare e quello che dà i risultati più immediati. Ogni paziente dializzato fa lo stesso tragitto casa → centro dialisi → casa, 2 o 3 volte a settimana, per tutto l'anno. Se due pazienti vicini vanno nello stesso centro, possono viaggiare insieme sulla stessa ambulanza, dimezzando i km.")

    st.markdown("""
    **Perché la dialisi è il 'quick win':**
    - I pazienti sono sempre gli stessi (~45 nell'arco dell'anno)
    - Le tratte sono fisse (stesso indirizzo di partenza, stesso centro di arrivo)
    - Gli orari sono prevedibili (turno del mattino o del pomeriggio)
    - Raggruppando 2-3 pazienti vicini su una sola ambulanza, si risparmiano migliaia di km all'anno

    **Cosa fa il modello:**
    1. Prende tutti i 45 pazienti dializzati
    2. Per ogni gruppo di pazienti che vanno allo stesso centro, nello stesso turno, nello stesso giorno
    3. Cerca quali pazienti abitano vicini (entro 15 km tra loro)
    4. Li raggruppa su una sola ambulanza
    5. Assegna il gruppo all'autista più vicino
    """)

    dial = data["dialysis"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pazienti Dialisi", dial["n_patients"])
    with col2:
        st.metric("km/anno Baseline", f"{dial['annual_km_baseline']:,}")
    with col3:
        st.metric("km/anno Ottimizzati", f"{dial['annual_km_optimized']:,}",
                   f"-{dial['annual_savings_km']:,}")

    euro_dialysis = dial["annual_savings_km"] * 1.20
    st.metric("Risparmio Economico Dialisi/anno", f"{euro_dialysis:,.0f} euro",
               f"{dial['savings_pct']}% di riduzione km")

    st.markdown("---")

    # Confronto per distretto
    st.markdown("### km per Distretto: Prima vs Dopo")
    st.caption("Le barre rosse mostrano i km se ogni paziente viaggia da solo. Le barre verdi mostrano i km dopo aver raggruppato i pazienti vicini. La differenza è il risparmio.")
    assignments_df = pd.DataFrame(dial["assignments"])
    if not assignments_df.empty:
        dist_comp = assignments_df.groupby("district").agg(
            baseline=("km_per_session_baseline", "sum"),
            optimized=("km_per_session_optimized", "sum")
        ).reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(x=dist_comp["district"], y=dist_comp["baseline"],
                             name="AS-IS", marker_color="#e74c3c"))
        fig.add_trace(go.Bar(x=dist_comp["district"], y=dist_comp["optimized"],
                             name="TO-BE", marker_color="#27ae60"))
        fig.update_layout(barmode="group", height=400,
                          title="km per sessione dialisi per Distretto")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Dettaglio Assegnamenti Dialisi")
    st.caption("'Cluster size' = quanti pazienti viaggiano insieme. 'km/sessione baseline' = km se il paziente viaggiasse da solo. 'km/sessione optimized' = km dopo il raggruppamento. 'Pattern' = i giorni della settimana (MWF = lun-mer-ven, TTh = mar-gio).")
    st.dataframe(assignments_df[["patient_id", "origin_name", "dest_name", "carrier_name",
                                 "pattern", "shift", "km_per_session_baseline",
                                 "km_per_session_optimized", "cluster_size"]]
                 if not assignments_df.empty else pd.DataFrame(),
                 height=400, use_container_width=True)


# --- PAGINA: KPI & Confronto ---
elif page == "📈 KPI & Confronto":
    st.title("KPI e Confronto Globale")
    st.markdown("### Riepilogo Completo: AS-IS vs TO-BE")

    st.info("Questa pagina riassume tutti i risultati in un'unica tabella. I KPI (Key Performance Indicators) sono le metriche chiave che permettono di misurare se il sistema sta funzionando. La colonna 'Risparmio' mostra la differenza tra la situazione attuale e quella ottimizzata.")

    st.markdown("""
    **Come leggere la tabella:**
    - **AS-IS** = come funzionano oggi i trasporti (gestione frammentata, nessuna ottimizzazione)
    - **TO-BE** = come funzionerebbero con il sistema di ottimizzazione LP
    - **Risparmio** = la differenza. I numeri negativi con il segno '-' indicano una riduzione (che è positiva!)
    """)

    bt = data["baseline_tactical"]
    ot = data["optimized_tactical"]
    dial = data["dialysis"]

    # Tabella riepilogativa
    annual_km_base = bt["total_km"] * 260 + dial["annual_km_baseline"]
    annual_km_opt = ot["total_km"] * 260 + dial["annual_km_optimized"]

    kpi_data = {
        "Metrica": [
            "km trasporti ordinari/giorno",
            "km trasporti ordinari/anno",
            "% viaggi fuori territorio",
            "Richieste non evase/giorno",
            "km dialisi/anno",
            "km totali/anno",
            "Costo stimato/anno (euro)",
        ],
        "AS-IS (Attuale)": [
            f"{bt['total_km']:,.0f}",
            f"{bt['total_km'] * 260:,.0f}",
            f"{bt['pct_out_territory']:.1f}%",
            f"{bt['n_unassigned']}",
            f"{dial['annual_km_baseline']:,}",
            f"{annual_km_base:,.0f}",
            f"{annual_km_base * 1.20:,.0f}",
        ],
        "TO-BE (Ottimizzato)": [
            f"{ot['total_km']:,.0f}",
            f"{ot['total_km'] * 260:,.0f}",
            f"{ot['pct_out_territory']:.1f}%",
            f"{ot['n_unassigned']}",
            f"{dial['annual_km_optimized']:,}",
            f"{annual_km_opt:,.0f}",
            f"{annual_km_opt * 1.20:,.0f}",
        ],
        "Risparmio": [
            f"-{bt['total_km'] - ot['total_km']:,.0f} ({(bt['total_km'] - ot['total_km'])/bt['total_km']*100:.1f}%)",
            f"-{(bt['total_km'] - ot['total_km']) * 260:,.0f}",
            f"-{bt['pct_out_territory'] - ot['pct_out_territory']:.1f} pp",
            f"-{bt['n_unassigned'] - ot['n_unassigned']}",
            f"-{dial['annual_savings_km']:,} ({dial['savings_pct']}%)",
            f"-{annual_km_base - annual_km_opt:,.0f} ({(annual_km_base - annual_km_opt)/annual_km_base*100:.1f}%)",
            f"-{(annual_km_base - annual_km_opt) * 1.20:,.0f}",
        ],
    }

    df_kpi = pd.DataFrame(kpi_data)
    st.dataframe(df_kpi, height=350, use_container_width=True)

    st.markdown("---")

    # Grafico a ciambella confronto
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Ripartizione km")
        st.caption("La fetta verde rappresenta i km che non è più necessario percorrere grazie all'ottimizzazione. La fetta rossa è il chilometraggio residuo che non si può eliminare (i pazienti devono comunque essere trasportati).")
        fig = go.Figure(go.Pie(
            labels=["km risparmiati", "km residui"],
            values=[annual_km_base - annual_km_opt, annual_km_opt],
            hole=0.5,
            marker_colors=["#27ae60", "#e74c3c"],
        ))
        fig.update_layout(title="Ripartizione km dopo ottimizzazione", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Timeline implementazione
        st.markdown("### Roadmap Implementazione")
        st.caption("Il progetto si sviluppa in 5 fasi lungo 12 mesi. Ogni fase si basa sui risultati della precedente. Non si parte subito con l'ottimizzazione: prima servono i dati.")
        roadmap = pd.DataFrame({
            "Fase": ["Fase 0", "Fase 1", "Fase 2", "Fase 3", "Fase 4"],
            "Periodo": ["Mesi 1-2", "Mesi 3-4", "Mesi 5-7", "Mesi 8-10", "Mesi 11-12"],
            "Attivita": [
                "Raccolta dati & matrice distanze",
                "Modello strategico allocazione",
                "Modello tattico giornaliero + dialisi",
                "Dispatch operativo real-time",
                "Armonizzazione contratti",
            ],
            "Impatto km": ["0%", "-5%", "-10%", "-13%", "-15%"],
        })
        st.dataframe(roadmap, height=300, use_container_width=True)
