import streamlit as st
import datetime
import gspread
import pandas as pd
import requests
from google.oauth2.service_account import Credentials
from streamlit_cookies_controller import CookieController

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(
    page_title="Diario Allenamento", 
    page_icon="🏋️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. INIZIALIZZA IL CONTROLLER DEI COOKIE
controller = CookieController()

# --- TEMA ENDUFIT: SFONDO SCURO, GLASSMORPHISM, BLU E ROSSO ---
st.markdown("""
    <style>
        /* Sfondo principale e Topbar */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #050A18 !important;
        }
        
        /* Colore testi globali */
        h1, h2, h3, h4, h5, label {
            color: #ffffff !important;
        }
        p { 
            color: rgba(255,255,255,0.7) !important; 
        }
        
        /* FIX CAMPI DI INPUT E TESTI INVISIBILI */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="base-input"] {
            background-color: #f1f5f9 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
        }
        
        /* Testo scuro dentro gli input per massima leggibilità */
        input, select, textarea, div[data-baseweb="select"] span {
            background-color: transparent !important;
            color: #0f172a !important; 
            font-weight: 600 !important;
        }
        
        /* Placeholder grigio scuro */
        input::placeholder, textarea::placeholder {
            color: #64748b !important;
        }

        /* Linee orizzontali */
        hr {
            border-bottom: 1px solid #ffffff !important;
            opacity: 0.3 !important;
            margin: 2em 0 !important;
        }
        
        /* Colore icona calendario scura */
        div[data-baseweb="icon"] svg {
            fill: #0f172a !important;
            color: #0f172a !important;
        }
        
        /* Banner Installazione stile Apple Glass */
        .pwa-banner {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white !important;
            padding: 15px;
            border-radius: 16px;
            margin-bottom: 20px;
            font-size: 14px;
            text-align: center;
            border-left: 4px solid #2997ff; /* Blu ENDU */
            border-right: 4px solid #e63946; /* Rosso FIT */
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        }

        /* Pulsante Primario */
        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: linear-gradient(to right, #e63946, #b01e28) !important;
            color: white !important;
            border: none !important;
            border-radius: 50px !important;
            font-weight: bold !important;
            box-shadow: 0 4px 15px rgba(230, 57, 70, 0.3) !important;
        }

        /* Pulsante Secondario */
        button[kind="secondary"],
        div[data-testid="stFormSubmitButton"] button:not([kind="primaryFormSubmit"]):not([kind="primary"]),
        div.stButton > button:not([kind="primary"]) {
            background-color: #2997ff !important; 
            color: white !important;
            border: none !important;
            border-radius: 50px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 10px rgba(41, 151, 255, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        
        button[kind="secondary"]:hover,
        div[data-testid="stFormSubmitButton"] button:not([kind="primaryFormSubmit"]):not([kind="primary"]):hover,
        div.stButton > button:not([kind="primary"]):hover {
            background-color: #1a75d1 !important;
        }

        /* Expanders */
        div[data-testid="stExpander"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
        }
        div[data-testid="stExpander"] summary {
            background-color: transparent !important;
        }
        div[data-testid="stExpander"] summary p {
            color: #ffffff !important;
            font-weight: bold !important;
            font-size: 17px !important; /* <--- Aumenta la grandezza del testo */
            letter-spacing: 0.5px !important; /* <--- Allarga le lettere tra loro */
        }
        div[data-testid="stExpander"] summary span[data-testid="stIconMaterial"] {
            color: #ffffff !important;
        }
        
        /* Tabs */
        button[data-baseweb="tab"] p {
            font-weight: bold !important;
            color: rgba(255,255,255,0.5) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] p {
            color: #2997ff !important; 
        }
        div[data-baseweb="tab-highlight"] {
            background-color: #ffffff !important; 
        }
        
        @media all and (display-mode: standalone) {
            .pwa-banner { display: none !important; }
        }
        @media all and (display-mode: fullscreen) {
            .pwa-banner { display: none !important; }
        }
    </style>
    
    <!-- LOGO ENDUFIT IN ALTO -->
    <div style="text-align: center; margin-top: -20px; margin-bottom: 25px;">
        <span style="color: #ffffff; font-size: 42px; font-weight: 900; letter-spacing: -2px;">ENDU</span><span style="color: #2997ff; font-size: 42px; font-weight: 300; letter-spacing: -2px;">FIT</span>
    </div>
    
    <div class="pwa-banner">
        📲 <b style="color: white;">Salva l'app sul telefono!</b><br><br>
        Tocca l'icona di condivisione del browser ( 📤 ) e seleziona <b style="color: white;">"Aggiungi alla schermata Home"</b> per non perdere la tua scheda.
    </div>
    
    <!-- SCRIPT AGGRESSIVO PER SOVRASCRIVERE LA CORONA DI STREAMLIT -->
    <script>
        const iconUrl = "INCOLLA_QUI_LA_TUA_STRINGA_BASE64_QUADRATA"; 
        document.querySelectorAll('link[rel="shortcut icon"], link[rel="icon"], link[rel="apple-touch-icon"]').forEach(el => el.remove());

        let appleTouchIcon = document.createElement('link');
        appleTouchIcon.rel = 'apple-touch-icon';
        appleTouchIcon.href = iconUrl;
        document.head.appendChild(appleTouchIcon);

        let favicon = document.createElement('link');
        favicon.rel = 'icon';
        favicon.type = 'image/png';
        favicon.href = iconUrl;
        document.head.appendChild(favicon);

        const manifestLink = document.querySelector('link[rel="manifest"]');
        if (manifestLink) {
            fetch(manifestLink.href)
                .then(r => r.json())
                .then(manifest => {
                    manifest.icons = [
                        { src: iconUrl, sizes: "192x192", type: "image/png" },
                        { src: iconUrl, sizes: "512x512", type: "image/png" }
                    ];
                    const blob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
                    manifestLink.href = URL.createObjectURL(blob);
                }).catch(e => console.log('Errore manifest:', e));
        }
    </script>
""", unsafe_allow_html=True)

# --- 1. AUTENTICAZIONE GOOGLE ---
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(credentials)
except Exception as e:
    st.error("Errore di autenticazione con Google. Controlla le chiavi segrete.")
    st.stop()

# --- 2. RECUPERO ID FOGLIO (AUTOMATICO DA URL O MEMORIA) ---
id_foglio_url = st.query_params.get("id")
id_foglio_salvato = controller.get("id_salvato")

if id_foglio_url:
    id_foglio = id_foglio_url
    if id_foglio_url != id_foglio_salvato:
        controller.set("id_salvato", id_foglio_url, max_age=31536000)
else:
    id_foglio = id_foglio_salvato

if not id_foglio:
    st.info("🔄 Sincronizzazione scheda in corso...")
    st.markdown("<p style='text-align: center; color: #475569; font-size: 12px;'>Se la schermata rimane bloccata, assicurati di aver aperto il link originale inviato dal coach almeno una volta.</p>", unsafe_allow_html=True)
    st.stop()

try:
    spreadsheet = client.open_by_key(id_foglio)
except Exception as e:
    st.error(f"Impossibile accedere al foglio. Dettagli: {e}")
    st.stop()

# --- 3. DEFINIZIONE DEI FOGLI E IDENTIFICAZIONE CATEGORIA ---
try:
    sheet_programma = spreadsheet.get_worksheet(0)
    
    # IDENTIFICATORE: Se il primo foglio si chiama "Programma coach", è Fitness. Altrimenti, è Endurance.
    is_fitness = sheet_programma.title.lower().strip() == "programma coach"
    
    # Se il foglio storico non esiste, lo crea al volo (soprattutto per Endurance)
    try:
        sheet_storico = spreadsheet.worksheet("Diario Atleta") 
    except gspread.exceptions.WorksheetNotFound:
        sheet_storico = spreadsheet.add_worksheet(title="Diario Atleta", rows="1000", cols="20")
except Exception as e:
    st.error(f"Errore durante la lettura dei fogli: {e}")
    st.stop()

# --- 4. SISTEMI DI CACHE ---
@st.cache_data(ttl=300)
def scarica_dati_fogli(id_atleta, _prog, _storico):
    return _prog.get_all_values(), _storico.get_all_values()

dati_programma, dati_storico = scarica_dati_fogli(id_foglio, sheet_programma, sheet_storico)

@st.cache_data(ttl=86400) 
def cerca_immagine_esercizio(nome_esercizio):
    nome_lower = nome_esercizio.lower().strip()
    db_interno = {
        "lat machine": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Lat-Pulldown.gif",
        "panca piana": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bench-Press.gif",
        "spinte": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Incline-Dumbbell-Press.gif",
        "squat": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Squat.gif",
        "stacco": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Deadlift.gif",
        "trazioni": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Pull-up.gif",
        "rematore": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Row.gif",
        "curl": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Curl.gif",
        "alzate laterali": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lateral-Raise.gif",
        "alzate frontali": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Front-Raise.gif",
        "pressa": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Leg-Press.gif",
        "leg extension": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Leg-Extension.gif",
        "leg curl": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Leg-Curl.gif",
        "affondi": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lunge.gif",
        "croci": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Fly.gif",
        "lento avanti": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Shoulder-Press.gif",
        "french press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Skull-Crusher.gif"
    }
    
    for chiave, url_gif in db_interno.items():
        if chiave in nome_lower:
            return url_gif
            
    traduzioni = {
        "military": "military press", "tricipiti": "triceps extension",
        "polpacci": "calf", "addominali": "crunch", "crunch": "crunch",
        "iperestensioni": "hyperextension"
    }
    
    termine_ricerca = nome_lower
    for ita, eng in traduzioni.items():
        if ita in nome_lower:
            termine_ricerca = eng
            break
            
    try:
        url_search = f"https://wger.de/api/v2/exercise/search/?term={termine_ricerca}"
        res = requests.get(url_search, timeout=2)
        if res.status_code == 200:
            dati = res.json()
            if dati.get("suggestions"):
                for sugg in dati["suggestions"]:
                    ex_id = sugg["data"]["id"]
                    url_img = f"https://wger.de/api/v2/exerciseinfo/{ex_id}/"
                    res_img = requests.get(url_img, timeout=2)
                    if res_img.status_code == 200:
                        dati_img = res_img.json()
                        if dati_img.get("images"):
                            return dati_img["images"][0]["image"]
    except:
        pass
        
    return None

# ==========================================
# PARSING DATI (DIVERSO PER FITNESS ED ENDURANCE)
# ==========================================
if is_fitness:
    riga_header = -1
    idx_es, idx_giorno = -1, -1
    idx_serie_coach, idx_rip_coach, idx_carico_coach, idx_recupero = -1, -1, -1, -1
    idx_note = -1 # <--- AGGIUNGI QUESTA RIGA

    for i, riga in enumerate(dati_programma):
        riga_pulita = [str(c).lower().strip() for c in riga]
        if "esercizio" in riga_pulita and "giorno" in riga_pulita:
            riga_header = i
            idx_es = riga_pulita.index("esercizio")
            idx_giorno = riga_pulita.index("giorno")
            for j, col_str in enumerate(riga_pulita):
                if "serie target" in col_str or "serie" in col_str: idx_serie_coach = j
                elif "ripetizioni target" in col_str or "ripetizioni" in col_str or "rip" in col_str: idx_rip_coach = j
                elif "carico" in col_str or "kg" in col_str or "peso" in col_str: idx_carico_coach = j
                elif "recupero" in col_str: idx_recupero = j
                elif "note" in col_str: idx_note = j # <--- AGGIUNGI QUESTA RIGA
            break

    if riga_header == -1:
        st.error("Errore: Impossibile trovare le colonne 'Esercizio' e 'Giorno' nel programma.")
        st.stop()

    esercizi_dict = {}
    giorni_disponibili = set()

   for riga in dati_programma[riga_header+1:]:
        nome = str(riga[idx_es]).strip() if idx_es < len(riga) else ""
        giorno = str(riga[idx_giorno]).strip().upper() if idx_giorno < len(riga) else ""
        serie_coach = str(riga[idx_serie_coach]).strip() if idx_serie_coach != -1 and idx_serie_coach < len(riga) else "?"
        rip_coach = str(riga[idx_rip_coach]).strip() if idx_rip_coach != -1 and idx_rip_coach < len(riga) else "?"
        carico_coach = str(riga[idx_carico_coach]).strip() if idx_carico_coach != -1 and idx_carico_coach < len(riga) else ""
        recupero_coach = str(riga[idx_recupero]).strip() if idx_recupero != -1 and idx_recupero < len(riga) else ""
        note_coach = str(riga[idx_note]).strip() if idx_note != -1 and idx_note < len(riga) else "" # <--- AGGIUNGI QUESTA
        
        if nome != "":
            if giorno not in esercizi_dict:
                esercizi_dict[giorno] = []
            esercizi_dict[giorno].append({
                "nome": nome, "serie_coach": serie_coach, "rip_coach": rip_coach,
                "carico_coach": carico_coach, "recupero_coach": recupero_coach,
                "note_coach": note_coach # <--- AGGIUNGI QUESTA
            })
            if giorno != "":
                giorni_disponibili.add(giorno)

    giorni_disponibili = sorted(list(giorni_disponibili))

    riga_header_storico = -1
    for i, riga in enumerate(dati_storico):
        if "Esercizio" in riga and "Kg Sollevati" in riga:
            riga_header_storico = i
            break

    if riga_header_storico != -1 and len(dati_storico) > riga_header_storico + 1:
        header_storico = dati_storico[riga_header_storico]
        dati_storico_puliti = [riga + [""] * (len(header_storico) - len(riga)) for riga in dati_storico[riga_header_storico+1:]]
        df_storico = pd.DataFrame(dati_storico_puliti, columns=header_storico)
    else:
        df_storico = pd.DataFrame()

    def ottieni_testo_titolo(es_nome, serie_coach, rip_coach, carico_coach, recupero_coach):
        s_val = str(serie_coach).strip() if str(serie_coach).strip() not in ["", "N/D", "nan", "?"] else "?"
        r_val = str(rip_coach).strip() if str(rip_coach).strip() not in ["", "N/D", "nan", "?"] else "?"
        rec_val = str(recupero_coach).strip()
        
        sep = " \u2003|\u2003 " 
        
        # 1. SERIE x RIPETIZIONI 
        if s_val != "?" and r_val != "?": base_str = f"{s_val} x {r_val}"
        elif s_val != "?": base_str = f"{s_val} Set"
        elif r_val != "?": base_str = f"{r_val} rip"
        else: base_str = "Set liberi"
            
        # 2. RECUPERO 
        str_recupero = f"{sep}{rec_val}" if rec_val not in ["", "N/D", "nan", "?"] else ""
        kg_finale = ""
        
        # 3. CARICO DALLO STORICO
        if not df_storico.empty and "Esercizio" in df_storico.columns:
            df_es = df_storico[df_storico["Esercizio"] == es_nome]
            if not df_es.empty and "Kg Sollevati" in df_es.columns:
                pesi_validi = df_es[~df_es["Kg Sollevati"].astype(str).str.strip().isin(["", "0", "0,0", "0.0", "nan"])]
                if not pesi_validi.empty:
                    ultimi_kg = str(pesi_validi["Kg Sollevati"].iloc[-1]).strip().replace(",0", "").replace(".0", "")
                    if "kg" in ultimi_kg.lower():
                        kg_finale = f"{sep}{ultimi_kg}"
                    else:
                        kg_finale = f"{sep}{ultimi_kg} kg"
                
        # 4. CARICO DAL PROGRAMMA COACH
        if kg_finale == "":
            c_val = str(carico_coach).strip()
            # Se il carico esiste (non è vuoto o N/D), lo formatta. Altrimenti NON scrive nulla.
            if c_val not in ["", "N/D", "nan", "-1", "?"]: 
                if "kg" in c_val.lower():
                    kg_finale = f"{sep}{c_val}"
                else:
                    kg_finale = f"{sep}{c_val} kg"
                
        return f"{base_str}{kg_finale}{str_recupero}"

else:
    # --- LOGICA ENDURANCE ---
    idx_set, idx_gio, idx_all = 0, 1, 2
    riga_header_end = -1
    
    for i, riga in enumerate(dati_programma):
        riga_pulita = [str(c).lower().strip() for c in riga]
        if "settimana" in riga_pulita:
            riga_header_end = i
            idx_set = riga_pulita.index("settimana")
            if "giorno" in riga_pulita: idx_gio = riga_pulita.index("giorno")
            elif "data" in riga_pulita: idx_gio = riga_pulita.index("data")
            
            for col in ["allenamento", "descrizione", "programma", "workout", "seduta"]:
                if col in riga_pulita:
                    idx_all = riga_pulita.index(col)
                    break
            else:
                idx_all = idx_gio + 1 # Fallback 
            break
            
    programma_endurance = {}
    if riga_header_end != -1:
        for riga in dati_programma[riga_header_end+1:]:
            sett = str(riga[idx_set]).strip() if idx_set < len(riga) else ""
            gio = str(riga[idx_gio]).strip() if idx_gio < len(riga) else ""
            alln = str(riga[idx_all]).strip() if idx_all < len(riga) else ""
            
            if sett and gio and alln:
                if sett not in programma_endurance:
                    programma_endurance[sett] = []
                programma_endurance[sett].append({"giorno": gio, "allenamento": alln})

    # Lettura Diario Atleta (Endurance)
    if len(dati_storico) > 1:
        header_storico = dati_storico[0]
        dati_storico_puliti = [riga + [""] * (len(header_storico) - len(riga)) for riga in dati_storico[1:]]
        df_storico = pd.DataFrame(dati_storico_puliti, columns=header_storico)
    else:
        df_storico = pd.DataFrame()


# ==========================================
# INTERFACCIA A SCHEDE (TABS)
# ==========================================
tab_dash, tab_workout = st.tabs(["📊 Dashboard", "🏃‍♂️ Scheda Allenamento" if not is_fitness else "🏋️‍♂️ Scheda Allenamento"])


# ==========================================
# SEZIONE 1: DASHBOARD
# ==========================================
with tab_dash:
    if is_fitness:
        st.header("Dashboard Analitica 🚀")
        df_stat = df_storico.copy() if not df_storico.empty else pd.DataFrame()
        
        if not df_stat.empty and "Data" in df_stat.columns:
            df_stat["Data_dt"] = pd.to_datetime(df_stat["Data"], errors="coerce", dayfirst=True)
            df_stat = df_stat.dropna(subset=["Data_dt"])
            
        if df_stat.empty:
            st.info("Nessun allenamento registrato. Inizia ad allenarti per sbloccare le metriche avanzate!")
        else:
            col_rpe = next((col for col in df_stat.columns if "rpe" in str(col).lower()), None)
            if col_rpe: df_stat["RPE_num"] = pd.to_numeric(df_stat[col_rpe].astype(str).replace(",", ".", regex=True), errors="coerce").fillna(0)
            else: df_stat["RPE_num"] = 0

            tot_allenamenti = df_stat["Data"].nunique()
            c1, c2, c3 = st.columns(3)
            c1.metric("Allenamenti", tot_allenamenti)
            c2.metric("Ultima Sessione", df_stat["Data"].max())
            c3.metric("RPE Medio", f"{df_stat['RPE_num'].mean():.1f}/10" if col_rpe else "N/D")
            
            st.divider()
            import altair as alt

            st.subheader("Costanza di Allenamento")
            st.markdown("<p style='font-size: 13px;'>Ogni quadrato rappresenta un giorno. Più è scuro, maggiore è il volume (serie) completato.</p>", unsafe_allow_html=True)
            
            df_giorni = df_stat.groupby("Data_dt").size().reset_index(name="Volume (Serie)")
            heatmap = alt.Chart(df_giorni).mark_rect().encode(
                x=alt.X("yearweek(Data_dt):O", title="Settimana dell'anno", axis=alt.Axis(labelAngle=0, labelColor="rgba(255,255,255,0.5)")),
                y=alt.Y("day(Data_dt):O", title="", axis=alt.Axis(labelColor="rgba(255,255,255,0.7)")),
                color=alt.Color("Volume (Serie):Q", scale=alt.Scale(scheme="blues"), legend=None),
                tooltip=[alt.Tooltip("Data_dt:T", title="Data", format="%d %b %Y"), alt.Tooltip("Volume (Serie):Q", title="Serie Totali")]
            ).properties(height=180).configure_view(strokeWidth=0).configure_axis(grid=False, domain=False).configure(background='transparent')
            
            st.altair_chart(heatmap, use_container_width=True)
            st.divider()

            col_graf_1, col_graf_2 = st.columns(2)
            with col_graf_1:
                st.write("**Fatica Percepita (RPE)**")
                if col_rpe and df_stat["RPE_num"].sum() > 0:
                    df_rpe_trend = df_stat.groupby("Data_dt")["RPE_num"].mean().reset_index()
                    grafico_rpe = alt.Chart(df_rpe_trend).mark_line(
                        color="#e63946", strokeWidth=3, point=alt.OverlayMarkDef(color="#ffffff", size=60, filled=True)
                    ).encode(
                        x=alt.X("Data_dt:T", title="", axis=alt.Axis(labelAngle=-45, format="%d %b")),
                        y=alt.Y("RPE_num:Q", title="RPE (0-10)", scale=alt.Scale(domain=[0, 10])),
                        tooltip=[alt.Tooltip("Data_dt:T", title="Data", format="%d %b"), alt.Tooltip("RPE_num:Q", title="RPE", format=".1f")]
                    ).properties(height=250).configure_view(strokeWidth=0).configure_axis(
                        gridColor="rgba(255,255,255,0.1)", domain=False, labelColor="rgba(255,255,255,0.7)"
                    ).configure(background='transparent')
                    st.altair_chart(grafico_rpe, use_container_width=True)
                else:
                    st.info("Nessun dato RPE registrato.")

            with col_graf_2:
                st.write("**Distribuzione Carico (Tonnellaggio)**")
                mappa_muscoli = {
                    "panca": "Petto", "spinte": "Petto", "croci": "Petto", "chest": "Petto", "dip": "Petto", "piegament": "Petto", "pectoral": "Petto",
                    "lat machine": "Schiena", "trazion": "Schiena", "rematore": "Schiena", "pulley": "Schiena", "pull": "Schiena", "row": "Schiena", "dorso": "Schiena", "schiena": "Schiena",
                    "squat": "Gambe", "pressa": "Gambe", "leg press": "Gambe", "leg extension": "Gambe", "leg curl": "Gambe", "affond": "Gambe", "polpacc": "Gambe", "stacco": "Gambe", "calf": "Gambe", "glute": "Gambe",
                    "military": "Spalle", "lento": "Spalle", "alzate": "Spalle", "shoulder": "Spalle", "deltoid": "Spalle",
                    "curl": "Bicipiti", "bicipit": "Bicipiti", "bicep": "Bicipiti",
                    "french": "Tricipiti", "tricipit": "Tricipiti", "pushdown": "Tricipiti", "kickback": "Tricipiti", "tricep": "Tricipiti", "extension": "Tricipiti"
                }
                
                def assegna_muscolo(es):
                    es_lower = str(es).lower()
                    for chiave, muscolo in mappa_muscoli.items():
                        if chiave in es_lower: return muscolo
                    return "Altro"

                df_stat["Gruppo"] = df_stat["Esercizio"].apply(assegna_muscolo)
                col_tonn = next((col for col in df_stat.columns if "tonnellagg" in str(col).lower()), None)
                if col_tonn: df_stat["Tonn_num"] = pd.to_numeric(df_stat[col_tonn].astype(str).replace(",", ".", regex=True), errors="coerce").fillna(0)
                else: df_stat["Tonn_num"] = 0
                    
                df_muscoli = df_stat.groupby("Gruppo")["Tonn_num"].sum().reset_index(name="Tonnellaggio Totale")
                df_muscoli = df_muscoli[df_muscoli["Tonnellaggio Totale"] > 0]
                
                if not df_muscoli.empty:
                    totale_carico = df_muscoli["Tonnellaggio Totale"].sum()
                    df_muscoli["Percentuale"] = (df_muscoli["Tonnellaggio Totale"] / totale_carico) * 100
                    df_muscoli["Label"] = df_muscoli["Percentuale"].apply(lambda x: f"{x:.0f}%" if x >= 3 else "")
                    
                    base_chart = alt.Chart(df_muscoli).encode(
                        theta=alt.Theta(field="Tonnellaggio Totale", type="quantitative", stack=True),
                        color=alt.Color(field="Gruppo", type="nominal", scale=alt.Scale(scheme="category10"), legend=alt.Legend(title="", labelColor="rgba(255,255,255,0.7)"))
                    )
                    ciambella = base_chart.mark_arc(innerRadius=45, outerRadius=90, stroke="#050A18", strokeWidth=2).encode(
                        tooltip=[alt.Tooltip("Gruppo:N"), alt.Tooltip("Tonnellaggio Totale:Q", format=".0f", title="Carico")]
                    )
                    testo = base_chart.mark_text(radius=115, fill="white", size=11, fontWeight="bold").encode(text="Label:N")
                    grafico_finale = (ciambella + testo).properties(height=250).configure_view(strokeWidth=0).configure(background='transparent')
                    st.altair_chart(grafico_finale, use_container_width=True)
                else:
                    st.info("Nessun carico registrato.")

    else:
        # --- DASHBOARD ENDURANCE ---
        st.header("Dashboard Analitica 🏃‍♂️")
        df_stat = df_storico.copy() if not df_storico.empty else pd.DataFrame()
        
        # Per endurance il diario ha tipicamente: [Data, Settimana, Giorno, Allenamento, RPE, Feedback]
        if not df_stat.empty and len(df_stat.columns) >= 5:
            col_data = next((col for col in df_stat.columns if "data" in str(col).lower()), df_stat.columns[0])
            df_stat["Data_dt"] = pd.to_datetime(df_stat[col_data], errors="coerce", dayfirst=True)
            df_stat = df_stat.dropna(subset=["Data_dt"])
                
        if df_stat.empty:
            st.info("Nessun allenamento registrato. Registra la tua prima sessione Endurance!")
        else:
            import altair as alt
            col_rpe = next((col for col in df_stat.columns if "rpe" in str(col).lower()), None)
            if col_rpe: df_stat["RPE_num"] = pd.to_numeric(df_stat[col_rpe].astype(str).replace(",", ".", regex=True), errors="coerce").fillna(0)
            else: df_stat["RPE_num"] = 0
                
            tot_allenamenti = len(df_stat)
            c1, c2, c3 = st.columns(3)
            c1.metric("Allenamenti Completati", tot_allenamenti)
            c2.metric("Ultima Sessione", df_stat["Data_dt"].dt.strftime('%d/%m/%Y').max())
            c3.metric("RPE Medio", f"{df_stat['RPE_num'].mean():.1f}/10")
            
            st.divider()
            st.subheader("Andamento Fatica (RPE)")
            
            df_rpe_trend = df_stat.groupby("Data_dt")["RPE_num"].mean().reset_index()
            grafico_rpe = alt.Chart(df_rpe_trend).mark_line(
                color="#2997ff", strokeWidth=3, point=alt.OverlayMarkDef(color="#ffffff", size=60, filled=True)
            ).encode(
                x=alt.X("Data_dt:T", title="", axis=alt.Axis(labelAngle=-45, format="%d %b")),
                y=alt.Y("RPE_num:Q", title="RPE (0-10)", scale=alt.Scale(domain=[0, 10])),
                tooltip=[alt.Tooltip("Data_dt:T", title="Data", format="%d %b"), alt.Tooltip("RPE_num:Q", title="RPE", format=".1f")]
            ).properties(height=250).configure_view(strokeWidth=0).configure_axis(
                gridColor="rgba(255,255,255,0.1)", domain=False, labelColor="rgba(255,255,255,0.7)"
            ).configure(background='transparent')
            
            st.altair_chart(grafico_rpe, use_container_width=True)


# ==========================================
# SEZIONE 2: SCHEDA DI ALLENAMENTO
# ==========================================
with tab_workout:
    if st.session_state.get("dati_salvati", False):
        st.success("Dati inviati al coach! 🔥 Puoi chiudere questa pagina.")
        if st.button("Inserisci un'altra scheda"):
            st.session_state.dati_salvati = False
            st.rerun()
    else:
        st.write("### Registra la sessione di oggi")
        data_sessione = st.date_input("Data della sessione", datetime.date.today())

        if is_fitness:
            # --- FORM FITNESS (ORIGINALE) ---
            if not giorni_disponibili:
                st.warning("Non ci sono esercizi assegnati o manca la lettera del 'Giorno' nel programma.")
            else:
                giorno_scelto = st.selectbox("Quale scheda (Giorno) vuoi allenare oggi?", giorni_disponibili)
                esercizi_assegnati = esercizi_dict[giorno_scelto]
                
                if "contatore_serie" not in st.session_state: st.session_state.contatore_serie = {}
                if "ultimo_giorno_scelto" not in st.session_state: st.session_state.ultimo_giorno_scelto = giorno_scelto
                if "es_aperto" not in st.session_state: st.session_state.es_aperto = None
                    
                if st.session_state.ultimo_giorno_scelto != giorno_scelto:
                    st.session_state.contatore_serie = {}
                    st.session_state.ultimo_giorno_scelto = giorno_scelto
                    st.session_state.es_aperto = None

                st.divider()
                
                with st.form("workout_form"):
                    st.write("### Scheda")
                    
                    for es_obj in esercizi_assegnati:
                        es = es_obj["nome"]
                        serie_coach = es_obj["serie_coach"]
                        rip_coach = es_obj["rip_coach"]
                        carico_coach = es_obj["carico_coach"]
                        recupero_coach = es_obj["recupero_coach"]
                        
                        if es not in st.session_state.contatore_serie:
                            import re
                            numeri = re.findall(r'\d+', str(serie_coach))
                            st.session_state.contatore_serie[es] = max(1, int(numeri[0])) if numeri else 1
                        
                        testo_titolo = ottieni_testo_titolo(es, serie_coach, rip_coach, carico_coach, recupero_coach)
                        tieni_aperto = (st.session_state.es_aperto == es)
                        
                        with st.expander(f"{es} \u2003—\u2003 {testo_titolo}", expanded=tieni_aperto):
                            img_url = cerca_immagine_esercizio(es)
                            if img_url:
                                st.markdown(f'<div style="display:flex;justify-content:center;margin-bottom:15px;"><img src="{img_url}" width="200" style="border-radius:10px;"></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='text-align:center;margin-bottom:15px;'><a href='https://www.youtube.com/results?search_query=tutorial+esecuzione+{es.replace(' ', '+')}' target='_blank' style='text-decoration:none;font-size:14px;font-weight:bold;color:#e63946;'>🎥 Cerca Tutorial YouTube</a></div>", unsafe_allow_html=True)
                            
                            for i in range(st.session_state.contatore_serie[es]):
                                st.markdown(f"**Serie {i + 1}**")
                                c1, c2 = st.columns(2)
                                with c1: st.number_input("Ripetizioni", min_value=0, step=1, key=f"rip_{es}_{i}")
                                with c2: st.number_input("Kg", min_value=0.0, step=0.5, key=f"kg_{es}_{i}")
                            
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.form_submit_button(f"➕ Aggiungi Serie", key=f"btn_add_{es}", use_container_width=True):
                                    idx_nuovo = st.session_state.contatore_serie[es]
                                    st.session_state[f"rip_{es}_{idx_nuovo}"] = st.session_state.get(f"rip_{es}_{idx_nuovo-1}", 0)
                                    st.session_state[f"kg_{es}_{idx_nuovo}"] = st.session_state.get(f"kg_{es}_{idx_nuovo-1}", 0.0)
                                    st.session_state.contatore_serie[es] += 1
                                    st.session_state.es_aperto = es
                                    st.rerun() 
                            with btn_col2:
                                if st.form_submit_button(f"➖ Rimuovi Serie", key=f"btn_rem_{es}", use_container_width=True):
                                    if st.session_state.contatore_serie[es] > 1:
                                        st.session_state.contatore_serie[es] -= 1
                                        st.session_state.es_aperto = es
                                        st.rerun()

                    st.divider()
                    st.write("### Fine Allenamento")
                    rpe_globale = st.slider("Fatica percepita (10=massima, 0=nessuna)", min_value=0.0, max_value=10.0, value=7.0, step=0.5)
                    feedback_globale = st.text_area("Feedback / Dolori (Opzionale)", placeholder="Scrivi qui se hai provato fastidi...")
                    
                    st.divider()
                    if st.form_submit_button("💾 Consegna Intero Allenamento", type="primary", use_container_width=True):
                        righe_da_inserire = []
                        for es_obj in esercizi_assegnati:
                            es = es_obj["nome"]
                            for i in range(st.session_state.contatore_serie[es]):
                                rip = st.session_state.get(f"rip_{es}_{i}", 0)
                                kg = st.session_state.get(f"kg_{es}_{i}", 0.0)
                                if rip > 0:
                                    righe_da_inserire.append([
                                        str(data_sessione), es, i+1, rip, str(kg).replace(".", ","), 
                                        str(rip*kg).replace(".", ","), str(rpe_globale).replace(".", ","), feedback_globale
                                    ])
                        
                        if len(righe_da_inserire) > 0:
                            try:
                                sheet_storico.append_rows(righe_da_inserire, value_input_option='USER_ENTERED')
                                scarica_dati_fogli.clear()
                                st.session_state.dati_salvati = True
                                st.session_state.contatore_serie = {} 
                                st.session_state.es_aperto = None 
                                st.rerun() 
                            except Exception as e:
                                st.error(f"Errore durante il salvataggio: {e}")
                        else:
                            st.warning("⚠️ Non hai compilato nessuna serie valida. Nessun dato salvato.")

        else:
            # --- FORM ENDURANCE ---
            if not programma_endurance:
                st.warning("⚠️ Impossibile generare le settimane. Assicurati che nel foglio ci siano le colonne 'Settimana', 'Giorno' e 'Allenamento'.")
            else:
                settimane_disponibili = list(programma_endurance.keys())
                settimana_scelta = st.selectbox("📅 Seleziona la Settimana", settimane_disponibili)
                
                allenamenti_settimana = programma_endurance[settimana_scelta]
                st.divider()
                st.write("### I tuoi allenamenti")
                
                for idx, all_obj in enumerate(allenamenti_settimana):
                    gio = all_obj["giorno"]
                    txt_allenamento = all_obj["allenamento"]
                    
                    with st.expander(f"📍 {gio}", expanded=False):
                        st.markdown(f"**Programma della seduta:**")
                        st.info(txt_allenamento)
                        
                        # Form separato per OGNI singolo giorno
                        with st.form(key=f"form_endurance_{idx}"):
                            st.write("**Com'è andata questa seduta?**")
                            rpe_seduta = st.slider("Fatica percepita (RPE)", min_value=0.0, max_value=10.0, value=7.0, step=0.5, key=f"rpe_endurance_{idx}")
                            feedback_seduta = st.text_area("Note / Feedback (Opzionale)", placeholder="Sensazioni, fatica, dolori...", key=f"feed_endurance_{idx}")
                            
                            if st.form_submit_button("💾 Salva Allenamento", type="primary", use_container_width=True):
                                righe_da_inserire = []
                                
                                # Se il diario è completamente vuoto, inseriamo prima le intestazioni per non far crollare la dashboard in futuro
                                se_diario_vuoto = len(dati_storico) == 0
                                if se_diario_vuoto:
                                    righe_da_inserire.append(["Data", "Settimana", "Giorno", "Allenamento", "RPE", "Feedback"])
                                
                                righe_da_inserire.append([
                                    str(data_sessione),
                                    settimana_scelta,
                                    gio,
                                    txt_allenamento,
                                    str(rpe_seduta).replace(".", ","),
                                    feedback_seduta
                                ])
                                
                                try:
                                    sheet_storico.append_rows(righe_da_inserire, value_input_option='USER_ENTERED')
                                    scarica_dati_fogli.clear()
                                    st.session_state.dati_salvati = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Errore durante il salvataggio: {e}")
