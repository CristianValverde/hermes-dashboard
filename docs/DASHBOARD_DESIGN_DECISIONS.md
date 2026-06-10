# Hermes Dashboard Design Decisions

Updated: 2026-06-03

## Scope

This document captures cross-session UI decisions for the Hermes dashboard. Treat these as project-level defaults unless a later explicit decision supersedes them.

## Information Model

- Work tab by tab. Do not generalize a tab before its mental map has been validated.
- `Overview` is the first validated tab and should act as a single-scan cockpit.
- Above charts, avoid repeating the same metric in multiple layers.
- Cards should use one large central metric and related secondary KPIs in the footer.
- Dense details belong in tooltips when they support inspection but are not part of first-scan reading.

## Tooltip Offloading

Apply this pattern first to `Overview`; extend to other tabs only after their information model is validated.

- Donut legends should show color plus label only.
- Donut totals and percentages should live in hover/focus tooltips.
- Daily stacked bars should expose daily total and per-category breakdown in tooltips.
- Category legends should keep labels visible and move accumulated totals to per-category tooltips.
- Tooltip anchors should support keyboard focus/tap where practical, not hover only.

## Categorical Palette

Primary categorical order for charts should use the saturated OpenRouter-style dashboard palette already used by model/tool bar charts:

1. Teal: `#00D4B4`
2. Violet: `#A855F7`
3. Red: `#E84848`
4. Amber: `#FBBF24`
5. Green: `#39D966`

Reserved colors for charts with more categories:

6. Pink: `#EC4899`
7. Purple: `#8B5CF6`
8. Coral: `#FF6B6B`
9. Cyan: `#06B6D4`
10. Emerald: `#34D399`
11. Lavender: `#A78BFA`
12. Electric cyan: `#22D3EE`

Palette rationale:

- Do not use the previous pastel palette in dashboard charts; it does not fit the dark HUD theme.
- Do not pair mint/teal-like colors with ice-blue/cyan-like colors in adjacent donut segments when the contrast is weak.
- For circular charts, test adjacency as a loop, including last-to-first.
- Prefer perceptual separation over semantic color habits when categories are nominal.
- Prefer saturated model/tool palette colors over muted or washed-out variants.

## Economic Class Colors

Use explicit semantic mapping for economic classes instead of generic palette index order:

- `Usage-billable`: teal `#00D4B4`
- `OSS`: green `#39D966`
- `Subscription-based`: violet `#A855F7`
- `Unknown`: red `#E84848`

Reasoning:

- The dashboard's dark HUD theme reads better with the saturated OpenRouter-style chart palette.
- Pastel mint/ice-blue combinations have poor contrast in donuts and should not be reused.
- Economic colors should remain explicit, but the mapping should use saturated chart colors.

## Credential Guidance

- Do not render Management Key setup prompts or credential instructions inside dashboard pages.
- Keep `OPENROUTER_MANAGEMENT_KEY` setup instructions in `README.md`; the dashboard should only display collected telemetry.

## Terminology

- Use `Tool calls`, not `Tools`, when the metric is the number of invocations.
- Use `Models`, not `Surface`, for model-related cards.
- Use `Contexto (KV-cache)` / `Context`, not plain `Cache`, when describing token usage taxonomy.
- Economic taxonomy should be user-facing as:
  - `Usage-billable`
  - `OSS`
  - `Subscription-based`

## Verification Expectations

For color/order changes:

- Verify the DOM/browser output, not just the source file.
- Disable or clear browser/Babel cache when needed because runtime Babel can keep transformed code.
- Check both visible swatches and tooltip content where the UI uses tooltip offloading.

For data/API changes:

- `/api/all` must return HTTP 200.
- Run focused tests when backend classification or parser logic changes.
