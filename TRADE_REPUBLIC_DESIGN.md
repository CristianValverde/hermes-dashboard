# Hermes Dashboard - Rediseño Trade Republic

## Cambios Realizados (2026-05-11)

### Sistema de Diseño Aplicado
- **Tema Oscuro**: Fondo negro puro (#000000) como Trade Republic
- **Cards Elevadas**: Fondo gris oscuro (#1A1A1A) con bordes redondeados (16px)
- **Tipografía**: Jerarquía clara con pesos diferenciados (Sans-serif)
- **Espaciado**: Generoso entre elementos, alineación izquierda
- **Colores Alternativos**: Siguiendo tu petición de evitar blanco/azul/verde en gráficos

### Paleta de Colores
- **Fondo**: #000000 (negro)
- **Texto Principal**: #FFFFFF (blanco)
- **Texto Secundario**: #AAAAAA (gris)
- **Cards/Superficies**: #1A1A1A (gris oscuro)
- **Bordes**: #2A2A2A
- **Acento Positivo**: #4ADE80 (verde suave)
- **Acento Negativo**: #F87171 (rojo suave)
- **Gráficos (líneas)**: #A855F7 (violeta)
- **Gráficos (barras)**: #8B5CF6 (violeta claro)

### Componentes Implementados
1. **Cards estilo Trade Republic**: Con efecto hover y bordes redondeados
2. **Header jerárquico**: Título + subtítulo con estilo uppercase
3. **Sidebar mejorado**: Con cards para créditos y estado del colector
4. **Gráficos personalizados**: Tema oscuro Plotly con colores violeta
5. **Dataframes con estilo**: Fondo oscuro, bordes sutiles
6. **Advertencia visual**: Banner de advertencia sobre precisión de costes

### Archivos Modificados/Creados
- `streamlit_app.py` → **REDISEÑADO COMPLETO** (backup: `streamlit_app_original_112915.py`)
- `.streamlit/config.toml` → Configuración de tema oscuro
- `launch_dashboard_tr.bat` → Script de lanzamiento Windows
- `launch_dashboard_tr.ps1` → Script de lanzamiento PowerShell

### Cómo Usar
1. **Lanzar dashboard**: `launch_dashboard_tr.bat` (o `.ps1`)
2. **URL**: http://localhost:8501
3. **Colector de datos**: Ya está programado (cron job `a4dcdae4dd65`, cada hora, modo silencioso)

### Diferencia Visual vs Anterior
| Característica | Anterior | Nuevo (Trade Republic) |
|----------------|----------|------------------------|
| Fondo | Blanco/gris | Negro (#000000) |
| Cards | Rectangulares simples | Elevadas, bordes redondeados |
| Gráficos | Azul/verde/blanco | Violeta (#A855F7) |
| Jerarquía | Básica | Claramente definida |
| Estado | Estático | Cards con hover |

### Consideraciones Técnicas
- El CSS personalizado se inyecta via `st.markdown()`
- Los gráficos Plotly usan `plot_bgcolor='#000000'` y `paper_bgcolor='#000000'`
- Los dataframes tienen CSS personalizado para tema oscuro
- Toda la configuración del tema está centralizada en `.streamlit/config.toml`

---

*Diseño inspirado en la interfaz de Trade Republic (capturas proporcionadas)*
