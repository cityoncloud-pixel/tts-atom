# Execution Rules (AI-owned)

## Consent Gate
- 在开始连续实现前必须获得 Owner 明确同意（见 `project_control/approval.json` 或聊天 `APPROVE`）。
- 未同意前只做澄清与 spec/plan 提案，不做代码实现（除非 Owner 明确授权 Tiny Fix）。

## Scope Discipline
- 只做 plan/spec 中列出的内容；新增工作先更新 plan 并写入 `project_control/decision_log.md`。

## Safety
- 默认避免破坏性操作（删除/迁移/重置数据/大重构）；确需执行必须先征得 Owner 决策。

## Reporting (每次循环必须落盘)
写 `reports/*.report.md`，至少包含：
- Done / Not done
- Verification steps + results
- Risks / Follow-ups
- Next task suggestion

## Git Discipline (Professional Default)
After Owner approval, AI should treat git as part of the delivery pipeline:
- Preconditions:
  - The project must be a git repo (`.git/` exists)
  - `origin` remote must exist and be pushable
- Workflow per subtask:
  1) Implement changes
  2) Run minimal verification (commands or manual steps) and record in `reports/*.report.md`
  3) `git status` must be understood (no surprise files)
  4) `git add -A`
  5) `git commit -m "<type>(<scope>): <summary>"`
  6) `git push origin <current-branch>`
- If any precondition fails (no git / no origin / auth issue), stop and ask Owner.

