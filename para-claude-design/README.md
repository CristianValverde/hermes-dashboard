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

## 🗺️ Mapa del Código (streamlit_app.py)

Busca por `🎯` en el código para saltar directo a cada sección.

| Línea | Sección | Búsqueda |
|-------|---------|----------|
| ~60-400 | CSS global (cards, tabs, colores) | `.custom-card` |
| ~407-528 | Funciones load_* (datos) | `def load_` |
| ~530-790 | Funciones create_*_chart (gráficos) | `def create_` |
| ~794-900 | `render_overview_tab` | `render_overview_tab` |
| ~900-953 | `render_tools_tab` | `render_tools_tab` |
| ~954-1148 | `render_tokens_tab` | `render_tokens_tab` |
| ~1149-1381 | `render_errors_tab` | `render_errors_tab` |
| ~1400-1593 | `render_system_performance_tab` | `render_system_performance_tab` |
| **~1604** | **🎯 LOGO CADUCEO CANVAS** | **Buscar: `🎯`** |
| **~1626** | **🎯 TABS HORIZONTALES** | **Buscar: `🎯`** |
| ~1633-1665 | Sidebar (DB status, quick links) | `with st.sidebar` |
| ~1667-1695 | Renderizado de tabs + footer | `with tab1:` |

### Canvas Animation (L1604-1622)
- **Logo pixel-art Caduceo**: array `PX` (54x54 grid)
- **Escalar**: cambiar `CW, CH, DR` (actual: 3, 3, 1.3)
- **Contenedor**: `components.html(height=280)`
- **No modificar** el array `PX` — escalar via CW/CH

### Tabs (L1626)
- 5 tabs: Overview, Tools Analytics, Token Analytics, Errors & Performance, System Performance
- **Objetivo**: reemplazar `st.tabs()` por sidebar radio navigation
- Cada tab renderiza su función: `render_overview_tab()`, etc.

### Bug `~x` (ya corregido)
- Lineas donde se usa: L1435, L1549
- `(~x).sum()` → `(x == 0).sum()` porque `success` es INTEGER (0/1)
