# Hermes Analytics Dashboard — Blueprint

> **Última actualización:** 2026-05-11  
> **Estado:** Producción (78 sesiones, 6 modelos, 65M tokens, 2,875 tool calls)

## Diseño Visual

| Elemento | Valor |
|----------|-------|
| Fondo | `#0D0D0D` (OpenRouter dark) |
| Cards | `#1A1A1A`, border-radius 16px, hover elevation |
| Texto | `#FFFFFF` (primario), `#AAAAAA` (secundario) |
| Títulos/Headers/Tabs | `#F59E0B` (ámbar — Hermes brand) |
| Chart 1 (base) | `#3B82F6` (Blue) |
| Chart 2 | `#EC4899` (Pink) |
| Chart 3 | `#22C55E` (Green) |
| Chart 4 | `#EAB308` (Gold) |
| Chart 5 | `#F97316` (Orange) |
| Positivo | `#4ADE80` |
| Negativo | `#F87171` |
| Logo animado | Caduceus Hermes con glow cíclico + gradient sweep |

## Tabs

### 1️⃣ Overview — KPIs, stacked bar tokens, eficiencia, tabla sesiones, sidebar créditos OR
### 2️⃣ Tools Analytics — tool calls, stacked bar por día, pie chart distribución
### 3️⃣ Token Analytics — Total Tokens, OpenRouter gastado, Coste Real (est.), stacked bar, pie chart desglose, mgmt key notice
### 4️⃣ Errors & Performance — filtros source/type/tool/resolved, clustering msg_clean, priorización frecuencia×unresolved, tendencias, performance, hora del día
### 5️⃣ System Performance — matriz error rate modelo×herramienta, heatmap, tendencia diaria

## Colector

Incremental vía high_water_mark. Pipeline: watermark → migrate_db → sessions → compute_real_costs → tool_performance → credits → model_prices → openrouter_activity → log_run_end. Cron hourly (deliver=local).

## Skills relacionadas

- `model-pricing-reference` — precios por token de cada modelo
- `session-iteration-limit` — cambiar max_turns entre 60/100/150

## Pendiente

- [ ] Management Key → token comparison Hermes vs OpenRouter
- [ ] Alertas de gasto excesivo
