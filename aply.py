import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
from google import genai

st.set_page_config(
    page_title="Flota Varela",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- CONFIGURACIÓN VISUAL ---
CONF = {
    "COLOR_PRINCIPAL": "#008F7A",
    "COLOR_SECUNDARIO": "#00c49a",
    "COLOR_ROJO": "#E05C5C",
    "COLOR_VERDE": "#4CAF7D",
    "LOGO_URL": "https://i.ibb.co/chpfBP5X/Logo1.png",
    "BANNER_URL": "https://i.ibb.co/Fq6mSJgm/Secretar-a-de-Obras-Servicios-P-blicos-Ambiente-y-Planificaci-n-Urbana.png",
}

def inject_custom_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

        /* === GLOBAL === */
        html, body, [data-testid="stAppViewContainer"] {{
            background-color: #009472 !important;
            font-family: 'Inter', sans-serif !important;
        }}
        [data-testid="stAppViewContainer"] > section > div {{
            padding-top: 0 !important;
        }}
        .main .block-container {{
            max-width: 1200px;
            width: 100% !important;
            padding: 0 !important;
            background-color: #f5fbfa !important;
            margin: 40px auto !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
        }}
        /* Banner fully fluid - scales with zoom */
        .green-top-bar, .green-top-bar img {{
            min-width: 0 !important;
            min-height: 0 !important;
        }}

        /* === BANNER === */
        .green-top-bar {{
            background-color: {CONF['COLOR_PRINCIPAL']};
            width: 100%;
            aspect-ratio: 512 / 55;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
            overflow: hidden;
        }}
        .green-top-bar img {{ width: 100%; height: 100%; object-fit: cover; }}
        .banner-accent-line {{
            height: 4px;
            background: linear-gradient(90deg, {CONF['COLOR_PRINCIPAL']}, {CONF['COLOR_SECUNDARIO']});
            width: 100%;
        }}

        /* === PAGE HEADER === */
        .page-header {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 18px 32px 14px 32px;
            background: transparent;
            border-bottom: 1px solid #E8EEEC;
        }}
        .page-header img {{ height: 40px; width: auto; }}
        .page-header-titles h1 {{
            margin: 0 !important; padding: 0 !important;
            font-size: 22px !important; font-weight: 800 !important;
            color: {CONF['COLOR_PRINCIPAL']} !important;
            text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.1 !important;
        }}
        .page-header-titles span {{
            font-size: 11px; color: #9aaba6; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1.2px;
        }}

        /* === TABS === */
        .stTabs [data-baseweb="tab-list"] {{
            padding: 0 32px !important;
            background-color: transparent !important;
            border-bottom: 2px solid #E8EEEC !important;
            gap: 4px;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 46px !important; font-weight: 600 !important;
            font-size: 13px !important; color: #9aaba6 !important;
            padding: 0 18px !important; letter-spacing: 0.3px;
        }}
        .stTabs [aria-selected="true"] {{
            color: {CONF['COLOR_PRINCIPAL']} !important;
            border-bottom: 3px solid {CONF['COLOR_PRINCIPAL']} !important;
            background-color: transparent !important;
        }}
        .stTabs [data-baseweb="tab-panel"] {{ padding: 24px 32px !important; }}

        /* === KPI CARDS === */
        .stat-container {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-box-flask {{
            background: #ffffff;
            padding: 22px 16px;
            text-align: center;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,143,122,0.08), 0 1px 3px rgba(0,0,0,0.06);
            border: 1px solid #E8EEEC;
            transition: box-shadow 0.2s;
        }}
        .stat-box-flask:hover {{ box-shadow: 0 6px 20px rgba(0,143,122,0.14); }}
        .stat-val-flask {{
            display: block; font-size: 34px; font-weight: 800;
            color: {CONF['COLOR_PRINCIPAL']}; line-height: 1;
        }}
        .stat-label-flask {{
            font-size: 11px; color: #9aaba6; font-weight: 600;
            margin-top: 6px; display: block; text-transform: uppercase; letter-spacing: 0.8px;
        }}

        /* === STATUS BADGES === */
        .badge-activo {{
            display: inline-block; padding: 3px 9px; border-radius: 20px;
            background-color: #E6F7F1; color: #1A7A55;
            font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.6px;
        }}
        .badge-inactivo {{
            display: inline-block; padding: 3px 9px; border-radius: 20px;
            background-color: #FDECEA; color: #B93333;
            font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.6px;
        }}

        /* === INPUTS (modo claro) === */
        input[type="text"], .stTextInput input {{
            background-color: #ffffff !important; color: #2c3e35 !important;
            border: 1px solid #D1DDD9 !important; border-radius: 6px !important;
            font-family: 'Inter', sans-serif !important; font-size: 12px !important;
        }}
        textarea {{
            font-family: 'Courier New', monospace !important;
            background-color: #fafafa !important; color: #2c3e35 !important;
            border: 1px solid #D1DDD9 !important; border-radius: 8px !important;
        }}

        /* === BUTTONS === */
        div.stButton > button {{
            background-color: {CONF['COLOR_PRINCIPAL']} !important;
            color: white !important; border-radius: 7px !important;
            border: none !important; font-weight: 700 !important;
            font-size: 12px !important; letter-spacing: 0.8px !important;
            text-transform: uppercase !important;
            transition: background-color 0.2s, transform 0.15s, box-shadow 0.2s !important;
        }}
        div.stButton > button:hover {{
            background-color: #007060 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,143,122,0.30) !important;
        }}

        /* === DIVIDER === */
        hr {{ border-color: #E8EEEC !important; }}

        /* === FLEET TABLE === */
        .fleet-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            font-family: 'Inter', sans-serif;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 0;
        }}
        .fleet-table thead tr {{
            background-color: {CONF['COLOR_PRINCIPAL']};
            color: #ffffff;
        }}
        .fleet-table thead th {{
            padding: 10px 8px;
            font-weight: 800;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            white-space: nowrap;
        }}
        .fleet-table tbody tr {{
            border-bottom: 1px solid #EEF3F1;
            transition: background-color 0.15s;
        }}
        .fleet-table tbody tr:nth-child(even) {{
            background-color: #F7FBFA;
        }}
        .fleet-table tbody tr:nth-child(odd) {{
            background-color: #FFFFFF;
        }}
        .fleet-table tbody tr:hover {{
            background-color: #E8F5F2;
        }}
        .fleet-table td {{
            padding: 9px 8px;
            vertical-align: middle;
            color: #2c3e35;
            font-weight: 500;
        }}
        .fleet-table td.td-unidad {{
            font-weight: 800;
            color: {CONF['COLOR_PRINCIPAL']};
            font-size: 12px;
        }}
        .fleet-table td.td-secondary {{
            color: #6B8A82;
            font-size: 11px;
        }}
        /* Input inline dentro de la tira de controles */
        .diag-input input {{
            padding: 4px 8px !important;
            font-size: 12px !important;
            height: 32px !important;
            border: 1px solid #D1DDD9 !important;
            border-radius: 5px !important;
            background-color: #fff !important;
        }}
        /* Botón compacto de actualización */
        .btn-actualizar > button {{
            padding: 4px 10px !important;
            font-size: 11px !important;
            height: 32px !important;
            background-color: {CONF['COLOR_PRINCIPAL']} !important;
            color: white !important;
            border-radius: 5px !important;
            border: none !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            width: 100% !important;
        }}
        .btn-actualizar > button:hover {{
            background-color: #007060 !important;
        }}
        /* Fila de controles (inputs + botón) */
        .control-strip {{
            background-color: #F0F7F5;
            border-bottom: 1px solid #DDE9E6;
            padding: 4px 0;
        }}

        /* === HIDE STREAMLIT CHROME === */
        #MainMenu, footer, header {{ visibility: hidden; }}
        [data-testid="stToolbar"] {{ display: none; }}
    </style>
    """, unsafe_allow_html=True)

def render_banner():
    """Banner institucional estático (escala con el viewport)."""
    st.markdown(f"""
    <div class="green-top-bar">
        <img src="{CONF['BANNER_URL']}" style="width:100%;height:auto;display:block;">
    </div>
    <div class="banner-accent-line"></div>
    """, unsafe_allow_html=True)

def render_page_title(title):
    """Título de página dinámico — llamar dentro de cada tab."""
    st.markdown(f"""
    <div class="page-header">
        <img src="{CONF['LOGO_URL']}">
        <div class="page-header-titles">
            <h1>{title}</h1>
            <span>Municipalidad de Florencio Varela</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- CONFIGURACIÓN ---
# Ahora la conexión se hace a través de st.secrets["spreadsheet_id"] y API
# La tabla de contratados vive en la hoja "AUX3" del mismo Google Sheets.

# --- MAPEO DE GÉNERO PARA UNIDADES ---
# Esto define si el estado termina en "O" (Masculino) o "A" (Femenino)
UNIDADES_FEMENINAS = [
    "APLANADORA", "BATEA", "CAMIONETA", "CHIPEADORA", "DESMALEZADORA", 
    "EXCAVADORA", "MINICARGADORA", "MOTONIVELADORA", "PALA CARGADORA", 
    "RETROEXCAVADORA", "TERMINADORA DE ASFALTO"
]

AREAS_SSPP = ["EQUIPOS VIALES", "HIGIENE URBANA", "ESPACIOS VERDES", "ALUMBRADO", "CEMENTERIO"]

# --- FUNCIONES DE CARGA ---
@st.cache_data(ttl=30)
def load_data():
    if "gcp_service_account" in st.secrets and "spreadsheet_id" in st.secrets:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet("AUX2")
        data = pd.DataFrame(sheet.get_all_records())
    else:
        st.error("No se encontraron las credenciales de GSheets en st.secrets.")
        return pd.DataFrame()
        
    data.columns = data.columns.str.strip().str.upper()
    data = data.loc[:, ~data.columns.duplicated()].copy() # Evitar duplicados por normalización
    if 'EX' in data.columns:
        data['EX'] = data['EX'].fillna('').astype(str).str.replace('.0', '', regex=False)
    for col in ['TIPO', 'ESTADO', 'ÁREA']:
        if col in data.columns:
            data[col] = data[col].fillna('').astype(str).str.strip().str.upper()
    return data.fillna("")

def obtener_terminacion(tipo):
    return "A" if tipo.upper() in UNIDADES_FEMENINAS else "O"

@st.cache_data(ttl=30)
def load_data_contratados():
    try:
        if "gcp_service_account" in st.secrets and "spreadsheet_id" in st.secrets:
            scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
            client = gspread.authorize(creds)
            sheet_c = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet("AUX3")
            df_c = pd.DataFrame(sheet_c.get_all_records())
            if df_c.empty:
                return pd.DataFrame(columns=['TIPO_C', 'AREA_C', 'CANTIDAD_C'])
            df_c.columns = df_c.columns.str.strip().str.upper()
            df_c = df_c.loc[:, ~df_c.columns.duplicated()].copy() # Evitar duplicados iniciales
            # Renombrar si las columnas no tienen sufijo _C
            col_map = {}
            for c in df_c.columns:
                if c in ('TIPO', 'TIPO_C'):
                    col_map[c] = 'TIPO_C'
                elif c in ('AREA', 'ÁREA', 'AREA_C', 'ÁREA_C'):
                    col_map[c] = 'AREA_C'
                elif c in ('CANTIDAD', 'CANTIDAD_C'):
                    col_map[c] = 'CANTIDAD_C'
            df_c = df_c.rename(columns=col_map)
            df_c = df_c.loc[:, ~df_c.columns.duplicated()].copy() # Evitar duplicados tras rename (ej: TIPO y TIPO_C)
            if not all(col in df_c.columns for col in ['TIPO_C', 'AREA_C', 'CANTIDAD_C']):
                st.warning("La hoja AUX2 no tiene las columnas esperadas (TIPO_C, AREA_C, CANTIDAD_C).")
                return pd.DataFrame(columns=['TIPO_C', 'AREA_C', 'CANTIDAD_C'])
            df_c['TIPO_C'] = df_c['TIPO_C'].fillna('').astype(str).str.strip().str.upper()
            df_c['AREA_C'] = df_c['AREA_C'].fillna('').astype(str).str.strip().str.upper()
            df_c['CANTIDAD_C'] = pd.to_numeric(df_c['CANTIDAD_C'], errors='coerce').fillna(0).astype(int)
            return df_c[['TIPO_C', 'AREA_C', 'CANTIDAD_C']]
    except Exception as e:
        st.warning(f"No se pudo cargar la tabla de contratados (AUX3): {e}")
    return pd.DataFrame(columns=['TIPO_C', 'AREA_C', 'CANTIDAD_C'])

def pluralizar_palabra(palabra):
    palabra_lower = palabra.lower()
    vocales_acentuadas = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'}
    def quitar_tilde(texto):
        for acentuada, sin_acento in vocales_acentuadas.items():
            texto = texto.replace(acentuada, sin_acento)
            texto = texto.replace(acentuada.upper(), sin_acento.upper())
        return texto

    if palabra_lower.endswith(('a', 'e', 'i', 'o', 'u', 'á', 'é', 'í', 'ó', 'ú')):
        if palabra_lower[-1] in ['í', 'ú']:
            res = quitar_tilde(palabra) + "ES" if palabra.isupper() else quitar_tilde(palabra) + "es"
            return res
        return palabra + "S" if palabra.isupper() else palabra + "s"
    elif palabra_lower.endswith('z'):
        res = palabra[:-1] + "CES" if palabra.isupper() else palabra[:-1] + "ces"
        return quitar_tilde(res)
    elif palabra_lower.endswith('s') or palabra_lower.endswith('x'):
        return palabra
    else:
        return quitar_tilde(palabra) + "ES" if palabra.isupper() else quitar_tilde(palabra) + "es"

def pluralizar(texto):
    palabras = texto.split()
    return " ".join([pluralizar_palabra(p) for p in palabras])

def format_totales(tipo, cant_p, cant_c):
    sufijo = "A" if tipo.upper() in UNIDADES_FEMENINAS else "O"
    parts = []
    if cant_p > 0:
        word = f"PROPI{sufijo}"
        if cant_p > 1: word += "S"
        parts.append(f"{cant_p} {word}")
    if cant_c > 0:
        word = f"CONTRATAD{sufijo}"
        if cant_c > 1: word += "S"
        parts.append(f"{cant_c} {word}")
    
    if not parts: return ""
    return " - (" + " + ".join(parts) + ")"

# --- CONFIGURACIÓN GEMINI (SDK google-genai 2026) ---
import time
import random
from typing import Optional

def ask_gemini(prompt: str, system_instruction: str = "", model_name: str = "gemini-3.1-flash-lite") -> str:
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: API Key no configurada."
    
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    config = {
        "system_instruction": system_instruction,
        "thinking_config": {"thinking_level": "minimal"},
        "temperature": 0.1,
    }

    for attempt in range(3):
        try:
            response = client.models.generate_content(model=model_name, contents=prompt, config=config)
            return response.text
        except Exception as e:
            err = str(e)
            if "429" in err: # Rate Limit (15 RPM)
                time.sleep((2 ** attempt) + random.uniform(0, 1))
                continue
            if "404" in err and model_name != "gemini-2.5-flash":
                return ask_gemini(prompt, system_instruction, model_name="gemini-2.5-flash")
            return f"Error en API: {e}"
    return "Error: Límite de reintentos (429) excedido."

def clean_fleet_context(df: pd.DataFrame) -> str:
    """Optimiza tokens mapeando columnas críticas y validando estados."""
    mapping = {'UNIDAD': 'ID_UNIDAD', 'ESTADO': 'ESTADO', 'TIPO': 'TIPO_MAQUINARIA', 'ULTIMA_REV': 'ULTIMA_REV'}
    cols = [c for c in mapping.keys() if c in df.columns]
    df_mini = df[cols].rename(columns={k: v for k, v in mapping.items() if k in df.columns}).copy()
    
    # Validador estricto INACTIVO vs ACTIVO
    if 'ESTADO' in df_mini.columns:
        df_mini['ESTADO'] = df_mini['ESTADO'].apply(
            lambda x: "INACTIVO" if "INACTIVO" in str(x).upper() else ("ACTIVO" if "ACTIVO" in str(x).upper() else x)
        )
    return df_mini.to_markdown(index=False)

def get_resumen_ejecutivo(df: pd.DataFrame) -> str:
    """Agrupa unidades por estado crítico en una sola llamada."""
    ctx = clean_fleet_context(df)
    sys_ins = "Eres un analista de flota. Responde solo con una tabla Markdown JSON compacto. Sin prosa introductoria."
    prompt = f"Genera un resumen ejecutivo agrupando unidades por estado crítico:\n\n{ctx}"
    return ask_gemini(prompt, system_instruction=sys_ins)

def get_fleet_proposals(df_inactivas: pd.DataFrame) -> str:
    """Genera propuestas y consultas para todas las unidades inactivas en una sola petición."""
    if df_inactivas.empty:
        return "No hay unidades inactivas para analizar."
    
    ctx = clean_fleet_context(df_inactivas)
    sys_ins = (
        "Eres un supervisor de taller experto. Analiza el estado de las unidades inactivas y propón "
        "acciones concretas o preguntas clave para agilizar la reparación. "
        "Responde con un formato de lista claro, ideal para leer rápidamente en WhatsApp."
    )
    prompt = f"Analiza estas unidades inactivas y dame propuestas o recordatorios de intervención:\n\n{ctx}"
    return ask_gemini(prompt, system_instruction=sys_ins)

# --- HELPERS GSHEETS ---
def get_gsheet_client():
    if "gcp_service_account" in st.secrets:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds)
    return None

def update_diagnostico_sheet(unidad, nuevo_diagnostico):
    try:
        client = get_gsheet_client()
        if client and "spreadsheet_id" in st.secrets:
            sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet("AUX2")
            cell = sheet.find(unidad)
            if cell:
                headers = sheet.row_values(1)
                diag_col = next((i + 1 for i, h in enumerate(headers) if h.upper().strip() == "DIAGNÓSTICO"), None)
                if diag_col:
                    sheet.update_cell(cell.row, diag_col, nuevo_diagnostico)
                    return True
    except Exception as e:
        st.error(f"Error al actualizar GSheets: {e}")
    return False

# --- INTERFAZ ---
render_banner()

try:
    df = load_data()
    df_contratados = load_data_contratados()
    
    # Resumen Ejecutivo (Stats) - Disponible para todas las pestañas según la imagen
    total_all = len(df)
    activos_all = len(df[df['ESTADO'].isin(['ACTIVO', 'ACTIVA'])])
    inactivos_all = total_all - activos_all
    percent_all = int((activos_all/total_all*100)) if total_all else 0

    st.markdown(f"""
    <div class="stat-container">
        <div class="stat-box-flask"><span class="stat-val-flask">{total_all}</span><span class="stat-label-flask">Unidades</span></div>
        <div class="stat-box-flask"><span class="stat-val-flask" style="color:{CONF['COLOR_VERDE']}">{activos_all}</span><span class="stat-label-flask">Activos</span></div>
        <div class="stat-box-flask"><span class="stat-val-flask" style="color:{CONF['COLOR_ROJO']}">{inactivos_all}</span><span class="stat-label-flask">Inactivos</span></div>
        <div class="stat-box-flask"><span class="stat-val-flask">{percent_all}%</span><span class="stat-label-flask">Operatividad</span></div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Reporte Individual", "Parte Diario", "Ida y Vuelta", "Seguimiento"])
    
    with tab1:
        render_page_title("REPORTE INDIVIDUAL")
        # --- SELECTORES DE FILTRADO ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tipos_disponibles = sorted(df['TIPO'].unique()) if not df.empty and 'TIPO' in df.columns else []
            tipo_sel = st.multiselect("Tipo de Unidad:", tipos_disponibles, default=[tipos_disponibles[0]] if len(tipos_disponibles) > 0 else [])
        
        with col2:
            filtro_area = st.selectbox("Filtrar por Área:", 
                                       ["TODAS", "SERVICIOS PÚBLICOS", "AMBIENTE", "SECRETARÍA", "ARQUITECTURA", "DELEGACIONES", "OBRAS"])
        
        with col3:
            filtro_estado = st.selectbox("Filtrar por Estado:", ["TODOS", "ACTIVOS", "INACTIVOS"])
    
        if st.button('Generar Informe para WhatsApp 📋'):
            if not tipo_sel:
                st.warning("Debe seleccionar al menos un Tipo de Unidad.")
            else:
                # 1. Filtrado Base (Tipo)
                df_f = df[df['TIPO'].isin(tipo_sel)].copy()
                
                # 2. Filtrado por Área
                if filtro_area == "SERVICIOS PÚBLICOS":
                    df_f = df_f[df_f['ÁREA'].isin(AREAS_SSPP)]
                elif filtro_area == "DELEGACIONES":
                    df_f = df_f[df_f['ÁREA'].str.contains("DELEGACI", na=False)]
                elif filtro_area == "OBRAS":
                    df_f = df_f[~df_f['ÁREA'].str.contains("DELEGACI", na=False)]
                elif filtro_area != "TODAS":
                    df_f = df_f[df_f['ÁREA'] == filtro_area]
                    
                # 3. Filtrado por Estado
                if filtro_estado == "ACTIVOS":
                    df_f = df_f[df_f['ESTADO'].isin(['ACTIVO', 'ACTIVA'])]
                elif filtro_estado == "INACTIVOS":
                    df_f = df_f[df_f['ESTADO'].isin(['INACTIVO', 'INACTIVA'])]
                    
                if df_f.empty:
                    st.warning("No se encontraron unidades con los filtros seleccionados.")
                else:
                    total_u = len(df_f)
                    activos_u = len(df_f[df_f['ESTADO'].isin(['ACTIVO', 'ACTIVA'])])
                    percent = int((activos_u/total_u*100)) if total_u else 0
                    fecha_hoy = datetime.now().strftime("%d/%m/%y")
                    tipos_str = ", ".join(tipo_sel)
                    reporte = f"Fecha: {fecha_hoy}\n\n"
                    reporte += f"Tipos: *{tipos_str} ({activos_u} de {total_u} activos)*\n"

                    st.markdown(f"""
                    <div class="stat-container">
                        <div class="stat-box-flask"><span class="stat-val-flask">{total_u}</span><span class="stat-label-flask">Unidades</span></div>
                        <div class="stat-box-flask"><span class="stat-val-flask" style="color:{CONF['COLOR_VERDE']}">{activos_u}</span><span class="stat-label-flask">Activas</span></div>
                        <div class="stat-box-flask"><span class="stat-val-flask" style="color:{CONF['COLOR_ROJO']}">{total_u-activos_u}</span><span class="stat-label-flask">Inactivas</span></div>
                        <div class="stat-box-flask"><span class="stat-val-flask">{percent}%</span><span class="stat-label-flask">Operatividad</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                    def formato_fila(row):
                        val_est = str(row['ESTADO']).upper()
                        is_ok = val_est in ['ACTIVO', 'ACTIVA']
                        emoji = "✅" if is_ok else "🔺"
                        sufijo = obtener_terminacion(row['TIPO'])
                        txt_estado = f"Operativ{sufijo.lower()}" if is_ok else f"INACTIV{sufijo}"
                        ex_val = str(row.get('EX', '')).strip()
                        nombre_ex = f" (ex {ex_val})" if ex_val != "" and ex_val.lower() != "nan" else ""
                        diag = row.get('DIAGNÓSTICO', '')
                        return f"\n- *{row['UNIDAD']}*{nombre_ex} ({row.get('MARCA', '')} {row.get('MODELO', '')}) {emoji} {txt_estado}: {diag}\n"
                    
                    df_f['REPORTE_TXT'] = df_f.apply(formato_fila, axis=1)
                    areas_visibles = df_f['ÁREA'].unique()
                    for area in areas_visibles:
                        sub_df = df_f[df_f['ÁREA'] == area]
                        activos_area = len(sub_df[sub_df['ESTADO'].isin(['ACTIVO', 'ACTIVA'])])
                        total_area = len(sub_df)
                        reporte += f"\n*{area} ({activos_area} de {total_area} activos):*\n"
                        reporte += sub_df['REPORTE_TXT'].str.cat(sep='')
        
                    # --- GUARDAR LOG EN GOOGLE SHEETS ---
                    if "gcp_service_account" in st.secrets and "spreadsheet_id" in st.secrets:
                        try:
                            scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
                            client = gspread.authorize(creds)
                            spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
                            
                            try:
                                worksheet_log = spreadsheet.worksheet("Historial")
                            except gspread.exceptions.WorksheetNotFound:
                                worksheet_log = spreadsheet.add_worksheet(title="Historial", rows="1000", cols="10")
                                worksheet_log.append_row(["Fecha y Hora", "Tipos de Unidad", "Filtro Área", "Filtro Estado", "Total Unidades", "Activos", "Reporte Generado"])
                            
                            hora_actual = datetime.now().strftime("%d/%m/%y %H:%M:%S")
                            worksheet_log.append_row([hora_actual, tipos_str, filtro_area, filtro_estado, total_u, activos_u, reporte])
                            st.success("Log guardado exitosamente en Google Sheets ('Historial').")
                        except Exception as ex_log:
                            st.warning(f"No se pudo guardar el log en GSheets. Detalle: {ex_log}")
        
                    # --- RENDERIZADO Y COPIADO ---
                    st.markdown("### 📋 Informe Generado")
                    st.text_area(label="Contenido final", value=reporte, height=450, label_visibility="collapsed")
                    
                    # Botón de Copiado con JS
                    copy_js = f"""
                    <button onclick="copyToClipboard()" style="
                        width: 100%; background-color: {CONF['COLOR_VERDE']}; color: white; border: none; 
                        padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; text-transform: uppercase; letter-spacing: 1px;">
                        Copiar al Portapapeles 📋
                    </button>
                    <script>
                    function copyToClipboard() {{
                        const text = `{reporte.replace('`', '\\`')}`;
                        const el = document.createElement('textarea');
                        el.value = text;
                        document.body.appendChild(el);
                        el.select();
                        document.execCommand('copy');
                        document.body.removeChild(el);
                        alert('Informe copiado.');
                    }}
                    </script>
                    """
                    components.html(copy_js, height=70)

    with tab2:
        render_page_title("PARTE DIARIO")
        # Filtrar para que NO CUENTEN las delegaciones en el Parte Diario
        df_diario = df[~df['ÁREA'].str.contains("DELEGACI", na=False)].copy() if not df.empty else df
        df_c_diario = df_contratados[~df_contratados['AREA_C'].str.contains("DELEGACI", na=False)].copy() if not df_contratados.empty else df_contratados

        st.markdown("### Seleccionar tipos para el Parte Diario")
        tipos_propios = set(df_diario['TIPO'].unique()) if not df_diario.empty and 'TIPO' in df_diario.columns else set()
        tipos_contra = set(df_c_diario['TIPO_C'].unique()) if not df_c_diario.empty and 'TIPO_C' in df_c_diario.columns else set()
        tipos_unificados = sorted(list(tipos_propios.union(tipos_contra)))
        tipos_unificados = [t for t in tipos_unificados if str(t).strip() != ""]

        col_d1, col_d2 = st.columns([3, 1])
        with col_d1:
            tipo_sel_diario = st.multiselect("Seleccionar Tipos de Unidad:", tipos_unificados, default=[], key="ms_diario")
        with col_d2:
            resumen_ia = st.checkbox("Resumen ✨", value=False, help="Usa IA para resumir diagnósticos de unidades inactivas.")

        if st.button('Generar Parte Diario 📋'):
            if not tipo_sel_diario:
                st.warning("Debe seleccionar al menos un Tipo de Unidad.")
            else:
                fecha_diario = datetime.now().strftime("%d/%m/%y")
                reporte_diario = f"*PARTE DIARIO {fecha_diario}*\n\n"

                for tipo in tipo_sel_diario:
                    # PROPIOS OPERATIVOS
                    cant_propios = 0
                    df_p_op = pd.DataFrame()
                    if not df_diario.empty and 'TIPO' in df_diario.columns:
                        df_p_tipo = df_diario[df_diario['TIPO'] == tipo]
                        df_p_op = df_p_tipo[df_p_tipo['ESTADO'].isin(['ACTIVO', 'ACTIVA'])]
                        cant_propios = len(df_p_op)
                    
                    # CONTRATADOS
                    cant_contratados = 0
                    df_c_tipo = pd.DataFrame()
                    if not df_c_diario.empty and 'TIPO_C' in df_c_diario.columns:
                        df_c_tipo = df_c_diario[df_c_diario['TIPO_C'] == tipo]
                        cant_contratados = df_c_tipo['CANTIDAD_C'].sum()
                    
                    total_operativos = cant_propios + cant_contratados
                    tipo_plural = pluralizar(tipo).upper()
                    
                    # Punto 2, 3 y 4: Formato condicional y concordancia
                    txt_totales = format_totales(tipo, cant_propios, cant_contratados)
                    reporte_diario += f"*{total_operativos} {tipo_plural}*{txt_totales}\n"
                    
                    # AREAS
                    areas_p = df_p_op['ÁREA'].value_counts().to_dict() if not df_p_op.empty and 'ÁREA' in df_p_op.columns else {}
                    areas_c = df_c_tipo.groupby('AREA_C')['CANTIDAD_C'].sum().to_dict() if not df_c_tipo.empty and 'AREA_C' in df_c_tipo.columns else {}
                    
                    todas_areas = set(areas_p.keys()).union(set(areas_c.keys()))
                    todas_areas = sorted([a for a in todas_areas if str(a).strip() != ""])
                    
                    for a in todas_areas:
                        tot_a = areas_p.get(a, 0) + areas_c.get(a, 0)
                        if tot_a > 0:
                            reporte_diario += f"• {tot_a} en {a}\n" # Cambiado a viñeta redonda como en el ejemplo
                    
                    # Punto 1: Unidades inactivas bajo cada tipo
                    df_p_inact = df_diario[
                        (df_diario['TIPO'] == tipo) & 
                        (df_diario['ESTADO'].isin(['INACTIVO', 'INACTIVA', 'IRRECUPERABLE']))
                    ]
                    
                    if not df_p_inact.empty:
                        reporte_diario += "\n"
                        if resumen_ia:
                            # Preparar contexto para IA
                            lista_inact = ""
                            for _, r in df_p_inact.iterrows():
                                ex_val = str(r.get('EX', '')).strip()
                                nombre_ex = f" (ex {ex_val})" if ex_val != "" and ex_val.lower() != "nan" else ""
                                lista_inact += f"- {r['UNIDAD']}{nombre_ex} ({r.get('ÁREA', '')}): {r.get('DIAGNÓSTICO', '')}\n"
                            
                            sys_ins = "Eres un supervisor de taller. Resume diagnósticos de forma extremadamente concisa (máximo 10 palabras por unidad). Mantén ID y Área. Usa el emoji 🔺."
                            prompt = f"Resume estas unidades inactivas para un reporte de WhatsApp:\n\n{lista_inact}"
                            resumen = ask_gemini(prompt, system_instruction=sys_ins)
                            reporte_diario += resumen + "\n"
                        else:
                            for _, row in df_p_inact.iterrows():
                                est = str(row['ESTADO']).upper()
                                emoji_nov = "❌" if est == "IRRECUPERABLE" else "🔺"
                                ex_val = str(row.get('EX', '')).strip()
                                nombre_ex = f" (ex {ex_val})" if ex_val != "" and ex_val.lower() != "nan" else ""
                                diag = row.get('DIAGNÓSTICO', '')
                                area_str = str(row.get('ÁREA', ''))
                                reporte_diario += f"- *{row['UNIDAD']}*{nombre_ex} ({area_str}) {emoji_nov} {diag}\n"
                    
                    reporte_diario += "\n"

                # NOVEDADES
                df_novedades = pd.DataFrame()
                if not df_diario.empty and 'TIPO' in df_diario.columns:
                    df_novedades = df_diario[
                        (df_diario['TIPO'].isin(tipo_sel_diario)) & 
                        (df_diario['ESTADO'].isin(['INACTIVO', 'INACTIVA', 'IRRECUPERABLE']))
                    ]
                
                if not df_novedades.empty:
                    reporte_diario += "DETALLE DE INACTIVOS:\n"
                    for _, row in df_novedades.iterrows():
                        est = str(row['ESTADO']).upper()
                        emoji_nov = "❌" if est == "IRRECUPERABLE" else "🔺"
                        ex_val = str(row.get('EX', '')).strip()
                        nombre_ex = f" (ex {ex_val})" if ex_val != "" and ex_val.lower() != "nan" else ""
                        diag = row.get('DIAGNÓSTICO', '')
                        area_str = str(row.get('ÁREA', ''))
                        reporte_diario += f"- *{row['UNIDAD']}*{nombre_ex} ({area_str}) {emoji_nov} {diag}\n"

                # Renderizado
                st.markdown("### 📋 Parte Diario Generado")
                st.text_area(label="Contenido final Parte Diario", value=reporte_diario, height=500, key="ta_diario", label_visibility="collapsed")
                
                copy_js_diario = f"""
                <button onclick="copyToClipboardDiario()" style="
                    width: 100%; background-color: {CONF['COLOR_VERDE']}; color: white; border: none; 
                    padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; text-transform: uppercase; letter-spacing: 1px;">
                    Copiar Parte Diario al Portapapeles 📋
                </button>
                <script>
                function copyToClipboardDiario() {{
                    const text = `{reporte_diario.replace('`', '\\`')}`;
                    const el = document.createElement('textarea');
                    el.value = text;
                    document.body.appendChild(el);
                    el.select();
                    document.execCommand('copy');
                    document.body.removeChild(el);
                    alert('Parte Diario copiado.');
                }}
                </script>
                """
                components.html(copy_js_diario, height=70)

    with tab3:
        render_page_title("IDA Y VUELTA")
        
        # Filtrar unidades inactivas (excluyendo delegaciones para consistencia)
        df_inactivas = df[
            (df['ESTADO'].isin(['INACTIVO', 'INACTIVA'])) & 
            (~df['ÁREA'].str.contains("DELEGACI", na=False))
        ].copy() if not df.empty else pd.DataFrame()

        col_chat, col_tracking = st.columns([1.5, 1])

        # --- COLUMNA IZQUIERDA: CHATBOT ---
        with col_chat:
            st.markdown("### 💬 Chat de Flota")
            
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Mostrar historial
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Pregunta sobre la flota..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    # Uso de contexto optimizado y system_instruction predefinida
                    ctx = clean_fleet_context(df)
                    sys_ins = "Eres un asistente de flota. Responde con tablas Markdown si es posible. No uses prosa innecesaria."
                    response = ask_gemini(f"Contexto:\n{ctx}\n\nPregunta: {prompt}", system_instruction=sys_ins)
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            if st.button("📊 Generar Resumen Ejecutivo"):
                with st.spinner("Analizando flota..."):
                    resumen = get_resumen_ejecutivo(df)
                    st.markdown(resumen)

        # --- COLUMNA DERECHA: SEGUIMIENTO ACTIVO (PROPUESTAS) ---
        with col_tracking:
            st.markdown("### 📋 Propuestas")
            
            if df_inactivas.empty:
                st.info("No hay unidades inactivas fuera de delegaciones.")
            else:
                if st.button("Solicitar ✨", key="btn_gen_prop"):
                    with st.spinner("Gemini analizando la flota inactiva..."):
                        propuestas = get_fleet_proposals(df_inactivas)
                        st.markdown(propuestas)
                
                st.divider()
                st.caption("Usa la pestaña 'Seguimiento' para actualizar diagnósticos rápidamente.")

    with tab4:
        render_page_title("SEGUIMIENTO")
        df_seg_base = df[~df['ÁREA'].str.contains("DELEGACI", na=False)].copy()

        # ----- FILTROS (fila de st.columns independiente) -----
        st.markdown("<div style='margin-bottom:6px;'>", unsafe_allow_html=True)
        f_cols = st.columns([1, 2, 2, 1, 2, 1])
        with f_cols[0]: f_id    = st.text_input("🔍 Unidad",    placeholder="Buscar unidad",  key="fi_id").upper()
        with f_cols[1]: f_tipo  = st.text_input("🔍 Tipo",      placeholder="Buscar tipo",    key="fi_tipo").upper()
        with f_cols[2]: f_marca = st.text_input("🔍 Marca/Mod", placeholder="Marca o Modelo", key="fi_marca").upper()
        with f_cols[3]: f_pat   = st.text_input("🔍 Patente",   placeholder="Dominio",        key="fi_pat").upper()
        with f_cols[4]: f_area  = st.text_input("🔍 Área",      placeholder="Buscar área",    key="fi_area").upper()
        with f_cols[5]: f_est   = st.text_input("🔍 Estado",    placeholder="ACTIVO…",        key="fi_est").upper()
        st.markdown("</div>", unsafe_allow_html=True)

        # ----- FILTRADO -----
        df_seg = df_seg_base.copy()
        if f_id:    df_seg = df_seg[df_seg['UNIDAD'].str.contains(f_id, na=False)]
        if f_tipo:  df_seg = df_seg[df_seg['TIPO'].str.contains(f_tipo, na=False)]
        if f_marca:
            mask = df_seg.get('MARCA', pd.Series(dtype=str)).fillna('').str.upper().str.contains(f_marca, na=False) \
                 | df_seg.get('MODELO', pd.Series(dtype=str)).fillna('').str.upper().str.contains(f_marca, na=False)
            df_seg = df_seg[mask]
        if f_pat:   df_seg = df_seg[df_seg.get('DOMINIO', pd.Series(dtype=str)).fillna('').str.upper().str.contains(f_pat, na=False)]
        if f_area:  df_seg = df_seg[df_seg['ÁREA'].str.contains(f_area, na=False)]
        if f_est:   df_seg = df_seg[df_seg['ESTADO'].str.contains(f_est, na=False)]

        # ----- TABLA HTML COMPLETA -----
        if df_seg.empty:
            st.info("No se encontraron unidades con los filtros aplicados.")
        else:
            # Construir tabla HTML
            rows_html = ""
            filas_lista = []  # para iterar luego con st.columns
            for i, (_, row) in enumerate(df_seg.iterrows()):
                u        = str(row['UNIDAD'])
                tipo     = str(row.get('TIPO', ''))
                marca    = str(row.get('MARCA', ''))
                modelo   = str(row.get('MODELO', ''))
                dominio  = str(row.get('DOMINIO', ''))
                area     = str(row.get('ÁREA', ''))
                est      = str(row['ESTADO']).upper()
                diag_val = str(row.get('DIAGNÓSTICO', ''))

                badge_cls = "badge-activo" if est in ['ACTIVO', 'ACTIVA'] else "badge-inactivo"

                rows_html += f"""
                <tr>
                    <td class="td-unidad">{u}</td>
                    <td class="td-secondary">{tipo}</td>
                    <td class="td-secondary">{marca} {modelo}</td>
                    <td class="td-secondary">{dominio}</td>
                    <td class="td-secondary">{area}</td>
                    <td><span class="{badge_cls}">{est}</span></td>
                    <td class="td-secondary" style="font-style:italic;color:#8aaa9e;">{diag_val if diag_val else '—'}</td>
                </tr>"""
                filas_lista.append((u, diag_val))

            tabla_html = f"""
            <div style="overflow-x:auto; border-radius:8px; box-shadow:0 2px 8px rgba(0,143,122,0.08);">
              <table class="fleet-table">
                <thead>
                  <tr>
                    <th>Unidad</th>
                    <th>Tipo</th>
                    <th>Marca / Modelo</th>
                    <th>Patente</th>
                    <th>Área</th>
                    <th>Estado</th>
                    <th>Diagnóstico Actual</th>
                  </tr>
                </thead>
                <tbody>
                  {rows_html}
                </tbody>
              </table>
            </div>
            """
            st.markdown(tabla_html, unsafe_allow_html=True)

            # ----- CONTROLES INTERACTIVOS DEBAJO DE LA TABLA -----
            st.markdown(
                "<div style='margin-top:14px; padding:10px 0 4px 0; "
                "border-top:2px solid #E8EEEC;'>"
                "<span style='font-size:11px;font-weight:700;color:#9aaba6;"
                "text-transform:uppercase;letter-spacing:0.8px;'>✏️ Editar diagnóstico</span>"
                "</div>",
                unsafe_allow_html=True
            )

            for u, diag_actual in filas_lista:
                ctrl_cols = st.columns([1, 5, 1])
                ctrl_cols[0].markdown(
                    f"<div style='padding-top:6px;font-weight:800;font-size:12px;"
                    f"color:{CONF['COLOR_PRINCIPAL']};'>{u}</div>",
                    unsafe_allow_html=True
                )
                new_diag = ctrl_cols[1].text_input(
                    "diag",
                    value=diag_actual,
                    key=f"diag_{u}",
                    label_visibility="collapsed",
                    placeholder="Ingrese diagnóstico…"
                )
                with ctrl_cols[2]:
                    st.markdown('<div class="btn-actualizar">', unsafe_allow_html=True)
                    if st.button("ACTUALIZAR", key=f"btn_{u}", use_container_width=True):
                        if new_diag != diag_actual:
                            with st.spinner("Guardando…"):
                                if update_diagnostico_sheet(u, new_diag):
                                    st.success(f"✔ {u} actualizado")
                                    st.cache_data.clear()
                                    st.rerun()
                        else:
                            st.info("Sin cambios.")
                    st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
