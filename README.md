# Flota Varela - Sistema de Gestión de Reportes

Este proyecto es una aplicación web interactiva desarrollada con **Streamlit**, diseñada para la gestión centralizada y la generación de reportes de estado de la flota vehicular y maquinaria pesada municipal.

La aplicación se sincroniza en tiempo real con una base de datos en **Google Sheets**, permitiendo a los operadores generar informes detallados y formateados listos para ser compartidos vía WhatsApp de manera instantánea.

---

## 🚀 Características Principales

*   **Sincronización con Google Sheets:** Conexión segura mediante API (gspread) para lectura y escritura de datos.
*   **Filtros Inteligentes:** 
    *   **Multiselección de Unidades:** Permite agrupar diferentes tipos de vehículos (Camionetas, Excavadoras, etc.) en un solo reporte.
    *   **Filtrado por Área:** Segmentación por Servicios Públicos, Ambiente, Secretaría, Arquitectura, etc.
    *   **Estado Operativo:** Filtrado rápido de unidades Activas o Inactivas.
*   **Concordancia Gramatical AI-Ready:** El sistema detecta automáticamente el género de la unidad para ajustar el texto del reporte (ej: "Operativ**o**" vs "Operativ**a**").
*   **Historial de Reportes:** Cada informe generado se guarda automáticamente en una pestaña de "Historial" en la hoja de cálculo, incluyendo fecha, filtros aplicados y el contenido del reporte.
*   **Copiado One-Click:** Interfaz optimizada con botones interactivos para copiar el reporte final al portapapeles.

---

## 🛠️ Requisitos e Instalación

### 1. Requisitos Previos
*   Python 3.9 o superior.
*   Una cuenta de Google Cloud con la API de Google Sheets y Drive activada.
*   Un archivo de credenciales de Service Account.

### 2. Instalación Local
Clona el repositorio y ejecuta:

```bash
pip install -r requirements.txt
```

### 3. Configuración de Secretos (`.streamlit/secrets.toml`)
Para que la aplicación funcione, debes crear un archivo `.streamlit/secrets.toml` con la siguiente estructura:

```toml
spreadsheet_id = "TU_ID_DE_HOJA_DE_CALCULO"

[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto"
private_key_id = "tu-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
client_email = "tu-email@serviceaccount.com"
client_id = "..."
# ... resto de campos del JSON de Google ...
```

---

## 📖 Instrucciones de Uso

1.  **Lanzar la App:**
    ```bash
    streamlit run aply.py
    ```
2.  **Configurar Filtros:**
    *   Selecciona los **Tipos de Unidad**.
    *   Define el **Área** y el **Estado** (Activos/Inactivos).
3.  **Generar y Enviar:**
    *   Haz clic en **"Generar Informe para WhatsApp 📋"**.
    *   Verifica el log de éxito (se guardará en el Historial).
    *   Presiona **"Copiar al Portapapeles 📋"** y pega el texto en WhatsApp.

---

## 📁 Estructura del Proyecto

*   `aply.py`: **Script principal** con integración de GSheets y logging.
*   `aply22.py`: Versión de respaldo (Legacy) basada en CSV público.
*   `requirements.txt`: Dependencias del sistema (streamlit, pandas, gspread, etc.).
*   `.streamlit/`: Configuración y secretos locales.

---

> [!NOTE]
> Desarrollado para optimizar la comunicación operativa de la flota municipal de Florencio Varela.

