# 💻 Code Implementer Instructions

- Check memory-bank/current-phase.md - only proceed if in 'implementation' phase
- SECURITY FIRST: Before any coding, verify .rooignore includes:
  * All .env* files (.env, .env.local, .env.production, etc.)
  * API keys and secrets (api-keys.txt, secrets.json, credentials.*)
  * Database connection strings and passwords
  * Build artifacts (dist/, build/, .next/, node_modules/)
  * IDE and OS files (.vscode/settings.json, .DS_Store, Thumbs.db)
  * Local configuration files (config.local.*, *.private.*)
  * Temporary and cache files (*.tmp, *.cache, .temp/)
- Read pseudocode.md and architecture.md before coding
- Read memory-bank/context/architectural-decisions.md for implementation guidance
- Implement functions keeping files under 500 lines
- Write self-documenting code with clear function names
- Add error handling for all external calls and user inputs
- Use environment variables for all configuration (never hardcode secrets)
- Run tests after each significant change
- Update memory-bank/context/implementation-patterns.md with new code patterns
- Update memory-bank/phases/implementation-status.md with progress
- NEVER commit hardcoded secrets, API keys, passwords, or credentials
- Use placeholder values in example configs (API_KEY=your_api_key_here)
- Coordinate with sparc-tdd-engineer for test-first development
