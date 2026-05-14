# Hermes Analytics Dashboard — UI Overhaul

## Resumen
Dashboard Streamlit para monitoreo de costos, tokens, herramientas y rendimiento de Hermes Agent.

## Estructura
- streamlit_app.py — Dashboard completo (78 KB, 1715 líneas)
- dashboard_schema.sql — Esquema SQLite de dashboard.db
- BLUEPRINT.md — Arquitectura y diseño visual
- assets/ — Logo Caduceo + capturas de referencia

## Lo que necesita arreglo (por orden de prioridad)

### 1. Navegación lateral
- Reemplazar `st.tabs()` horizontal por sidebar con radio buttons (st.radio)
- Cada opción debe tener tooltip al hacer hover explicando la sección
- El contenido actual de cada tab debe mostrarse según la opción seleccionada

### 2. Logo en sidebar
- Mover el canvas Caduceo animado a la sidebar (más pequeño, ~120px)
- El área principal debe usar el ancho completo

### 3. KPIs centrados
- Los valores numéricos en .custom-card deben tener text-align: center
- Consistencia en todos los KPIs de las 5 secciones

### 4. Etiquetas de datos en gráficos
- Algunos charts tienen etiquetas que no se ven bien (tamaño, posición, cortadas)
- Reescalar tamaño de fuente y posición de data labels

### 5. Consistencia de fuentes
- Tamaños de fuente uniformes en títulos de secciones
- Todos los títulos de sección deben usar .section-header

### 6. Bug conocido
- Columna `success` en tool_usage es INTEGER (0/1), no BOOLEAN
- `(~x).sum()` devuelve negativos — usar `(x == 0).sum()` en su lugar
- YA CORREGIDO en L1435 y L1549, verificar que no haya más ocurrencias

## Diseño visual
- Fondo: #000000 (negro puro)
- Tarjetas: #1A1A1A, border-radius 16px
- Títulos/acentos: #F59E0B (ámbar)
- Borders: #2A2A2A
- Chart palette: #3B82F6, #EC4899, #22C55E, #EAB308, #F97316
