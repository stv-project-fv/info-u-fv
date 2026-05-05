# 🚜 Generador de Reportes de Flota - Varela Pro

Este proyecto es una aplicación web interactiva desarrollada con **Streamlit** diseñada para la gestión y generación de reportes de estado de flota vehicular y maquinaria pesada. La aplicación consume datos en tiempo real desde una hoja de cálculo de Google Sheets y permite generar informes formateados listos para ser compartidos vía WhatsApp.

## 🚀 Características Principales

- **Sincronización en Tiempo Real:** Carga datos directamente desde un CSV público de Google Sheets.
- **Filtros Avanzados:** 
  - Filtrado por tipo de unidad (Aplanadoras, Camionetas, Excavadoras, etc.).
  - Filtrado por área (Servicios Públicos, Ambiente, Secretaría, Arquitectura).
  - Filtrado por estado operativo (Activos, Inactivos).
- **Concordancia Gramatical Automática:** El sistema detecta si la unidad es femenina o masculina para ajustar el texto del reporte (ej: "Operativo" vs "Operativa").
- **Generación de Reportes para WhatsApp:** Crea un resumen detallado con emojis, separando las unidades por área y detallando su diagnóstico.
- **Copiado Rápido:** Incluye un botón interactivo para copiar el reporte final al portapapeles con un solo clic.

## 🛠️ Requisitos e Instalación

### Requisitos Previos
Asegúrate de tener instalado Python 3.8 o superior.

### Instalación Local
Instala las bibliotecas necesarias utilizando el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

Las dependencias principales son:
- `streamlit`
- `pandas`

### Uso con Dev Containers (VS Code)
Este proyecto incluye una configuración de `.devcontainer`. Si utilizas VS Code con la extensión "Dev Containers" o GitHub Codespaces:
1. Abre la carpeta en el contenedor.
2. Las dependencias se instalarán automáticamente.
3. La aplicación se ejecutará automáticamente y estará disponible en el puerto 8501.

## 📖 Instrucciones de Uso

1. **Ejecutar la aplicación:**
   Abre una terminal en la carpeta del proyecto y ejecuta:
   ```bash
   streamlit run aply2.py
   ```

2. **Configurar Filtros:**
   - Selecciona el **Tipo de Unidad** que deseas reportar.
   - Selecciona el **Área** específica o deja en "TODAS".
   - Elige si quieres ver solo los **Activos**, **Inactivos** o el listado completo.

3. **Generar Informe:**
   - Haz clic en el botón **"Generar Informe para WhatsApp 📋"**.
   - Revisa el texto generado en el área de previsualización.

4. **Copiar y Compartir:**
   - Presiona el botón verde **"Copiar al Portapapeles 📋"**.
   - Pega el contenido directamente en un chat de WhatsApp o cualquier otro medio de comunicación.

## 📁 Estructura del Proyecto

- `aply2.py`: Script principal de la aplicación.
- `requirements.txt`: Lista de dependencias del proyecto.
- `aply.py`: Versión alternativa/respaldo del script principal.

---
*Desarrollado para la gestión eficiente de la flota municipal.*
