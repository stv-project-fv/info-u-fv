import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
from google import genai
try:
    import tabulate
except ImportError:
    tabulate = None

st.set_page_config(
    page_title="Flota Varela",
    page_icon="🚜",
    layout="centered", # 'centered' suele verse mejor en celulares que 'wide'
    initial_sidebar_state="collapsed",
)
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
    if tabulate:
        return df_mini.to_markdown(index=False)
    else:
        return df_mini.to_string(index=False)

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
st.title("🚜 Generador de Reportes de Flota")

try:
    df = load_data()
    df_contratados = load_data_contratados()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Reporte Individual", "Parte Diario", "Ida y Vuelta", "Seguimiento"])
    
    with tab1:
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
                    # --- CÁLCULOS ---
                    total_u = len(df_f)
                    activos_u = len(df_f[df_f['ESTADO'].isin(['ACTIVO', 'ACTIVA'])])
                    fecha_hoy = datetime.now().strftime("%d/%m/%y")
                    # --- CONSTRUCCIÓN DEL TEXTO ---
                    tipos_str = ", ".join(tipo_sel)
                    reporte = f"Fecha: {fecha_hoy}\n\n"
                    reporte += f"Tipos seleccionados: *{tipos_str} ({activos_u} de {total_u} activos en total)*\n"
                    
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
                    
                    # Optimización con apply en vez de iterrows
                    df_f['REPORTE_TXT'] = df_f.apply(formato_fila, axis=1)
                    
                    # Agrupar por áreas que sobrevivieron al filtro
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
                    st.markdown("### Informe Generado:")
                    st.text_area(label="Contenido final", value=reporte, height=450)
                    
                    # Botón de Copiado con JS
                    copy_js = f"""
                    <button onclick="copyToClipboard()" style="
                        width: 100%; background-color: #28a745; color: white; border: none; 
                        padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer;">
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
                st.markdown("### Parte Diario Generado:")
                st.text_area(label="Contenido final Parte Diario", value=reporte_diario, height=500, key="ta_diario")
                
                copy_js_diario = f"""
                <button onclick="copyToClipboardDiario()" style="
                    width: 100%; background-color: #28a745; color: white; border: none; 
                    padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer;">
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
        st.markdown("## 🔄 Ida y Vuelta: Centro de Control Inteligente")
        
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
        st.markdown("## 📝 Seguimiento Manual de Diagnósticos")
        
        # Filtro de búsqueda opcional para no saturar la vista
        search_seg = st.text_input("🔍 Buscar unidad por ID o diagnóstico:", "").upper()
        
        df_seg = df[~df['ÁREA'].str.contains("DELEGACI", na=False)].copy()
        if search_seg:
            df_seg = df_seg[
                df_seg['UNIDAD'].str.contains(search_seg, na=False) | 
                df_seg['DIAGNÓSTICO'].str.contains(search_seg, na=False)
            ]

        if df_seg.empty:
            st.info("No se encontraron unidades.")
        else:
            # Encabezados
            h1, h2, h3 = st.columns([1.5, 2, 1])
            h1.markdown("**Unidad (Actual)**")
            h2.markdown("**Actualizado**")
            h3.markdown("**Acción**")
            
            for _, row in df_seg.iterrows():
                u = row['UNIDAD']
                diag_actual = row.get('DIAGNÓSTICO', '')
                
                with st.container():
                    c1, c2, c3 = st.columns([1.5, 2, 1])
                    with c1:
                        st.markdown(f"**{u}**")
                        st.caption(diag_actual if diag_actual else "Sin diagnóstico")
                    with c2:
                        new_diag = st.text_input(f"Nuevo para {u}", key=f"inp_{u}", label_visibility="collapsed", placeholder="Escribe el avance...")
                    with c3:
                        if st.button("CONFIRMAR", key=f"btn_upd_{u}", use_container_width=True):
                            if new_diag.strip():
                                with st.spinner("..."):
                                    if update_diagnostico_sheet(u, new_diag):
                                        st.success("✔")
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("Error")
                            else:
                                st.warning("!")
                    st.divider()

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
