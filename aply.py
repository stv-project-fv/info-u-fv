import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials

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

# --- INTERFAZ ---
st.title("🚜 Generador de Reportes de Flota")

try:
    df = load_data()
    df_contratados = load_data_contratados()
    
    tab1, tab2 = st.tabs(["Reporte Individual", "Parte Diario"])
    
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

        tipo_sel_diario = st.multiselect("Seleccionar Tipos de Unidad:", tipos_unificados, default=[], key="ms_diario")

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
                    
                    reporte_diario += f"*{total_operativos} {tipo_plural}* - ({cant_propios} Propios + {cant_contratados} Contratados)\n"
                    
                    # AREAS
                    areas_p = df_p_op['ÁREA'].value_counts().to_dict() if not df_p_op.empty and 'ÁREA' in df_p_op.columns else {}
                    areas_c = df_c_tipo.groupby('AREA_C')['CANTIDAD_C'].sum().to_dict() if not df_c_tipo.empty and 'AREA_C' in df_c_tipo.columns else {}
                    
                    todas_areas = set(areas_p.keys()).union(set(areas_c.keys()))
                    todas_areas = sorted([a for a in todas_areas if str(a).strip() != ""])
                    
                    for a in todas_areas:
                        tot_a = areas_p.get(a, 0) + areas_c.get(a, 0)
                        if tot_a > 0:
                            reporte_diario += f"* {tot_a} en {a}\n"
                    
                    reporte_diario += "\n"

                # NOVEDADES
                df_novedades = pd.DataFrame()
                if not df_diario.empty and 'TIPO' in df_diario.columns:
                    df_novedades = df_diario[
                        (df_diario['TIPO'].isin(tipo_sel_diario)) & 
                        (df_diario['ESTADO'].isin(['INACTIVO', 'INACTIVA', 'IRRECUPERABLE']))
                    ]
                
                if not df_novedades.empty:
                    reporte_diario += "*NOVEDADES:*\n"
                    for _, row in df_novedades.iterrows():
                        est = str(row['ESTADO']).upper()
                        emoji_nov = "❌" if est == "IRRECUPERABLE" else "🔺"
                        ex_val = str(row.get('EX', '')).strip()
                        nombre_ex = f" (ex {ex_val})" if ex_val != "" and ex_val.lower() != "nan" else ""
                        diag = row.get('DIAGNÓSTICO', '')
                        area_str = str(row.get('ÁREA', ''))
                        reporte_diario += f"- *{row['UNIDAD']}*{nombre_ex} ({area_str}) {emoji_nov} {est}: {diag}\n"

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

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
