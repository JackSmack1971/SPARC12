# Handoff Protocols

Standard procedures for transferring work between SPARC modes.

## Checklist
1. Generate brief and context files for the receiving mode.
2. Compute and record SHA-256 hashes for all handoff artifacts.
3. Update `.roo/handoffs/next.json` with `nextSlug`, cursor, and brief hash.
4. Log coordination in `memory-bank/phases/orchestrator-status.md`.

## Validation
- Incoming handoffs must match recorded hashes before execution.
- Each mode acknowledges receipt in the memory bank log.
