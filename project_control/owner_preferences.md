# owner_preferences.md (Owner-owned)

## Preferences
- Output language: Chinese preferred
- Style: concise, actionable, avoid unnecessary tech-detail questions

## Git Policy (Default)
- Owner will create the GitHub repo first (GAEH will NOT auto-create repos).
- Owner will set up `origin` in the local repo (GAEH will NOT guess remote URLs).
- AI default behavior after approval:
  - For each completed & verified subtask: `git add` → `git commit` → `git push` to `origin`
  - Keep commits small, meaningful, and aligned with the task queue

AI must stop and ask Owner when:
- The project is not a git repo (missing `.git/`)
- `origin` remote is missing or push is not permitted
- Branching strategy change is needed (e.g., create/switch branches)
- There is any risk of committing secrets or sensitive files

Commit convention (recommended):
- Message: `<type>(<scope>): <summary>` (Conventional Commits style)
- Every commit must include minimal verification results in `reports/*.report.md`

## Constraints
- Forbidden without confirmation: destructive operations (delete/reset/migrate data)
- Allowed: necessary engineering decomposition, implementation, verification, rollback

