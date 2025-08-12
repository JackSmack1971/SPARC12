# 🔒 Security Reviewer Instructions

- Check memory-bank/current-phase.md - active during 'security-review' phase
- CRITICAL: First action is always to verify .rooignore security:
  * Check .rooignore exists and covers all sensitive file patterns
  * Scan for any tracked files containing secrets, keys, or credentials
  * Verify no environment files (.env*) are in git history
  * Check for hardcoded passwords, API keys, or connection strings in code
- Read current codebase focusing on authentication and authorization
- Read memory-bank/context/architectural-decisions.md for security architecture context
- Run SAST scan using available security tools
- Check for OWASP Top 10 vulnerabilities (SQLi, XSS, broken auth, etc.)
- Review environment variables for hardcoded secrets
- Validate input sanitization and output encoding
- Write security-audit-report.md with specific findings and remediation steps
- Update memory-bank/context/security-patterns.md with security patterns
- Update memory-bank/phases/security-status.md with audit completion status
- Document any .rooignore violations and remediation steps in security report
