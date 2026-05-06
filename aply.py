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
    if 'EX' in data.columns:
        data['EX'] = data['EX'].fillna('').astype(str).str.replace('.0', '', regex=False)
    for col in ['TIPO', 'ESTADO', 'ÁREA']:
        if col in data.columns:
            data[col] = data[col].fillna('').str.strip().str.upper()
    return data.fillna("")

def obtener_terminacion(tipo):
    return "A" if tipo.upper() in UNIDADES_FEMENINAS else "O"

# --- INTERFAZ ---
st.title("🚜 Generador de Reportes de Flota")

try:
    df = load_data()
    
    # --- SELECTORES DE FILTRADO ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipos_disponibles = sorted(df['TIPO'].unique())
        tipo_sel = st.multiselect("Tipo de Unidad:", tipos_disponibles, default=[tipos_disponibles[0]] if len(tipos_disponibles) > 0 else [])
    
    with col2:
        filtro_area = st.selectbox("Filtrar por Área:", 
                                   ["TODAS", "SERVICIOS PÚBLICOS", "AMBIENTE", "SECRETARÍA", "ARQUITECTURA"])
    
    with col3:
        filtro_estado = st.selectbox("Filtrar por Estado:", ["TODOS", "ACTIVOS", "INACTIVOS"])

    if st.button('Generar Informe para WhatsApp 📋'):
        if not tipo_sel:
            st.warning("Debe seleccionar al menos un Tipo de Unidad.")
            st.stop()
            
        # 1. Filtrado Base (Tipo)
        df_f = df[df['TIPO'].isin(tipo_sel)].copy()
        
        # 2. Filtrado por Área
        if filtro_area == "SERVICIOS PÚBLICOS":
            df_f = df_f[df_f['ÁREA'].isin(AREAS_SSPP)]
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
                ex_val = str(row['EX']).strip()
                nombre_ex = f" (ex {ex_val})" if ex_val != "" and ex_val.lower() != "nan" else ""
                diag = row.get('DIAGNÓSTICO', '')
                return f"\n- *{row['UNIDAD']}*{nombre_ex} ({row['MARCA']} {row['MODELO']}) {emoji} {txt_estado}: {diag}\n"
            
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
                const text = `{reporte}`;
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

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
