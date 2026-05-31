# AGENTS.md instructions for C:\Users\Cristian Valverde\Git Repos\hermes-dashboard

## Repository memory policy
- After running `/repo-init`, always persist a concise repository snapshot in `CONTEXT.md`.
- If `CONTEXT.md` exists, update it instead of creating duplicates.
- Keep the snapshot practical for fast startup in new sessions: stack, entrypoints, commands, architecture, data flow, risks, and next checks.
- Add an `Updated:` line with ISO date (`YYYY-MM-DD`).

## Startup expectation for future sessions
- Before coding, read `CONTEXT.md` when present.
- If repository structure changed materially, refresh that file first.
