import streamlit as st
import streamlit.components.v1 as components
import datetime
import inspect
import re
import gspread
import pandas as pd
import requests
import altair as alt
from google.oauth2.service_account import Credentials
from streamlit_cookies_controller import CookieController

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(
    page_title="Diario Allenamento",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 2. INIZIALIZZA IL CONTROLLER DEI COOKIE
controller = CookieController()

# --- TEMA ENDUFIT: SFONDO SCURO, BLU E GIALLO ---
st.markdown(
    """
    <style>
        /* Forza dark mode nativo su iOS/Android ed elimina qualsiasi fascia bianca sotto/sopra la tastiera */
        :root, html, body, #root,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"],
        section.main,
        [data-testid="stHeader"] {
            color-scheme: dark !important;
            background-color: #050A18 !important;
        }

        /* Nasconde il contenitore dell'iframe JS per evitare spazi extra */
        iframe[height="0"],
        div[data-testid="stElementContainer"]:has(iframe[height="0"]) {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Spazio extra in fondo per poter traslare in alto anche l'ultimo esercizio/campo */
        section[data-testid="stMain"] .block-container,
        div[data-testid="stAppViewContainer"] .block-container,
        .main .block-container {
            padding-bottom: 80vh !important;
        }

        /* Colore testi globali */
        h1, h2, h3, h4, h5, label,
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stMarkdownContainer"] p {
            color: #ffffff !important;
        }

        /* CONTENITORI CAMPI DI INPUT, TEXTAREA E TENDINE */
        div[data-baseweb="input"],
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"],
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"],
        div[data-baseweb="textarea"] > div {
            background-color: #111b33 !important;
            border: 1.5px solid rgba(255, 255, 255, 0.25) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important;
        }

        /* EVIDENZIAZIONE CHIARA DEL CAMPO MENTRE LO STAI COMPILANDO */
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="base-input"]:focus-within,
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="textarea"]:focus-within,
        div[data-baseweb="textarea"] > div:focus-within {
            background-color: #172544 !important;
            border-color: #2997ff !important;
            box-shadow: 0 0 0 3px rgba(41, 151, 255, 0.35) !important;
        }

        /* TESTO E CURSORE BIANCHI SU TUTTI GLI INPUT + ANTI-ZOOM MOBILE */
        input, select, textarea,
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            caret-color: #2997ff !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            background-color: transparent !important;
        }

        /* PULSANTI - / + DEL NUMBER INPUT BEN VISIBILI */
        button[data-testid="stNumberInputStepDown"],
        button[data-testid="stNumberInputStepUp"] {
            background-color: rgba(255, 255, 255, 0.08) !important;
            color: #ffffff !important;
            border: none !important;
        }
        button[data-testid="stNumberInputStepDown"] svg,
        button[data-testid="stNumberInputStepUp"] svg {
            fill: #ffffff !important;
            color: #ffffff !important;
        }

        /* ELEMENTI DENTRO LE TENDINE (SELECTBOX) */
        div[data-baseweb="select"] * {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        ul[role="listbox"], ul[data-baseweb="menu"] {
            background-color: #0f172a !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
        }
        ul[role="listbox"] *, ul[data-baseweb="menu"] * {
            color: #ffffff !important;
        }

        /* PLACEHOLDER LEGGIBILE SU SFONDO SCURO */
        input::placeholder, textarea::placeholder {
            color: rgba(255, 255, 255, 0.45) !important;
            -webkit-text-fill-color: rgba(255, 255, 255, 0.45) !important;
        }

        /* Linee orizzontali */
        hr {
            border-bottom: 1px solid #ffffff !important;
            opacity: 0.3 !important;
            margin: 2em 0 !important;
        }

        /* Icone calendario e tendine bianche */
        div[data-baseweb="icon"] svg {
            fill: #ffffff !important;
            color: #ffffff !important;
        }

        /* Banner Installazione Blu & Giallo ENDUFIT */
        .pwa-banner {
            background: linear-gradient(135deg, rgba(16, 40, 62, 0.92), rgba(11, 28, 46, 0.85));
            backdrop-filter: blur(12px);
            border: 1px solid rgba(245, 208, 0, 0.3);
            color: #ffffff !important;
            padding: 16px;
            border-radius: 16px;
            margin-bottom: 20px;
            font-size: 14px;
            line-height: 1.5;
            text-align: center;
            border-left: 4px solid #2997ff;
            border-right: 4px solid #F5D000;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
        }
        .pwa-banner .hl-blue {
            color: #4db2ff !important;
            font-weight: 700 !important;
        }
        .pwa-banner .hl-yellow {
            color: #F5D000 !important;
            font-weight: 700 !important;
        }

        /* Pulsante Primario */
        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
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
            font-size: 16px !important;
            letter-spacing: 0.5px !important;
            white-space: normal !important;
            line-height: 1.5 !important;
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
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: -15px; margin-bottom: 22px;">
        <svg width="108" height="108" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.45));">
            <circle cx="100" cy="100" r="95" fill="#10283E" stroke="rgba(245, 208, 0, 0.35)" stroke-width="2.5"/>
            <!-- Monogramma EF Giallo -->
            <path d="M 94 38 C 79 38, 65 42, 54 49" fill="none" stroke="#F5D000" stroke-width="8.5" stroke-linecap="butt"/>
            <line x1="94" y1="34" x2="94" y2="166" stroke="#F5D000" stroke-width="8.5" stroke-linecap="butt"/>
            <line x1="56" y1="84" x2="94" y2="84" stroke="#F5D000" stroke-width="8.5" stroke-linecap="butt"/>
            <path d="M 94 162 C 79 162, 65 158, 54 151" fill="none" stroke="#F5D000" stroke-width="8.5" stroke-linecap="butt"/>
            <path d="M 106 38 C 121 38, 135 42, 146 49" fill="none" stroke="#F5D000" stroke-width="8.5" stroke-linecap="butt"/>
            <line x1="106" y1="34" x2="106" y2="165" stroke="#F5D000" stroke-width="8.5" stroke-linecap="butt"/>
            <line x1="106" y1="120" x2="142" y2="120" stroke="#F5D000" stroke-width="8.5" stroke-linecap="butt"/>
        </svg>
        <div style="margin-top: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 21px; letter-spacing: 4.5px; line-height: 1;">
            <span style="color: #ffffff; font-style: italic; font-weight: 400;">ENDU</span><span style="color: #F5D000; font-style: normal; font-weight: 600;">FIT</span>
        </div>
    </div>

    <div class="pwa-banner">
        📲 <span class="hl-yellow">Salva l'app sul telefono!</span><br><br>
        Tocca l'icona di condivisione del browser ( <span class="hl-blue">📤</span> ) e seleziona <span class="hl-yellow">"Aggiungi alla schermata Home"</span> per avere sempre la tua scheda a portata di mano.
    </div>
""",
    unsafe_allow_html=True,
)

# --- SCRIPT PER ICONA HOME SCREEN, DARK VIEWPORT SU iOS E TRASLAZIONE CAMPO SOPRA TASTIERA ---
components.html(
    """
    <script>
    (function() {
        const parentWin = window.parent;
        const parentDoc = parentWin.document;

        function impostaIconaApp(doc) {
            if (!doc || doc.__endufitIconApplied) return;
            doc.__endufitIconApplied = true;
            try {
                const canvas = doc.createElement("canvas");
                canvas.width = 512;
                canvas.height = 512;
                const ctx = canvas.getContext("2d");

                // Sfondo blu navy pieno per icona iOS/Android
                ctx.fillStyle = "#10283E";
                ctx.fillRect(0, 0, 512, 512);

                ctx.strokeStyle = "#F5D000";
                ctx.lineWidth = 22;
                ctx.lineCap = "butt";

                // E specchiata (sinistra)
                ctx.beginPath();
                ctx.moveTo(240, 98);
                ctx.quadraticCurveTo(185, 98, 138, 126);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(240, 88);
                ctx.lineTo(240, 424);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(144, 215);
                ctx.lineTo(240, 215);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(240, 414);
                ctx.quadraticCurveTo(185, 414, 138, 386);
                ctx.stroke();

                // F (destra)
                ctx.beginPath();
                ctx.moveTo(272, 98);
                ctx.quadraticCurveTo(327, 98, 374, 126);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(272, 88);
                ctx.lineTo(272, 422);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(272, 308);
                ctx.lineTo(364, 308);
                ctx.stroke();

                const iconUrl = canvas.toDataURL("image/png");
                doc.querySelectorAll('link[rel="shortcut icon"], link[rel="icon"], link[rel="apple-touch-icon"]').forEach(el => el.remove());

                const appleTouchIcon = doc.createElement("link");
                appleTouchIcon.rel = "apple-touch-icon";
                appleTouchIcon.href = iconUrl;
                doc.head.appendChild(appleTouchIcon);

                const favicon = doc.createElement("link");
                favicon.rel = "icon";
                favicon.type = "image/png";
                favicon.href = iconUrl;
                doc.head.appendChild(favicon);
            } catch (e) {}
        }

        function forzaSfondoScuroDocumento(doc) {
            if (!doc) return;
            try {
                doc.documentElement.style.setProperty("background-color", "#050A18", "important");
                doc.documentElement.style.setProperty("color-scheme", "dark", "important");
                if (doc.body) {
                    doc.body.style.setProperty("background-color", "#050A18", "important");
                    doc.body.style.setProperty("color-scheme", "dark", "important");
                }
                let metaTheme = doc.querySelector('meta[name="theme-color"]');
                if (!metaTheme) {
                    metaTheme = doc.createElement("meta");
                    metaTheme.name = "theme-color";
                    doc.head.appendChild(metaTheme);
                }
                metaTheme.content = "#050A18";

                let metaScheme = doc.querySelector('meta[name="color-scheme"]');
                if (!metaScheme) {
                    metaScheme = doc.createElement("meta");
                    metaScheme.name = "color-scheme";
                    doc.head.appendChild(metaScheme);
                }
                metaScheme.content = "dark";
            } catch (e) {}
        }

        forzaSfondoScuroDocumento(parentDoc);
        impostaIconaApp(parentDoc);
        try {
            if (parentWin.top && parentWin.top.document) {
                forzaSfondoScuroDocumento(parentWin.top.document);
                impostaIconaApp(parentWin.top.document);
            }
        } catch (e) {}

        if (parentWin.__endufitKeyboardScrollV3) return;
        parentWin.__endufitKeyboardScrollV3 = true;

        function getAncestors(el) {
            const list = [];
            let curr = el ? el.parentElement : null;
            while (curr) {
                list.push(curr);
                curr = curr.parentElement;
            }
            return list;
        }

        function portaCampoInAlto(el) {
            if (!el) return;
            const tag = el.tagName;
            if (tag !== "INPUT" && tag !== "TEXTAREA") return;

            if (parentWin.scrollY !== 0) {
                parentWin.scrollTo(0, 0);
            }

            const widgetBox =
                el.closest('[data-testid="stNumberInput"]') ||
                el.closest('[data-testid="stTextArea"]') ||
                el.closest('[data-baseweb="input"]') ||
                el;

            const vv = parentWin.visualViewport;
            const vvTop = vv ? vv.offsetTop : 0;
            const rect = widgetBox.getBoundingClientRect();

            const targetTop = vvTop + 65;
            const delta = rect.top - targetTop;

            if (Math.abs(delta) < 4) return;

            let remaining = delta;
            const candidates = [
                ...getAncestors(widgetBox),
                parentDoc.querySelector('section[data-testid="stMain"]'),
                parentDoc.querySelector('[data-testid="stAppViewContainer"]'),
                parentDoc.querySelector('.stApp'),
                parentDoc.scrollingElement || parentDoc.documentElement,
                parentDoc.body
            ];

            const seen = new Set();
            for (const scroller of candidates) {
                if (!scroller || seen.has(scroller)) continue;
                seen.add(scroller);

                const maxScroll = scroller.scrollHeight - scroller.clientHeight;
                if (maxScroll > 5) {
                    const before = scroller.scrollTop;
                    scroller.scrollTop = Math.max(0, Math.min(maxScroll, before + remaining));
                    const moved = scroller.scrollTop - before;
                    remaining -= moved;
                    if (Math.abs(remaining) < 2) break;
                }
            }
        }

        function schedulaSpostamento(target) {
            if (!target || (target.tagName !== "INPUT" && target.tagName !== "TEXTAREA")) return;
            [50, 180, 350, 550].forEach(delay => {
                setTimeout(() => {
                    if (parentDoc.activeElement === target) {
                        portaCampoInAlto(target);
                    }
                }, delay);
            });
        }

        parentDoc.addEventListener("focusin", function(e) {
            schedulaSpostamento(e.target);
        }, true);

        parentDoc.addEventListener("click", function(e) {
            const inp = e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")
                ? e.target
                : (e.target && e.target.closest ? e.target.closest("input, textarea") : null);
            if (inp) schedulaSpostamento(inp);
        }, true);

        if (parentWin.visualViewport) {
            const onViewportChange = () => {
                if (parentWin.scrollY !== 0) {
                    parentWin.scrollTo(0, 0);
                }
                const active = parentDoc.activeElement;
                if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA")) {
                    portaCampoInAlto(active);
                }
            };
            parentWin.visualViewport.addEventListener("resize", onViewportChange);
            parentWin.visualViewport.addEventListener("scroll", onViewportChange);
        }
    })();
    </script>
    """,
    height=0,
    width=0,
)


# --- 1. AUTENTICAZIONE GOOGLE (IN CACHE) ---
@st.cache_resource(ttl=3600)
def connetti_a_google():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        return gspread.authorize(credentials)
    except Exception:
        return None


client = connetti_a_google()
if not client:
    st.error("Errore di autenticazione con Google. Controlla le chiavi segrete.")
    st.stop()


# --- 2. RECUPERO ID FOGLIO (SENZA RERUN RIPETUTI) ---
id_foglio_url = st.query_params.get("id")
if id_foglio_url:
    st.session_state["id_foglio_attivo"] = id_foglio_url
    if not st.session_state.get("cookie_sincronizzato"):
        id_foglio_salvato = controller.get("id_salvato")
        if id_foglio_url != id_foglio_salvato:
            controller.set("id_salvato", id_foglio_url, max_age=31536000)
        st.session_state["cookie_sincronizzato"] = True
elif "id_foglio_attivo" not in st.session_state:
    id_foglio_salvato = controller.get("id_salvato")
    if id_foglio_salvato:
        st.session_state["id_foglio_attivo"] = id_foglio_salvato

id_foglio = st.session_state.get("id_foglio_attivo")

if not id_foglio:
    st.info("🔄 Sincronizzazione scheda in corso...")
    st.markdown(
        "<p style='text-align: center; color: #475569; font-size: 12px;'>Se la schermata rimane bloccata, assicurati di aver aperto il link originale inviato dal coach almeno una volta.</p>",
        unsafe_allow_html=True,
    )
    st.stop()


# --- 3. CONNESSIONE AI FOGLI (IN CACHE PER EVITARE BLOCCHI API 429) ---
@st.cache_resource(ttl=3600)
def ottieni_fogli_google(foglio_id, _client_gspread):
    sp = _client_gspread.open_by_key(foglio_id)
    fogli_disponibili = sp.worksheets()

    sh_prog = None
    is_fit = False

    for ws in fogli_disponibili:
        if ws.title.lower().strip() == "programma coach":
            sh_prog = ws
            is_fit = True
            break

    if not sh_prog:
        for ws in fogli_disponibili:
            titolo = ws.title.lower().strip()
            if "macrociclo" in titolo or "programma" in titolo:
                sh_prog = ws
                break

    if not sh_prog:
        for ws in fogli_disponibili:
            titolo = ws.title.lower().strip()
            if titolo not in ["diario atleta", "report rpe", "test"]:
                sh_prog = ws
                break

    if not sh_prog:
        sh_prog = fogli_disponibili[0]

    nome_foglio_salvataggio = "Diario Atleta" if is_fit else "Report RPE"

    try:
        sh_stor = sp.worksheet(nome_foglio_salvataggio)
    except gspread.exceptions.WorksheetNotFound:
        sh_stor = sp.add_worksheet(title=nome_foglio_salvataggio, rows="1000", cols="20")

    return sp, sh_prog, sh_stor, is_fit


try:
    spreadsheet, sheet_programma, sheet_storico, is_fitness = ottieni_fogli_google(
        id_foglio, client
    )
except Exception as e:
    st.error(f"Impossibile accedere al foglio. Dettagli: {e}")
    st.stop()


# --- 4. SISTEMI DI CACHE PER I DATI DELLE CELLE ---
@st.cache_data(ttl=300)
def scarica_dati_fogli_v2(id_atleta, _prog, _storico):
    return _prog.get_all_values(), _storico.get_all_values()


dati_programma, dati_storico = scarica_dati_fogli_v2(
    id_foglio, sheet_programma, sheet_storico
)


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
        "french press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Skull-Crusher.gif",
    }

    for chiave, url_gif in db_interno.items():
        if chiave in nome_lower:
            return url_gif

    traduzioni = {
        "military": "military press",
        "tricipiti": "triceps extension",
        "polpacci": "calf",
        "addominali": "crunch",
        "crunch": "crunch",
        "iperestensioni": "hyperextension",
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
    except Exception:
        pass

    return None


# ==========================================
# PARSING DATI (DIVERSO PER FITNESS ED ENDURANCE)
# ==========================================
if is_fitness:
    riga_header = -1
    idx_es, idx_giorno = -1, -1
    idx_serie_coach, idx_rip_coach, idx_carico_coach, idx_recupero = -1, -1, -1, -1
    idx_note = -1

    for i, riga in enumerate(dati_programma):
        riga_pulita = [str(c).lower().strip() for c in riga]
        if "esercizio" in riga_pulita and "giorno" in riga_pulita:
            riga_header = i
            idx_es = riga_pulita.index("esercizio")
            idx_giorno = riga_pulita.index("giorno")
            for j, col_str in enumerate(riga_pulita):
                if "serie target" in col_str or "serie" in col_str:
                    idx_serie_coach = j
                elif (
                    "ripetizioni target" in col_str
                    or "ripetizioni" in col_str
                    or "rip" in col_str
                ):
                    idx_rip_coach = j
                elif "carico" in col_str or "kg" in col_str or "peso" in col_str:
                    idx_carico_coach = j
                elif "recupero" in col_str:
                    idx_recupero = j
                elif "note" in col_str:
                    idx_note = j
            break

    if riga_header == -1:
        st.error(
            "Errore: Impossibile trovare le colonne 'Esercizio' e 'Giorno' nel programma."
        )
        st.stop()

    esercizi_dict = {}
    giorni_disponibili = set()

    for riga in dati_programma[riga_header + 1 :]:
        nome = str(riga[idx_es]).strip() if idx_es < len(riga) else ""
        giorno = (
            str(riga[idx_giorno]).strip().upper() if idx_giorno < len(riga) else ""
        )
        serie_coach = (
            str(riga[idx_serie_coach]).strip()
            if idx_serie_coach != -1 and idx_serie_coach < len(riga)
            else "?"
        )
        rip_coach = (
            str(riga[idx_rip_coach]).strip()
            if idx_rip_coach != -1 and idx_rip_coach < len(riga)
            else "?"
        )
        carico_coach = (
            str(riga[idx_carico_coach]).strip()
            if idx_carico_coach != -1 and idx_carico_coach < len(riga)
            else ""
        )
        recupero_coach = (
            str(riga[idx_recupero]).strip()
            if idx_recupero != -1 and idx_recupero < len(riga)
            else ""
        )
        note_coach = (
            str(riga[idx_note]).strip()
            if idx_note != -1 and idx_note < len(riga)
            else ""
        )

        if nome != "":
            if giorno not in esercizi_dict:
                esercizi_dict[giorno] = []
            esercizi_dict[giorno].append(
                {
                    "nome": nome,
                    "serie_coach": serie_coach,
                    "rip_coach": rip_coach,
                    "carico_coach": carico_coach,
                    "recupero_coach": recupero_coach,
                    "note_coach": note_coach,
                }
            )
            if giorno != "":
                giorni_disponibili.add(giorno)

    giorni_disponibili = sorted(list(giorni_disponibili))

    riga_header_storico = -1
    for i, riga in enumerate(dati_storico):
        riga_lower = [str(c).lower().strip() for c in riga]
        if "esercizio" in riga_lower and any(
            col in riga_lower
            for col in [
                "kg sollevati",
                "kg sollevati / secondi",
                "kg sollevati / secondi / minuti",
                "data",
            ]
        ):
            riga_header_storico = i
            break

    if riga_header_storico != -1 and len(dati_storico) > riga_header_storico + 1:
        header_storico = []
        for h in dati_storico[riga_header_storico]:
            testo_h = str(h).strip()
            testo_lower = testo_h.lower()
            if testo_lower == "data":
                header_storico.append("Data")
            elif testo_lower == "esercizio":
                header_storico.append("Esercizio")
            elif testo_lower in [
                "kg sollevati",
                "kg sollevati / secondi",
                "kg sollevati / secondi / minuti",
            ]:
                header_storico.append("Kg Sollevati / Secondi / Minuti")
            elif testo_lower == "rpe":
                header_storico.append("RPE")
            else:
                header_storico.append(testo_h)

        dati_storico_puliti = [
            riga + [""] * (len(header_storico) - len(riga))
            for riga in dati_storico[riga_header_storico + 1 :]
        ]
        df_storico = pd.DataFrame(dati_storico_puliti, columns=header_storico)
    else:
        df_storico = pd.DataFrame()

    def ottieni_testo_titolo(
        es_nome, serie_coach, rip_coach, carico_coach, recupero_coach
    ):
        s_val = (
            str(serie_coach).strip()
            if str(serie_coach).strip() not in ["", "N/D", "nan", "?"]
            else "?"
        )
        r_val = (
            str(rip_coach).strip()
            if str(rip_coach).strip() not in ["", "N/D", "nan", "?"]
            else "?"
        )
        rec_val = str(recupero_coach).strip()

        sep = " | "

        if s_val != "?" and r_val != "?":
            base_str = f"{s_val} x {r_val}"
        elif s_val != "?":
            base_str = f"{s_val} Set"
        elif r_val != "?":
            base_str = f"{r_val} rip"
        else:
            base_str = "Set liberi"

        str_recupero = (
            f"{sep}{rec_val}" if rec_val not in ["", "N/D", "nan", "?"] else ""
        )

        kg_finale = ""
        c_val = str(carico_coach).strip()

        if c_val not in ["", "N/D", "nan", "-1", "?"]:
            if any(simbolo in c_val.lower() for simbolo in ["kg", "'", '"']):
                kg_finale = f"{sep}{c_val}"
            else:
                kg_finale = f"{sep}{c_val} kg"

        return f"{base_str}{kg_finale}{str_recupero}"

else:
    # --- PARSING ENDURANCE ---
    programma_endurance = {}
    settimana_corrente = None
    giorni_colonne = {}

    for i, riga in enumerate(dati_programma):
        riga_testo_unito = " ".join(
            [str(c).lower().strip() for c in riga if str(c).strip()]
        )

        if not riga_testo_unito:
            continue

        if "settimana" in riga_testo_unito:
            if settimana_corrente and giorni_colonne:
                programma_endurance[settimana_corrente] = list(giorni_colonne.values())

            for cella in riga:
                if "settimana" in str(cella).lower():
                    settimana_corrente = str(cella).strip().replace("\n", " - ")
                    break
            giorni_colonne = {}
            continue

        is_riga_giorni = False
        for cella in riga:
            if str(cella).lower().strip().startswith("giorno "):
                is_riga_giorni = True
                break

        if is_riga_giorni and settimana_corrente:
            for j, cella in enumerate(riga):
                testo = str(cella).strip()
                if testo.lower().startswith("giorno"):
                    giorni_colonne[j] = {
                        "giorno": testo,
                        "titolo": "",
                        "descrizione": [],
                    }
            continue

        if settimana_corrente and giorni_colonne:
            for j in giorni_colonne:
                if j < len(riga):
                    testo = str(riga[j]).strip()
                    if testo:
                        if not giorni_colonne[j]["titolo"]:
                            giorni_colonne[j]["titolo"] = testo
                        else:
                            giorni_colonne[j]["descrizione"].append(testo)

    if settimana_corrente and giorni_colonne:
        programma_endurance[settimana_corrente] = list(giorni_colonne.values())

    if len(dati_storico) > 1:
        header_storico = dati_storico[0]
        dati_storico_puliti = [
            riga + [""] * (len(header_storico) - len(riga))
            for riga in dati_storico[1:]
        ]
        df_storico = pd.DataFrame(dati_storico_puliti, columns=header_storico)
    else:
        df_storico = pd.DataFrame()


# ==========================================
# INTERFACCIA A SCHEDE (TABS)
# ==========================================
tab_dash, tab_workout = st.tabs(
    [
        "📊 Dashboard",
        "🏃‍♂️ Scheda Allenamento" if not is_fitness else "🏋️‍♂️ Scheda Allenamento",
    ]
)


# ==========================================
# SEZIONE 1: DASHBOARD
# ==========================================
with tab_dash:
    if is_fitness:
        st.header("Dashboard Analitica 🚀")
        df_stat = df_storico.copy() if not df_storico.empty else pd.DataFrame()

        if not df_stat.empty and "Data" in df_stat.columns:
            df_stat["Data_dt"] = pd.to_datetime(
                df_stat["Data"], errors="coerce", dayfirst=True
            )
            df_stat = df_stat.dropna(subset=["Data_dt"])

        if df_stat.empty:
            st.info(
                "Nessun allenamento registrato. Inizia ad allenarti per sbloccare le metriche avanzate!"
            )
        else:
            col_rpe = next(
                (col for col in df_stat.columns if "rpe" in str(col).lower()), None
            )
            if col_rpe:
                df_stat["RPE_num"] = pd.to_numeric(
                    df_stat[col_rpe].astype(str).replace(",", ".", regex=True),
                    errors="coerce",
                ).fillna(0)
            else:
                df_stat["RPE_num"] = 0

            tot_allenamenti = df_stat["Data"].nunique()
            c1, c2, c3 = st.columns(3)
            c1.metric("Allenamenti", tot_allenamenti)
            c2.metric("Ultima Sessione", df_stat["Data"].max())
            c3.metric(
                "RPE Medio", f"{df_stat['RPE_num'].mean():.1f}/10" if col_rpe else "N/D"
            )

            st.divider()

            st.subheader("Costanza di Allenamento")
            st.markdown(
                "<p style='font-size: 13px;'>Ogni quadrato rappresenta un giorno. Più è scuro, maggiore è il volume (serie) completato.</p>",
                unsafe_allow_html=True,
            )

            df_giorni = (
                df_stat.groupby("Data_dt").size().reset_index(name="Volume (Serie)")
            )
            heatmap = (
                alt.Chart(df_giorni)
                .mark_rect()
                .encode(
                    x=alt.X(
                        "yearweek(Data_dt):O",
                        title="Settimana dell'anno",
                        axis=alt.Axis(
                            labelAngle=0, labelColor="rgba(255,255,255,0.5)"
                        ),
                    ),
                    y=alt.Y(
                        "day(Data_dt):O",
                        title="",
                        axis=alt.Axis(labelColor="rgba(255,255,255,0.7)"),
                    ),
                    color=alt.Color(
                        "Volume (Serie):Q",
                        scale=alt.Scale(scheme="blues"),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Data_dt:T", title="Data", format="%d %b %Y"),
                        alt.Tooltip("Volume (Serie):Q", title="Serie Totali"),
                    ],
                )
                .properties(height=180)
                .configure_view(strokeWidth=0)
                .configure_axis(grid=False, domain=False)
                .configure(background="transparent")
            )

            st.altair_chart(heatmap, use_container_width=True)
            st.divider()

            st.write("**Fatica Percepita (RPE)**")
            if col_rpe and df_stat["RPE_num"].sum() > 0:
                df_rpe_trend = df_stat.groupby("Data_dt")["RPE_num"].mean().reset_index()
                grafico_rpe = (
                    alt.Chart(df_rpe_trend)
                    .mark_line(
                        color="#e63946",
                        strokeWidth=3,
                        point=alt.OverlayMarkDef(
                            color="#ffffff", size=60, filled=True
                        ),
                    )
                    .encode(
                        x=alt.X(
                            "Data_dt:T",
                            title="",
                            axis=alt.Axis(labelAngle=-45, format="%d %b"),
                        ),
                        y=alt.Y(
                            "RPE_num:Q",
                            title="RPE (0-10)",
                            scale=alt.Scale(domain=[0, 10]),
                        ),
                        tooltip=[
                            alt.Tooltip("Data_dt:T", title="Data", format="%d %b"),
                            alt.Tooltip("RPE_num:Q", title="RPE", format=".1f"),
                        ],
                    )
                    .properties(height=250)
                    .configure_view(strokeWidth=0)
                    .configure_axis(
                        gridColor="rgba(255,255,255,0.1)",
                        domain=False,
                        labelColor="rgba(255,255,255,0.7)",
                    )
                    .configure(background="transparent")
                )
                st.altair_chart(grafico_rpe, use_container_width=True)
            else:
                st.info("Nessun dato RPE registrato.")

            st.divider()

            st.write("**Distribuzione Volume (Serie per Gruppo)**")
            mappa_muscoli = {
                "panca": "Petto",
                "spinte": "Petto",
                "croci": "Petto",
                "chest": "Petto",
                "dip": "Petto",
                "piegament": "Petto",
                "pectoral": "Petto",
                "push up": "Petto",
                "cavi": "Petto",
                "lat": "Schiena",
                "trazion": "Schiena",
                "rematore": "Schiena",
                "pulley": "Schiena",
                "pull down": "Schiena",
                "pull-down": "Schiena",
                "pullup": "Schiena",
                "pull up": "Schiena",
                "row": "Schiena",
                "dorso": "Schiena",
                "schiena": "Schiena",
                "t-bar": "Schiena",
                "chin up": "Schiena",
                "chin-up": "Schiena",
                "squat": "Gambe",
                "pressa": "Gambe",
                "leg press": "Gambe",
                "leg extension": "Gambe",
                "leg curl": "Gambe",
                "affond": "Gambe",
                "lunge": "Gambe",
                "polpacc": "Gambe",
                "stacco": "Gambe",
                "deadlift": "Gambe",
                "calf": "Gambe",
                "glute": "Gambe",
                "hip thrust": "Gambe",
                "bulgarian": "Gambe",
                "abductor": "Gambe",
                "adductor": "Gambe",
                "abd": "Gambe",
                "military": "Spalle",
                "lento": "Spalle",
                "alzate": "Spalle",
                "shoulder": "Spalle",
                "deltoid": "Spalle",
                "face pull": "Spalle",
                "tirate": "Spalle",
                "arnold": "Spalle",
                "curl": "Bicipiti",
                "bicipit": "Bicipiti",
                "bicep": "Bicipiti",
                "hammer": "Bicipiti",
                "french": "Tricipiti",
                "tricipit": "Tricipiti",
                "pushdown": "Tricipiti",
                "push down": "Tricipiti",
                "kickback": "Tricipiti",
                "tricep": "Tricipiti",
                "extension": "Tricipiti",
                "skullcrusher": "Tricipiti",
                "crunch": "Addome",
                "plank": "Addome",
                "addominal": "Addome",
                "sit up": "Addome",
                "sit-up": "Addome",
                "core": "Addome",
                "russian twist": "Addome",
                "leg raise": "Addome",
                "ab roller": "Addome",
                "deadbug": "Addome",
                "side bend": "Addome",
                "tapis roulant": "Cardio",
                "camminata": "Cardio",
                "corsa": "Cardio",
                "run": "Cardio",
                "bike": "Cardio",
                "cyclette": "Cardio",
                "vogatore": "Cardio",
                "rower": "Cardio",
                "ellittica": "Cardio",
                "stairmaster": "Cardio",
                "jump": "Cardio",
                "salto": "Cardio",
                "corda": "Cardio",
                "burpee": "Cardio",
                "jumping jack": "Cardio",
                "skipping": "Cardio",
            }

            def assegna_muscolo(es):
                es_lower = str(es).lower()
                for chiave, muscolo in mappa_muscoli.items():
                    if chiave in es_lower:
                        return muscolo
                return "Altro"

            df_stat["Gruppo"] = df_stat["Esercizio"].apply(assegna_muscolo)
            df_muscoli = (
                df_stat.groupby("Gruppo").size().reset_index(name="Serie Totali")
            )
            df_muscoli = df_muscoli[df_muscoli["Serie Totali"] > 0]

            if not df_muscoli.empty:
                totale_serie = df_muscoli["Serie Totali"].sum()
                df_muscoli["Percentuale"] = (
                    df_muscoli["Serie Totali"] / totale_serie
                ) * 100
                df_muscoli["Label"] = df_muscoli["Percentuale"].apply(
                    lambda x: f"{x:.0f}%" if x >= 3 else ""
                )

                color_scale = alt.Scale(
                    domain=[
                        "Petto",
                        "Schiena",
                        "Gambe",
                        "Spalle",
                        "Bicipiti",
                        "Tricipiti",
                        "Addome",
                        "Cardio",
                        "Altro",
                    ],
                    range=[
                        "#e63946",
                        "#2997ff",
                        "#10b981",
                        "#f59e0b",
                        "#8b5cf6",
                        "#ec4899",
                        "#14b8a6",
                        "#f43f5e",
                        "#64748b",
                    ],
                )

                base_chart = alt.Chart(df_muscoli).encode(
                    theta=alt.Theta(
                        field="Serie Totali", type="quantitative", stack=True
                    ),
                    color=alt.Color(
                        field="Gruppo",
                        type="nominal",
                        scale=color_scale,
                        legend=alt.Legend(
                            title="",
                            labelColor="rgba(255,255,255,0.7)",
                            orient="right",
                            labelFontSize=13,
                        ),
                    ),
                )
                ciambella = base_chart.mark_arc(
                    innerRadius=50, outerRadius=100, stroke="#050A18", strokeWidth=2
                ).encode(
                    tooltip=[
                        alt.Tooltip("Gruppo:N"),
                        alt.Tooltip("Serie Totali:Q", title="Serie Eseguite"),
                    ]
                )
                testo = base_chart.mark_text(
                    radius=125, fill="white", size=12, fontWeight="bold"
                ).encode(text="Label:N")

                grafico_finale = (
                    (ciambella + testo)
                    .properties(height=300)
                    .configure_view(strokeWidth=0)
                    .configure(background="transparent")
                )
                st.altair_chart(grafico_finale, use_container_width=True)
            else:
                st.info("Nessun volume registrato.")

    else:
        st.header("Dashboard Analitica 🏃‍♂️")
        df_stat = df_storico.copy() if not df_storico.empty else pd.DataFrame()

        if not df_stat.empty and len(df_stat.columns) >= 3:
            col_data = next(
                (col for col in df_stat.columns if "data" in str(col).lower()),
                df_stat.columns[0],
            )
            df_stat["Data_dt"] = pd.to_datetime(
                df_stat[col_data], errors="coerce", dayfirst=True
            )
            df_stat = df_stat.dropna(subset=["Data_dt"])

        if df_stat.empty:
            st.info(
                "Nessun allenamento registrato. Registra la tua prima sessione Endurance!"
            )
        else:
            col_rpe = next(
                (col for col in df_stat.columns if "rpe" in str(col).lower()), None
            )
            if col_rpe:
                df_stat["RPE_num"] = pd.to_numeric(
                    df_stat[col_rpe].astype(str).replace(",", ".", regex=True),
                    errors="coerce",
                ).fillna(0)
            else:
                df_stat["RPE_num"] = 0

            tot_allenamenti = len(df_stat)
            c1, c2, c3 = st.columns(3)
            c1.metric("Allenamenti Completati", tot_allenamenti)
            c2.metric("Ultima Sessione", df_stat["Data_dt"].dt.strftime("%d/%m/%Y").max())
            c3.metric("RPE Medio", f"{df_stat['RPE_num'].mean():.1f}/10")

            st.divider()
            st.subheader("Andamento Fatica (RPE)")

            df_rpe_trend = df_stat.groupby("Data_dt")["RPE_num"].mean().reset_index()
            grafico_rpe = (
                alt.Chart(df_rpe_trend)
                .mark_line(
                    color="#2997ff",
                    strokeWidth=3,
                    point=alt.OverlayMarkDef(color="#ffffff", size=60, filled=True),
                )
                .encode(
                    x=alt.X(
                        "Data_dt:T",
                        title="",
                        axis=alt.Axis(labelAngle=-45, format="%d %b"),
                    ),
                    y=alt.Y(
                        "RPE_num:Q",
                        title="RPE (0-10)",
                        scale=alt.Scale(domain=[0, 10]),
                    ),
                    tooltip=[
                        alt.Tooltip("Data_dt:T", title="Data", format="%d %b"),
                        alt.Tooltip("RPE_num:Q", title="RPE", format=".1f"),
                    ],
                )
                .properties(height=250)
                .configure_view(strokeWidth=0)
                .configure_axis(
                    gridColor="rgba(255,255,255,0.1)",
                    domain=False,
                    labelColor="rgba(255,255,255,0.7)",
                )
                .configure(background="transparent")
            )

            st.altair_chart(grafico_rpe, use_container_width=True)


# Helper per gestire st.form_submit_button con chiave univoca su qualsiasi versione di Streamlit
_SUPPORTA_KEY_SUBMIT = "key" in inspect.signature(st.form_submit_button).parameters


def pulsante_form(label, key, tipo="secondary", full_width=True):
    if _SUPPORTA_KEY_SUBMIT:
        return st.form_submit_button(
            label, key=key, type=tipo, use_container_width=full_width
        )
    suffix = "\u200b" * (abs(hash(key)) % 40 + 1)
    return st.form_submit_button(
        f"{label}{suffix}", type=tipo, use_container_width=full_width
    )


# ==========================================
# SEZIONE 2: SCHEDA DI ALLENAMENTO (ISOLATA CON FRAGMENT + FORM)
# ==========================================
@st.fragment
def render_sezione_allenamento():
    if st.session_state.get("dati_salvati", False):
        st.success("Dati inviati al coach! 🔥 Puoi chiudere questa pagina.")
        if st.button("Inserisci un'altra scheda"):
            st.session_state.dati_salvati = False
            st.rerun(scope="fragment")
        return

    st.write("### Registra la sessione di oggi")
    data_sessione = st.date_input("Data della sessione", datetime.date.today())

    if is_fitness:
        if not giorni_disponibili:
            st.warning(
                "Non ci sono esercizi assegnati o manca la lettera del 'Giorno' nel programma."
            )
            return

        giorno_scelto = st.selectbox(
            "Quale scheda (Giorno) vuoi allenare oggi?", giorni_disponibili
        )
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
        st.write("### Scheda")

        with st.form(key=f"form_fitness_{giorno_scelto}", clear_on_submit=False):
            esercizio_da_aggiungere = None
            esercizio_da_rimuovere = None

            for idx_es, es_obj in enumerate(esercizi_assegnati):
                es = es_obj["nome"]
                serie_coach = es_obj["serie_coach"]
                rip_coach = es_obj["rip_coach"]
                carico_coach = es_obj["carico_coach"]
                recupero_coach = es_obj["recupero_coach"]
                note_coach = es_obj.get("note_coach", "")

                if es not in st.session_state.contatore_serie:
                    numeri = re.findall(r"\d+", str(serie_coach))
                    st.session_state.contatore_serie[es] = (
                        max(1, int(numeri[0])) if numeri else 1
                    )

                testo_titolo = ottieni_testo_titolo(
                    es, serie_coach, rip_coach, carico_coach, recupero_coach
                )
                tieni_aperto = st.session_state.es_aperto == es

                st.markdown(
                    "<div style='margin-top: 15px;'></div>", unsafe_allow_html=True
                )

                if note_coach and note_coach.lower() not in ["nan", "n/d"]:
                    titolo_expander = f"{es} — {testo_titolo} | Note esec: {note_coach}"
                else:
                    titolo_expander = f"{es} — {testo_titolo}"

                with st.expander(titolo_expander, expanded=tieni_aperto):
                    img_url = cerca_immagine_esercizio(es)
                    if img_url:
                        st.markdown(
                            f'<div style="display:flex;justify-content:center;margin-bottom:15px;margin-top:10px;"><img src="{img_url}" width="200" style="border-radius:10px;"></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<div style='text-align:center;margin-bottom:15px;margin-top:10px;'><a href='https://www.youtube.com/results?search_query=tutorial+esecuzione+{es.replace(' ', '+')}' target='_blank' style='text-decoration:none;font-size:14px;font-weight:bold;color:#e63946;'>🎥 Cerca Tutorial YouTube</a></div>",
                            unsafe_allow_html=True,
                        )

                    carico_vuoto = str(carico_coach).strip() in [
                        "",
                        "N/D",
                        "nan",
                        "-1",
                        "?",
                    ]
                    ha_minuti = "'" in str(rip_coach)
                    ha_secondi = '"' in str(rip_coach)

                    if not carico_vuoto:
                        etichetta_col2 = "Kg"
                        step_col2 = 0.5
                    else:
                        if ha_minuti:
                            etichetta_col2 = "Minuti"
                            step_col2 = 1.0
                        elif ha_secondi:
                            etichetta_col2 = "Secondi"
                            step_col2 = 5.0
                        else:
                            etichetta_col2 = "Kg"
                            step_col2 = 0.5

                    for i in range(st.session_state.contatore_serie[es]):
                        st.markdown(f"**Serie {i + 1}**")
                        c1, c2 = st.columns(2)

                        key_rip = f"inp_rip_{giorno_scelto}_{es}_{i}"
                        key_kg = f"inp_kg_{giorno_scelto}_{es}_{i}"
                        st.session_state.setdefault(key_rip, 0)
                        st.session_state.setdefault(key_kg, 0.0)

                        with c1:
                            st.number_input(
                                "Ripetizioni",
                                min_value=0,
                                step=1,
                                key=key_rip,
                            )

                        with c2:
                            st.number_input(
                                etichetta_col2,
                                min_value=0.0,
                                step=step_col2,
                                key=key_kg,
                            )

                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if pulsante_form(
                            "➕ Aggiungi Serie",
                            key=f"btn_add_{giorno_scelto}_{idx_es}_{es}",
                            tipo="secondary",
                            full_width=True,
                        ):
                            esercizio_da_aggiungere = es
                    with btn_col2:
                        if pulsante_form(
                            "➖ Rimuovi Serie",
                            key=f"btn_rem_{giorno_scelto}_{idx_es}_{es}",
                            tipo="secondary",
                            full_width=True,
                        ):
                            esercizio_da_rimuovere = es

            st.divider()
            st.write("### Fine Allenamento")
            rpe_globale = st.slider(
                "Fatica percepita (10 = massima, 0 = nessuna)",
                min_value=0.0,
                max_value=10.0,
                value=7.0,
                step=0.5,
            )
            feedback_globale = st.text_area(
                "Feedback / Dolori (Opzionale)",
                placeholder="Annotazioni sull'allenamento appena concluso",
            )

            st.divider()
            inviato = pulsante_form(
                "💾 Consegna Intero Allenamento",
                key=f"btn_submit_all_{giorno_scelto}",
                tipo="primary",
                full_width=True,
            )

        if esercizio_da_aggiungere is not None:
            es = esercizio_da_aggiungere
            idx_nuovo = st.session_state.contatore_serie[es]
            st.session_state[f"inp_rip_{giorno_scelto}_{es}_{idx_nuovo}"] = (
                st.session_state.get(
                    f"inp_rip_{giorno_scelto}_{es}_{idx_nuovo - 1}", 0
                )
            )
            st.session_state[f"inp_kg_{giorno_scelto}_{es}_{idx_nuovo}"] = (
                st.session_state.get(
                    f"inp_kg_{giorno_scelto}_{es}_{idx_nuovo - 1}", 0.0
                )
            )
            st.session_state.contatore_serie[es] += 1
            st.session_state.es_aperto = es
            st.rerun(scope="fragment")

        if esercizio_da_rimuovere is not None:
            es = esercizio_da_rimuovere
            if st.session_state.contatore_serie[es] > 1:
                st.session_state.contatore_serie[es] -= 1
                st.session_state.es_aperto = es
                st.rerun(scope="fragment")

        if inviato:
            righe_da_inserire = []

            if len(dati_storico) == 0:
                righe_da_inserire.append(
                    [
                        "Data",
                        "Esercizio",
                        "Serie",
                        "Ripetizioni",
                        "Kg Sollevati / Secondi / Minuti",
                        "Tonnellaggio",
                        "RPE",
                        "Feedback",
                    ]
                )

            primo_inserimento = True

            for es_obj in esercizi_assegnati:
                es = es_obj["nome"]
                rip_coach = es_obj["rip_coach"]
                carico_coach = es_obj["carico_coach"]

                carico_vuoto = str(carico_coach).strip() in [
                    "",
                    "N/D",
                    "nan",
                    "-1",
                    "?",
                ]
                ha_minuti = "'" in str(rip_coach)
                ha_secondi = '"' in str(rip_coach)

                if not carico_vuoto:
                    suffisso = " kg"
                else:
                    if ha_minuti:
                        suffisso = "'"
                    elif ha_secondi:
                        suffisso = "''"
                    else:
                        suffisso = " kg"

                for i in range(st.session_state.contatore_serie[es]):
                    rip = st.session_state.get(f"inp_rip_{giorno_scelto}_{es}_{i}", 0)
                    kg = st.session_state.get(f"inp_kg_{giorno_scelto}_{es}_{i}", 0.0)

                    kg_base = (
                        str(int(kg))
                        if kg == int(kg)
                        else str(kg).replace(".", ",")
                    )
                    kg_str = f"{kg_base}{suffisso}" if kg > 0 else "0"

                    tonnellaggio_str = (
                        str(int(rip * kg))
                        if (rip * kg) == int(rip * kg)
                        else str(rip * kg).replace(".", ",")
                    )

                    if rip > 0 or kg > 0:
                        if primo_inserimento:
                            val_rpe = str(rpe_globale).replace(".", ",")
                            val_feedback = feedback_globale
                            primo_inserimento = False
                        else:
                            val_rpe = ""
                            val_feedback = ""

                        righe_da_inserire.append(
                            [
                                str(data_sessione),
                                es,
                                i + 1,
                                rip,
                                kg_str,
                                tonnellaggio_str,
                                val_rpe,
                                val_feedback,
                            ]
                        )

            if len(righe_da_inserire) > 0:
                try:
                    sheet_storico.append_rows(
                        righe_da_inserire, value_input_option="USER_ENTERED"
                    )
                    scarica_dati_fogli_v2.clear()
                    st.session_state.dati_salvati = True
                    st.session_state.contatore_serie = {}
                    st.session_state.es_aperto = None
                    st.rerun(scope="fragment")
                except Exception as e:
                    st.error(f"Errore durante il salvataggio: {e}")
            else:
                st.warning(
                    "⚠️ Non hai compilato nessuna serie valida. Nessun dato salvato."
                )

    else:
        # --- MODALITÀ ENDURANCE ---
        if not programma_endurance:
            st.warning(
                "⚠️ Impossibile generare le settimane. Assicurati che nel foglio ci sia scritto 'Settimana' e sotto 'Giorno X' per ogni allenamento."
            )
            return

        settimane_disponibili = list(programma_endurance.keys())
        settimana_scelta = st.selectbox(
            "📅 Seleziona la Settimana", settimane_disponibili
        )

        allenamenti_settimana = programma_endurance[settimana_scelta]
        giorni_validi = [
            a["giorno"]
            for a in allenamenti_settimana
            if a["titolo"] or a["descrizione"]
        ]

        if not giorni_validi:
            st.info("Nessun allenamento programmato per questa settimana.")
            return

        giorno_scelto = st.selectbox(
            "🎯 Quale allenamento vuoi registrare oggi?", giorni_validi
        )
        dettaglio_allenamento = next(
            a for a in allenamenti_settimana if a["giorno"] == giorno_scelto
        )

        st.divider()
        st.write("### 🏃‍♂️ Programma della seduta")

        titolo_all = dettaglio_allenamento["titolo"]
        if titolo_all:
            st.markdown(
                f"<p style='font-family: monospace; font-size: 22px; font-weight: 700; color: #2997ff; letter-spacing: 1px; text-transform: uppercase;'>{titolo_all}</p>",
                unsafe_allow_html=True,
            )

        for desc in dettaglio_allenamento["descrizione"]:
            st.info(desc)

        st.divider()

        with st.form(key="form_endurance_single"):
            st.write("### 📝 Com'è andata?")
            rpe_seduta = st.slider(
                "Fatica percepita (RPE)",
                min_value=0.0,
                max_value=10.0,
                value=7.0,
                step=0.5,
            )
            feedback_seduta = st.text_area(
                "Note / Feedback (Opzionale)",
                placeholder="Sensazioni, fatica, dolori...",
            )

            inviato_end = st.form_submit_button(
                "💾 Salva Allenamento", type="primary", use_container_width=True
            )

        if inviato_end:
            righe_da_inserire = []
            if len(dati_storico) == 0:
                righe_da_inserire.append(["Data", "RPE", "Feedback"])

            righe_da_inserire.append(
                [
                    str(data_sessione),
                    str(rpe_seduta).replace(".", ","),
                    feedback_seduta,
                ]
            )

            try:
                sheet_storico.append_rows(
                    righe_da_inserire, value_input_option="USER_ENTERED"
                )
                scarica_dati_fogli_v2.clear()
                st.session_state.dati_salvati = True
                st.rerun(scope="fragment")
            except Exception as e:
                st.error(f"Errore durante il salvataggio: {e}")


with tab_workout:
    render_sezione_allenamento()
