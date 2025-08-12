# Emergency Procedures

Contingency plan when critical issues threaten progress or security.

## Trigger Conditions
- Failing tests on main branch.
- Newly discovered security vulnerabilities.
- Deployment blockers or data integrity issues.

## Response
1. Halt all active handoffs and freeze `.roo/handoffs/next.json` cursor.
2. Record incident in `memory-bank/phases/orchestrator-status.md` with severity.
3. Create `emergency.md` summarizing impact and mitigation plan.
4. Coordinate rollback or hotfix with relevant specialist modes.
