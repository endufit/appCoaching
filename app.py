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
        
        /* Colore testi globali (Rimosso 'div' e 'span' per non buggare i menu a tendina) */
        h1, h2, h3, h4, h5, label {
            color: #ffffff !important;
        }
        p { 
            color: rgba(255,255,255,0.7) !important; 
        }
        
        /* ⚠️ FIX CAMPI DI INPUT E TESTI INVISIBILI ⚠️ */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="base-input"] {
            background-color: #f1f5f9 !important; /* Sfondo chiaro per i campi */
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
        }
        
        /* Testo scuro dentro gli input per massima leggibilità */
        input, select, textarea, div[data-baseweb="select"] span {
            background-color: transparent !important;
            color: #0f172a !important; /* Testo scuro/nero */
            font-weight: 600 !important;
        }
        
        /* Placeholder grigio scuro */
        input::placeholder, textarea::placeholder {
            color: #64748b !important;
        }

        /* Linee orizzontali (st.divider) */
        hr {
            border-bottom: 1px solid #ffffff !important;
            opacity: 0.3 !important; /* Opzionale: per non renderle troppo un "pugno in un occhio" */
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
        div[data-testid="stFormSubmitButton"] > button[kind="secondary"] {
            background-color: rgba(41, 151, 255, 0.1) !important;
            color: #2997ff !important;
            border: 1px solid rgba(41, 151, 255, 0.4) !important;
            border-radius: 50px !important;
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
        }
        /* ⚠️ FIX: Forza le nuove freccette testuali (Material Icons) a essere bianche */
        div[data-testid="stExpander"] summary span[data-testid="stIconMaterial"] {
            color: #ffffff !important;
        }
        /* Tabs */
        button[data-baseweb="tab"] p {
            font-weight: bold !important;
            color: rgba(255,255,255,0.5) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] p {
            color: #2997ff !important; /* Lascia il testo blu... */
        }
        div[data-baseweb="tab-highlight"] {
            background-color: #ffffff !important; /* ...ma fai la linea sotto bianca! */
        }
        @media all and (display-mode: standalone) {
            .pwa-banner { display: none !important; }
        }
        @media all and (display-mode: fullscreen) {
            .pwa-banner { display: none !important; }
        }
    </style>
    
    <!-- ⚠️ NUOVO: LOGO ENDUFIT IN ALTO ⚠️ -->
    <div style="text-align: center; margin-top: -20px; margin-bottom: 25px;">
        <span style="color: #ffffff; font-size: 42px; font-weight: 900; letter-spacing: -2px;">ENDU</span><span style="color: #2997ff; font-size: 42px; font-weight: 300; letter-spacing: -2px;">FIT</span>
    </div>
    
    <div class="pwa-banner">
        📲 <b style="color: white;">Salva l'app sul telefono!</b><br><br>
        Tocca l'icona di condivisione del browser ( 📤 ) e seleziona <b style="color: white;">"Aggiungi alla schermata Home"</b> per non perdere la tua scheda.
    </div>
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

# Diamo priorità all'URL. Se c'è un ID nell'URL ed è diverso da quello salvato, aggiorniamo il cookie.
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

# --- 3. DEFINIZIONE DEI FOGLI ---
try:
    sheet_programma = spreadsheet.get_worksheet(0)
    sheet_storico = spreadsheet.worksheet("Diario Atleta") 
except Exception as e:
    st.error(f"Errore: Impossibile trovare 'Diario Atleta'. Controlla che le schede nel file Excel si chiamino correttamente. Errore: {e}")
    st.stop()


# --- 4. SISTEMI DI CACHE ---
@st.cache_data(ttl=300)
def scarica_dati_fogli(id_atleta, _prog, _storico):
    return _prog.get_all_values(), _storico.get_all_values()

# Passiamo l'id_foglio così Streamlit separa la memoria per ogni atleta!
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


# --- 5. ESTRAZIONE DATI PROGRAMMA E STORICO ---
riga_header = -1
idx_es, idx_giorno = -1, -1
idx_serie_coach, idx_rip_coach, idx_carico_coach, idx_recupero = -1, -1, -1, -1

# 1. Ricerca robusta delle colonne (ignora spazi vuoti e maiuscole)
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
        break

if riga_header == -1:
    st.error("Errore: Impossibile trovare le colonne 'Esercizio' e 'Giorno' nel programma.")
    st.stop()

esercizi_dict = {}
giorni_disponibili = set()

for riga in dati_programma[riga_header+1:]:
    # 2. Estrazione sicura (evita che le celle vuote facciano saltare l'esercizio)
    nome = str(riga[idx_es]).strip() if idx_es < len(riga) else ""
    giorno = str(riga[idx_giorno]).strip().upper() if idx_giorno < len(riga) else ""
    
    serie_coach = str(riga[idx_serie_coach]).strip() if idx_serie_coach != -1 and idx_serie_coach < len(riga) else "?"
    rip_coach = str(riga[idx_rip_coach]).strip() if idx_rip_coach != -1 and idx_rip_coach < len(riga) else "?"
    carico_coach = str(riga[idx_carico_coach]).strip() if idx_carico_coach != -1 and idx_carico_coach < len(riga) else ""
    recupero_coach = str(riga[idx_recupero]).strip() if idx_recupero != -1 and idx_recupero < len(riga) else ""
    
    if nome != "":
        if giorno not in esercizi_dict:
            esercizi_dict[giorno] = []
        esercizi_dict[giorno].append({
            "nome": nome, 
            "serie_coach": serie_coach,
            "rip_coach": rip_coach,
            "carico_coach": carico_coach,
            "recupero_coach": recupero_coach
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
    # Correggi l'estrazione dello storico, considerando che alcune righe potrebbero essere più corte dell'header
    header_storico = dati_storico[riga_header_storico]
    dati_storico_puliti = [riga + [""] * (len(header_storico) - len(riga)) for riga in dati_storico[riga_header_storico+1:]]
    df_storico = pd.DataFrame(dati_storico_puliti, columns=header_storico)
else:
    df_storico = pd.DataFrame()

def ottieni_testo_titolo(es_nome, serie_coach, rip_coach, carico_coach, recupero_coach):
    s_val = str(serie_coach).strip() if str(serie_coach).strip() not in ["", "N/D", "nan", "?"] else "?"
    r_val = str(rip_coach).strip() if str(rip_coach).strip() not in ["", "N/D", "nan", "?"] else "?"
    rec_val = str(recupero_coach).strip()
    
    if s_val != "?" and r_val != "?":
        base_str = f"{s_val}x{r_val}"
    elif s_val != "?":
        base_str = f"{s_val} Set"
    elif r_val != "?":
        base_str = f"{r_val} rip"
    else:
        base_str = "Set liberi"
        
    str_recupero = f"  •  {rec_val}" if rec_val not in ["", "N/D", "nan", "?"] else ""
    
    kg_finale = ""
    if not df_storico.empty and "Esercizio" in df_storico.columns:
        df_es = df_storico[df_storico["Esercizio"] == es_nome]
        if not df_es.empty and "Kg Sollevati" in df_es.columns:
            pesi_validi = df_es[~df_es["Kg Sollevati"].astype(str).str.strip().isin(["", "0", "0,0", "0.0", "nan"])]
            if not pesi_validi.empty:
                ultimi_kg = pesi_validi["Kg Sollevati"].iloc[-1]
                kg_str = str(ultimi_kg).strip().replace(",0", "").replace(".0", "")
                kg_finale = f"  •  {kg_str} kg"
                
    if kg_finale == "":
        c_val = str(carico_coach).strip()
        if c_val not in ["", "N/D", "nan", "-1", "?"]:
            kg_finale = f"  •  {c_val} kg"
        else:
            kg_finale = f"  •  Kg liberi"
            
    return f"{base_str}{kg_finale}{str_recupero}"

# --- 6. INTERFACCIA A SCHEDE (TABS) ---
tab_dash, tab_workout = st.tabs(["📊 Dashboard", "🏋️‍♂️ Scheda Allenamento"])

# ==========================================
# SEZIONE 1: DASHBOARD
# ==========================================
with tab_dash:
    st.header("I Tuoi Progressi 🚀")
    
    if df_storico.empty:
        st.info("Non ci sono ancora dati registrati. Inizia ad allenarti per sbloccare i grafici!")
    else:
        df_stat = df_storico.copy()
        
        # 1. KPI Generali 
        tot_allenamenti = df_stat["Data"].nunique() if "Data" in df_stat.columns else 0
        
        c1, c2 = st.columns(2)
        c1.metric("Allenamenti Completati", tot_allenamenti)
        
        if "Data" in df_stat.columns:
            ultima_data = df_stat["Data"].max()
            c2.metric("Ultimo Allenamento", str(ultima_data))
        
        st.divider()
        
        # 2. PROGRESSIONE SUI SINGOLI ESERCIZI (Molto più utile)
        st.subheader("Progressione Carichi 📈")
        st.markdown("<p style='font-size: 14px;'>Seleziona un esercizio per vedere come è migliorata la tua forza nel tempo.</p>", unsafe_allow_html=True)
        
        if "Esercizio" in df_stat.columns and "Kg Sollevati" in df_stat.columns:
            # Puliamo la colonna dei Kg in caso l'utente abbia inserito la virgola invece del punto
            df_stat["Kg_puliti"] = pd.to_numeric(df_stat["Kg Sollevati"].astype(str).replace(",", ".", regex=True), errors='coerce').fillna(0)
            
            # Filtriamo solo le serie in cui è stato sollevato un peso effettivo
            df_validi = df_stat[df_stat["Kg_puliti"] > 0]
            
            esercizi_svolti = sorted(df_validi["Esercizio"].unique().tolist())
            
            if esercizi_svolti:
                # Menu a tendina elegante per scegliere l'esercizio
                es_selezionato = st.selectbox("Scegli un esercizio", esercizi_svolti, label_visibility="collapsed")
                
                # Filtra i dati per l'esercizio scelto
                df_es = df_validi[df_validi["Esercizio"] == es_selezionato]
                
                # Trova il massimale assoluto (Personal Best)
                pb_assoluto = df_es["Kg_puliti"].max()
                
                # Badge visivo per il PB
                st.markdown(f"""
                    <div style='background: rgba(230, 57, 70, 0.1); border: 1px solid rgba(230, 57, 70, 0.3); border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 20px;'>
                        <span style='font-size: 13px; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 1px;'>Personal Best (1RM Testato)</span><br>
                        <span style='color: #e63946; font-size: 28px; font-weight: 900;'>{pb_assoluto:g} <span style='font-size: 16px;'>kg</span></span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Calcola il carico massimo sollevato in ogni data per creare la curva di progressione
                progressione = df_es.groupby("Data")["Kg_puliti"].max().reset_index()
                
                import altair as alt
                # Grafico della progressione
                grafico_prog = alt.Chart(progressione).mark_line(
                    color="#2997ff", # Linea Blu ENDU
                    strokeWidth=4, 
                    point=alt.OverlayMarkDef(color="#e63946", size=150, filled=True, opacity=1) # Pallini Rossi FIT
                ).encode(
                    x=alt.X("Data:N", title="", axis=alt.Axis(labelAngle=-45, labelPadding=10)),
                    y=alt.Y("Kg_puliti:Q", title="Carico Massimo (kg)", scale=alt.Scale(zero=False, padding=10)),
                    tooltip=[alt.Tooltip("Data:N", title="Data"), alt.Tooltip("Kg_puliti:Q", title="Carico (kg)")]
                ).configure(
                    background='#050A18'
                ).configure_axis(
                    gridColor="rgba(255,255,255,0.08)",
                    domainColor="rgba(255,255,255,0.2)",
                    labelColor="rgba(255,255,255,0.7)",
                    titleColor="#ffffff"
                ).configure_view(
                    strokeWidth=0
                )
                
                st.altair_chart(grafico_prog, use_container_width=True, theme=None)
            else:
                st.info("Registra dei carichi in allenamento per sbloccare le statistiche di progressione.")


# ==========================================
# SEZIONE 2: SCHEDA DI ALLENAMENTO
# ==========================================
with tab_workout:
    
    if st.session_state.get("dati_salvati", False):
        st.success("Dati della scheda inviati al coach! 🏋️‍♂️🔥 Puoi chiudere questa pagina.")
        if st.button("Inserisci un'altra scheda"):
            st.session_state.dati_salvati = False
            st.rerun()
    else:
        st.write("### Registra la sessione di oggi")
        data_sessione = st.date_input("Data della sessione", datetime.date.today())

        if not giorni_disponibili:
            st.warning("Non ci sono esercizi assegnati o manca la lettera del 'Giorno' nel programma.")
        else:
            giorno_scelto = st.selectbox("Quale scheda (Giorno) vuoi allenare oggi?", giorni_disponibili)
            esercizi_assegnati = esercizi_dict[giorno_scelto]
            
            if "contatore_serie" not in st.session_state:
                st.session_state.contatore_serie = {}
            if "ultimo_giorno_scelto" not in st.session_state:
                st.session_state.ultimo_giorno_scelto = giorno_scelto
            if "es_aperto" not in st.session_state:
                st.session_state.es_aperto = None
                
            if st.session_state.ultimo_giorno_scelto != giorno_scelto:
                st.session_state.contatore_serie = {}
                st.session_state.ultimo_giorno_scelto = giorno_scelto
                st.session_state.es_aperto = None

            st.divider()
            
            with st.form("workout_form"):
                
                # Aggiunta del titolo sopra l'elenco
                st.write("### Scheda")
                
                for es_obj in esercizi_assegnati:
                    es = es_obj["nome"]
                    serie_coach = es_obj["serie_coach"]
                    rip_coach = es_obj["rip_coach"]
                    carico_coach = es_obj["carico_coach"]
                    recupero_coach = es_obj["recupero_coach"]
                    
                    if es not in st.session_state.contatore_serie:
                        st.session_state.contatore_serie[es] = 1
                    
                    testo_titolo = ottieni_testo_titolo(es, serie_coach, rip_coach, carico_coach, recupero_coach)
                    titolo_expander = f"{es}  —  {testo_titolo}"
                    
                    tieni_aperto = (st.session_state.es_aperto == es)
                    
                    with st.expander(titolo_expander, expanded=tieni_aperto):
                        
                        img_url = cerca_immagine_esercizio(es)
                        if img_url:
                            st.markdown(f"""
                                <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                                    <img src="{img_url}" width="200" style="border-radius: 10px;">
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f"<div style='text-align: center; margin-bottom: 15px;'>"
                                f"<a href='https://www.youtube.com/results?search_query=tutorial+esecuzione+{es.replace(' ', '+')}' "
                                f"target='_blank' style='text-decoration: none; font-size: 14px; font-weight: bold; color: #e63946;'>"
                                f"🎥 Cerca Tutorial YouTube</a></div>", 
                                unsafe_allow_html=True
                            )
                        
                        for i in range(st.session_state.contatore_serie[es]):
                            st.markdown(f"**Serie {i + 1}**")
                            c1, c2 = st.columns(2)
                            with c1:
                                st.number_input("Ripetizioni", min_value=0, step=1, key=f"rip_{es}_{i}")
                            with c2:
                                st.number_input("Kg", min_value=0.0, step=0.5, key=f"kg_{es}_{i}")
                        
                        if st.form_submit_button(f"➕ Aggiungi Serie", key=f"btn_add_{es}"):
                            idx_nuovo = st.session_state.contatore_serie[es]
                            idx_vecchio = idx_nuovo - 1
                            
                            st.session_state[f"rip_{es}_{idx_nuovo}"] = st.session_state.get(f"rip_{es}_{idx_vecchio}", 0)
                            st.session_state[f"kg_{es}_{idx_nuovo}"] = st.session_state.get(f"kg_{es}_{idx_vecchio}", 0.0)
                            
                            st.session_state.contatore_serie[es] += 1
                            st.session_state.es_aperto = es
                            st.rerun() 

                st.divider()
                st.write("### Fine Allenamento")
                rpe_globale = st.slider(
                    "Fatica percepita (10=fatica massima, 0=nessuna fatica)", 
                    min_value=0.0, max_value=10.0, value=7.0, step=0.5
                )
                feedback_globale = st.text_area(
                    "Feedback / Dolori (Opzionale)", 
                    placeholder="Scrivi qui se hai provato fastidi, come ti sei sentito, ecc..."
                )
                
                st.divider()
                
                submit_finale = st.form_submit_button("💾 Consegna Intero Allenamento", type="primary", use_container_width=True)
                
                if submit_finale:
                    righe_da_inserire = []
                    
                    for es_obj in esercizi_assegnati:
                        es = es_obj["nome"]
                        
                        for i in range(st.session_state.contatore_serie[es]):
                            rip = st.session_state.get(f"rip_{es}_{i}", 0)
                            kg = st.session_state.get(f"kg_{es}_{i}", 0.0)
                            
                            if rip > 0:
                                numero_serie = i + 1
                                tonnellaggio = rip * kg
                                
                                nuova_riga = [
                                    str(data_sessione),             
                                    es,                             
                                    numero_serie,        
                                    rip,          
                                    str(kg).replace(".", ","),            
                                    str(tonnellaggio).replace(".", ","),
                                    str(rpe_globale).replace(".", ","),          
                                    feedback_globale          
                                ]
                                righe_da_inserire.append(nuova_riga)
                    
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
                        st.warning("⚠️ Non hai compilato nessuna serie valida (Ripetizioni > 0). Nessun dato salvato.")
