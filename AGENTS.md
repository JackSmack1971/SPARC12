# AGENTS.md: AI Collaboration Guide

This document provides essential context for AI models interacting with this project. Adhering to these guidelines will ensure consistency, maintain code quality, and optimize agent performance within the SPARC12 framework.

## 1. Project Overview & Purpose

* **Primary Goal:** SPARC12 is a comprehensive template for building AI-assisted software projects using the Roo Code ecosystem. It codifies the SPARC methodology, breaking development into 12 clearly defined phases with specialized AI modes, persistent context management, and security-first practices.
* **Business Domain:** AI-Assisted Software Development, Development Framework Templates, Structured Development Methodologies.
* **Key Features:** 12-phase SPARC methodology, custom AI mode system with role-based permissions, memory bank architecture for persistent context, security-first design with comprehensive `.rooignore`, automated quality gates, template-based project initialization.

## 2. Core Technologies & Stack

* **Languages:** Shell/Bash (automation scripts), Markdown (documentation), JSON (configuration), Python 3.8+ (enhanced server components).
* **Frameworks & Runtimes:** Roo Code Custom Modes (primary framework), GitHub Actions (CI/CD), SQLite (enhanced context portal), Model Context Protocol (MCP).
* **Databases:** File-based persistence via memory bank structure (primary), SQLite (enhanced context portal with semantic search).
* **Key Libraries/Dependencies:** bandit (Python security scanning), markdownlint-cli (Markdown linting), scikit-learn (semantic search), mcp (Model Context Protocol), pytest (testing framework).
* **Package Manager:** Git (for template distribution), npm (for markdown tooling when used), pip (for Python dependencies).
* **Platforms:** Cross-platform (designed to work with any Roo Code-compatible environment).

## 3. Architectural Patterns & Structure

* **Overall Architecture:** Template-based development framework with phase-driven AI mode specialization. The system orchestrates 12 development phases (Specification → Pseudocode → Architecture → Implementation → Testing → Security → QA → Integration → Deployment → Documentation) with dedicated AI modes for each phase.
* **Directory Structure Philosophy:**
  * `.roo/` - Roo Code configuration including custom mode definitions and instructions
  * `memory-bank/` - Persistent project context, phase tracking, and architectural decisions
  * `.tools/` - Development utilities and quality validation scripts
  * `.github/workflows/` - CI/CD automation pipelines
  * `docs/` - Project documentation and deliverables
  * `sparc-server/` - Enhanced MCP server implementation with semantic search
  * `tests/` - Python test suite for server components
* **Module Organization:** Each development phase is handled by a specialized AI mode with specific file access permissions defined in `.roomodes`. Context flows through the memory bank system, maintaining project knowledge across phase transitions.
* **Common Patterns & Idioms:**
  * **Mode Specialization:** Each AI mode has specific responsibilities and file access patterns
  * **Context Preservation:** Memory bank maintains decisions and context across phases
  * **Security-First:** Comprehensive `.rooignore` patterns protect sensitive information
  * **Quality Gates:** Automated validation prevents progression with unresolved issues
  * **Handoff Protocols:** Structured transitions between development phases

## 4. Coding Conventions & Style Guide

* **Formatting:** Markdown follows standard conventions with relative links. JSON uses 2-space indentation. Shell scripts use `set -euo pipefail` for safety. Python follows PEP 8 standards. Maximum line length varies by file type but generally follows readability standards.
* **Naming Conventions:**
  * Mode slugs: `kebab-case` (e.g., `sparc-orchestrator`, `sparc-code-implementer`)
  * Memory bank files: `snake_case` or `kebab-case` (e.g., `current-phase.md`, `architectural-decisions.md`)
  * GitHub workflows: `kebab-case` (e.g., `sparc-quality.yml`)
  * Documentation files: `kebab-case` or `camelCase` depending on context
  * Python: `snake_case` for variables, functions, methods, files; `PascalCase` for classes
* **API Design Principles:** The framework emphasizes clear role separation, explicit handoffs between phases, and maintaining comprehensive context. Each mode has well-defined responsibilities and file access patterns.
* **Documentation Style:** Memory bank documentation should be concise and actionable. Each phase produces specific deliverables documented in `memory-bank/phases/`. All mode instructions follow a consistent template structure.
* **Error Handling:** Shell scripts use strict error handling with `set -euo pipefail`. Python uses standard exception handling with custom exception classes. Quality checks provide clear pass/fail criteria. Security validation is mandatory and blocking.
* **Forbidden Patterns:** **NEVER** commit secrets or credentials to any tracked files. **NEVER** bypass security validation in `.rooignore`. **NEVER** skip quality gates between phases.

## 5. Development & Testing Workflow

* **Local Development Setup:**
  1. Install Roo Code CLI from official documentation
  2. Clone the SPARC12 template: `git clone https://github.com/JackSmack1971/SPARC12.git my-new-project`
  3. Initialize for your project: Update `projectBrief.md`, configure `.roomodes` if needed
  4. Set initial phase: `echo "research" > memory-bank/current-phase.md`
  5. For enhanced features: `pip install -r sparc-server/requirements.txt`
* **Build Commands:**
  * Run quality validation: `./.tools/quality-check.sh`
  * Markdown linting: `markdownlint '**/*.md' --ignore AGENTS.md`
  * Python tests: `pytest tests/` (for enhanced server components)
* **Testing Commands:** **All development phases require corresponding validation.**
  * Quality checks: `./.tools/quality-check.sh` (validates task markers, secrets, file sizes)
  * Security scan: `bandit -r .` (Python security analysis)
  * Markdown validation: `markdownlint '**/*.md'`
  * Python tests: `pytest -q` (for server components)
  * **CRITICAL:** Quality checks **MUST** pass before phase transitions
  * **MUST** mock any external dependencies to ensure tests do not make external calls
* **Linting/Formatting Commands:** **All content MUST pass quality checks before committing.**
  * Shell script validation: Built into quality checks
  * JSON validation: Built into quality checks
  * Documentation standards: Built into quality checks
  * Python: Use `black`, `isort`, `flake8` for formatting and linting
* **CI/CD Process Overview:** GitHub Actions automatically run quality checks, security scans, and documentation validation on every pull request. No code merges until all workflows pass.

## 6. Git Workflow & PR Instructions

* **Pre-Commit Checks:** **ALWAYS** run `./.tools/quality-check.sh` and ensure no errors before committing. Verify no unfinished task markers, secrets, or oversized files exist.
* **Branching Strategy:** Work on feature branches for framework improvements. **DO NOT** commit directly to `main` branch.
* **Commit Messages:** Follow clear, descriptive commit message format. Include: What changed? Why? Any breaking changes to the framework? Consider following Conventional Commits specification (e.g., `feat:`, `fix:`, `docs:`).
* **Pull Request (PR) Process:**
  1. Ensure your branch is up-to-date with `main`
  2. Run all quality checks and ensure they pass
  3. Update relevant memory bank documentation
  4. Create PR with clear description of framework improvements
* **Force Pushes:** **NEVER** use `git push --force` on `main` branch. Use `git push --force-with-lease` on feature branches only when necessary.
* **Clean State:** **You MUST leave the repository in a clean state after completing any work** - no uncommitted changes, no untracked files, no temporary artifacts.

## 7. Security Considerations

* **General Security Practices:** **Security is the highest priority in SPARC12.** The framework is designed with security-first principles. Be extremely mindful when handling file access patterns and mode permissions.
* **Sensitive Data Handling:** **NEVER** hardcode secrets, API keys, or credentials in any files. The comprehensive `.rooignore` is designed to prevent accidental exposure. Always use environment variables for sensitive data in actual projects.
* **Input Validation:** Validate all user inputs when customizing the framework. Ensure mode permissions are correctly configured to prevent unauthorized file access.
* **Vulnerability Avoidance:** The framework includes automated security scanning. Generate secure configurations that prevent common weaknesses. Always verify `.rooignore` patterns are comprehensive before any development phase.
* **Dependency Management:** Keep all tooling dependencies updated. Use only trusted tools for quality checks and security scanning.
* **Principle of Least Privilege:** Each AI mode operates with minimal necessary file access permissions. Never expand permissions beyond what's required for the specific phase.

## 8. Specific Agent Instructions & Known Issues

* **Mode Usage and Activation:**
  * Always check `memory-bank/current-phase.md` to understand the active development phase
  * Use `roo --mode sparc-[specific-mode]` to activate appropriate modes
  * Only use modes appropriate for the current phase (enforced by mode instructions)
  * Start with `sparc-orchestrator` for phase coordination
* **Memory Bank Management:**
  * **ALWAYS** update `memory-bank/phases/[phase]-status.md` when completing work
  * Update `memory-bank/context/` files with decisions and patterns
  * Keep memory bank documentation concise and actionable
  * Never skip memory bank updates - they provide critical context for subsequent phases
* **Quality Assurance & Verification:**
  * **ALWAYS** run `./.tools/quality-check.sh` before considering any work complete
  * Verify no unfinished task markers exist in main branch (quality check enforces this)
  * Ensure no secrets or credentials are in tracked files
  * Validate file sizes remain under 1MB limit
  * **ALL quality checks must pass before phase transitions**
  * For Python components: Run `pytest -q` and ensure all tests pass
* **Security-Specific Instructions:**
  * **FIRST ACTION** when using any implementation mode: verify `.rooignore` coverage
  * Never modify `.rooignore` to be less restrictive without explicit justification
  * Document any security patterns in `memory-bank/context/security-patterns.md`
  * Security review is mandatory - never skip `sparc-security-reviewer` mode
* **Framework-Specific Patterns:**
  * This is a **template framework**, not an application - focus on framework improvements and template quality
  * Each mode has specific file access patterns - respect the permissions defined in `.roomodes`
  * Phase transitions require orchestrator coordination - don't jump between phases arbitrarily
  * Context preservation is critical - always update memory bank before mode handoffs
* **Enhanced Context Portal (sparc-server/):**
  * Use `python sparc-server/specialized_mcp_server.py <workspace_path> --action status` to check system status
  * For MCP integration: Configure `.roo/mcp.json` with proper server settings
  * Run `pip install -r sparc-server/requirements.txt` for enhanced semantic search capabilities
* **Troubleshooting & Debugging:**
  * If quality checks fail, examine the specific error output from `./.tools/quality-check.sh`
  * For mode permission issues, verify the file regex patterns in `.roomodes`
  * For phase confusion, check `memory-bank/current-phase.md` and relevant status files
  * Always provide full error output when reporting issues
  * For Python components: Include full stack traces and use `pytest -v` for detailed test output
* **Breaking Down Large Work:**
  * Framework improvements should be broken into logical phases following SPARC methodology
  * Each phase should have clear deliverables and updated memory bank documentation
  * Use the orchestrator mode to coordinate complex multi-phase improvements
* **Avoidances/Forbidden Actions:**
  * **DO NOT** modify core SPARC phase definitions without comprehensive testing
  * **DO NOT** bypass security validation or quality gates
  * **DO NOT** work outside the designated mode permissions
  * **DO NOT** commit any files that would violate `.rooignore` patterns
  * **DO NOT** skip memory bank documentation updates
  * **DO NOT** use `localStorage` or `sessionStorage` in any artifacts (not supported in Claude.ai environment)
* **Dependencies Management:**
  * For Python dependencies: Use `pip install` and update `requirements.txt`
  * For npm dependencies: Use `npm install` for markdown tooling
  * Always run quality checks after dependency changes
* **Pass/Fail Criteria:** Quality checks define the finish line. The agent stops only when `./.tools/quality-check.sh` passes without errors and all relevant tests are green.
