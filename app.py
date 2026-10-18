import streamlit as st
import datetime
import gspread
import pandas as pd
import requests
from google.oauth2.service_account import Credentials
from streamlit_cookies_controller import CookieController

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(
    page_title="ENDUFIT - Diario", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. INIZIALIZZA IL CONTROLLER DEI COOKIE
controller = CookieController()

# --- TEMA ENDUFIT: SFONDO SCURO, GLASSMORPHISM, BLU E ROSSO ---
st.markdown("""
    <style>
        /* 1. Sfondo principale e Topbar */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #050A18 !important;
            color: #ffffff !important;
        }
        
        /* 2. Colore testi globali */
        h1, h2, h3, h4, h5, label, p, span, div {
            color: #ffffff !important;
        }
        p { color: rgba(255,255,255,0.7) !important; }

        /* 3. Banner Installazione stile Apple Glass */
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
        }

        /* 4. Pulsante Primario (Es. Consegna Allenamento) - Rosso FIT */
        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: linear-gradient(to right, #e63946, #b01e28) !important;
            color: white !important;
            border: none !important;
            border-radius: 50px !important; /* Arrotondato a pillola */
            font-weight: bold !important;
            box-shadow: 0 4px 15px rgba(230, 57, 70, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(230, 57, 70, 0.5) !important;
        }

        /* 5. Pulsante Secondario (Es. Aggiungi Serie) - Blu ENDU Outline */
        div[data-testid="stFormSubmitButton"] > button[kind="secondary"],
        div.stButton > button[kind="secondary"] {
            background-color: rgba(41, 151, 255, 0.1) !important;
            color: #2997ff !important;
            border: 1px solid rgba(41, 151, 255, 0.4) !important;
            border-radius: 50px !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stFormSubmitButton"] > button[kind="secondary"]:hover {
            background-color: rgba(41, 151, 255, 0.2) !important;
            border: 1px solid #2997ff !important;
        }

        /* 6. Expanders (I box degli esercizi) - Effetto Vetro */
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
        div[data-testid="stExpander"] svg {
            color: #2997ff !important; /* Freccetta blu */
        }

        /* 7. Input Fields (Numeri, Testi, Select) */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border-radius: 10px !important;
        }
        
        /* 8. Tabs (Dashboard / Scheda) */
        button[data-baseweb="tab"] p {
            font-weight: bold !important;
            color: rgba(255,255,255,0.5) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] p {
            color: #2997ff !important; /* Tab attivo Blu */
        }
        div[data-baseweb="tab-highlight"] {
            background-color: #2997ff !important;
        }

        /* 9. Nascondi Banner PWA se installato */
        @media all and (display-mode: standalone) {
            .pwa-banner { display: none !important; }
        }
    </style>
    
    <div class="pwa-banner">
        📲 <b style="color: white;">Porta ENDUFIT in palestra!</b><br><br>
        Tocca l'icona di condivisione ( 📤 ) e seleziona <b style="color: #2997ff;">"Aggiungi alla schermata Home"</b> per usare l'app a schermo intero.
    </div>
""", unsafe_allow_html=True)
