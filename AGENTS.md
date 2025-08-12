# AGENTS.md — Roo Code Agent Architecture, Modes, and Operational Playbook
**Owner:** Engineering Enablement / AgentOps  
**Scope:** Global guidance for designing, validating, and operating Roo Code agents (modes) across projects  
**Audience:** Architects, Staff+ Engineers, Toolsmiths, SecEng, QA, PM

---

## 0) How to Use This Doc
- **Copy-paste ready** templates live under **§8 Templates**.
- **Ship-safe defaults**: start with **§3.2 Baseline Custom Instructions** and **§4 Security & Least-Privilege**.
- **Validate before merge**: run checks in **§6 Validation & CI Hooks**.
- **Decompose work**: apply **§2.3 Orchestrated Multi-Mode Pattern** with handoff contracts in **§8.3**.
- **Troubleshoot fast**: see **§7 Common Failures & Fixes**.

---

## 1) Architecture Overview
### 1.1 What “Agents” Mean in Roo Code
Roo Code exposes **modes**—constrained tool permission sets + role definitions—bound to the VS Code extension runtime. Each mode is a **persona** with:
- **`roleDefinition`**: the core behavior injected at the start of the system prompt.
- **`groups`**: tool capability boundaries (`read`, `edit`, `browser`, `command`, `mcp`), with optional **fileRegex** for surgical write scopes.
- **`customInstructions`**: optional tail guidance for tactics and conventions. :contentReference[oaicite:0]{index=0}

### 1.2 Canonical Project Layout
```

project-root/
├── .clinerules                 # Global rules (optional legacy/global guidance)
├── .roomodes                   # Project-level custom modes (JSON or YAML)
├── projectBrief.md             # High-level context (product/tech/standards)
└── .roo/
├── memory-bank/            # RooFlow persistence (active/product/progress/decisions)
├── rules-{slug}/           # Mode-specific rules bundles (markdown/text)
└── mcp.json                # Project-scoped MCP servers & creds (principle of least privilege)

```
Rationale: keeps **global vs project context clean**, enables **persistent memory**, and **isolates** mode rules. :contentReference[oaicite:1]{index=1}

> **Migration note:** Prefer **`.roo/rules-{mode}`** directories over legacy `.clinerules-{slug}` single files in modern Roo Code (3.25.x+). Directory rules are the robust, supported path for mode-specific prompt material. :contentReference[oaicite:2]{index=2}

---

## 2) Mode System Design
### 2.1 Mode Schema (Required / Optional)
- **Required:** `slug` (unique lowercase-hyphen), `name` (≥1 char), `roleDefinition` (non-empty), `groups` (tool permissions).
- **Optional:** `customInstructions` (tail guidance).  
Constraints: **unique slugs**, **no duplicate groups**, **valid regex**, **UTF-8 text rules**. :contentReference[oaicite:3]{index=3}

### 2.2 Tool Groups & Least-Privilege
Available groups: `read`, `edit`, `browser`, `command`, `mcp`.  
**Rule of thumb:** enable **only** what the role truly needs; gate `edit` with **`fileRegex`** to reduce blast radius. :contentReference[oaicite:4]{index=4}

### 2.3 Orchestrated Multi-Mode Pattern
Use a **planning/brain** (read-heavy), **implementation specialists** (scoped edit), **reviewers/testers** (read+limited edit), and an **implementation orchestrator** that:
- Reads **handoff artifacts** (hash-verified)
- Instructs the next mode by **writing context files**
- Advances a **cursor** in `.roo/handoffs/next.json`  
This achieves **deterministic progress**, **auditability**, and **safety**. :contentReference[oaicite:5]{index=5}

---

## 3) Prompting & Instructions
### 3.1 Role Definition Principles
- **Purpose over poetry**: describe outcomes, constraints, and decision criteria.
- **Ban runtime side-effects**: no implicit permission granting, no shell directives in role text.
- **Phase clarity**: ANALYZE → PLAN → (optionally) EDIT; document before edits. :contentReference[oaicite:6]{index=6}

### 3.2 Baseline Custom Instructions (Apply to All Modes)
Use this block in `customInstructions` unless a mode explicitly overrides it:
```

Follow this operating protocol:

1. READ FIRST: summarize goal, constraints, and unknowns from current context.
2. PLAN: list minimal steps; call out risks, assumptions, and success checks.
3. ACTION: only within your tool permissions. Never exceed scope implied by `groups`.
4. EVIDENCE: reference specific files/lines when asserting facts or making changes.
5. MINIMUM CHANGE: prefer smallest diff that satisfies acceptance criteria.
6. LOGGING: write brief rationale to progress/decision logs when provided.
7. EXIT CRITERIA: state what’s done, what’s blocked, what’s next handoff.
   Security guardrails:

* Never run arbitrary commands unless `command` is granted and required.
* Only edit files that match your `fileRegex`. Refuse otherwise.
* Treat secrets and tokens as sensitive; never print or persist them.
  Performance:
* Keep outputs concise; avoid repeating large context verbatim.
* Prefer links/paths over inlining long content.

````
(See **§4** for stricter security gates.)

---

## 4) Security & Least-Privilege
### 4.1 Checklist (apply per mode)
- [ ] Unique `slug`; distinct `name`.
- [ ] `groups` contain **no duplicates**; only the **minimal set**.
- [ ] `edit` has **`fileRegex`** scoped to necessity (path + ext).
- [ ] Regex validated (anchors, escapes, catastrophic backtracking avoided).
- [ ] Rules stored in **`.roo/rules-{slug}/`**; UTF-8; no binaries.
- [ ] No secrets in role text/rules; use env or secret manager via MCP if needed.
- [ ] Handoff artifacts use **hash fields**; verify before acting.
- [ ] Logs redact PII/secrets; commit to repo only if compliant. 

### 4.2 File Regex Patterns (safe starters)
- Frontend only: `^src/(components|pages)/.*\.(tsx|ts|jsx|js|css|scss)$`
- Docs only: `^(docs|README\.md|CHANGELOG\.md|\.roo/rules-[^/]+/).*\.mdx?$`
- Tests only: `^src/.*\.(test|spec)\.(ts|tsx|js)$`  
(*Tune anchors to your tree; always test against full paths.*) :contentReference[oaicite:8]{index=8}

---

## 5) Performance & Token Strategy
- **Short role, long rules**: keep `roleDefinition` crisp; move playbooks to `.roo/rules-{slug}/`.  
- **Disable unused MCP** to halve prompt size in many setups.  
- **Avoid redundant context** and large pasted blobs; cite file paths instead. :contentReference[oaicite:9]{index=9}

---

## 6) Validation & CI Hooks
### 6.1 Schema Checks
- Confirm **required fields** present and non-empty.
- Verify **unique slugs** and **non-duplicated groups**.
- Compile **`fileRegex`** with your runtime regex engine; fail on error. :contentReference[oaicite:10]{index=10}

### 6.2 Pre-Commit (example)
- Lint `.roomodes` (JSON/YAML), validate regex, and ensure rules folders exist:
```bash
# package.json scripts (example)
"scripts": {
  "agents:lint": "node .tools/agents-validate.mjs"
}
````

```js
// .tools/agents-validate.mjs (sketch)
import fs from "node:fs"; import path from "node:path";
import { parse } from "yaml";
import { pathToFileURL } from "node:url";

const file = fs.readFileSync(".roomodes", "utf8");
const data = file.trim().startsWith("{") ? JSON.parse(file) : parse(file);
const modes = data.customModes || [];

const slugs = new Set();
for (const m of modes) {
  if (!m.slug || !m.name || !m.roleDefinition || !m.groups) throw new Error(`Missing required field in ${m.name||m.slug}`);
  if (slugs.has(m.slug)) throw new Error(`Duplicate slug: ${m.slug}`);
  slugs.add(m.slug);

  const groupSet = new Set();
  for (const g of m.groups) {
    const key = Array.isArray(g) ? g[0] : g;
    if (groupSet.has(key)) throw new Error(`Duplicate group '${key}' in ${m.slug}`);
    groupSet.add(key);
    if (Array.isArray(g) && g[1]?.fileRegex) new RegExp(g[1].fileRegex); // throws if invalid
  }
  const rulesDir = path.join(".roo", `rules-${m.slug}`);
  if (!fs.existsSync(rulesDir)) console.warn(`(info) Missing ${rulesDir} — create if you plan mode-specific rules`);
}
console.log(`Validated ${modes.length} modes ✅`);
```

---

## 7) Common Failures & Fixes

| Failure                   | Root Cause                                 | Fix                                             |
| ------------------------- | ------------------------------------------ | ----------------------------------------------- |
| “Mode not loading”        | Missing required field / bad YAML          | Validate schema; use **§6** script              |
| Edits in wrong files      | Missing/loose `fileRegex`                  | Add anchored, escaped path regex                |
| Duplicated behavior bleed | Centralized/legacy `.clinerules` spillover | Migrate to `.roo/rules-{slug}/` dirs            |
| Token bloat / truncation  | Long `roleDefinition` or unused MCP        | Move playbooks to rules dir; disable unused MCP |
| Silent rules              | Wrong file place/encoding                  | Ensure UTF-8, **project root** placement        |

---

## 8) Templates (Copy-Paste)

### 8.1 Mode Schema (YAML, project-level `.roomodes`)

```yaml
customModes:
  - slug: impl-orchestrator
    name: "🧭 Implementation Orchestrator"
    roleDefinition: >-
      Load .roo/handoffs/next.json, validate brief hashes, instruct the indicated
      implementation mode via context files, then advance the cursor atomically.
      Never write application code directly.
    groups:
      - read
      - - edit
        - fileRegex: '^\.roo/(handoffs|memory-bank)/.*\.(md|mdx|json)$'
          description: Handoff & progress context only
      - - edit
        - fileRegex: '^docs/(knowledge|qa|security)/.*\.(md|mdx)$'
          description: Status docs during implementation
      - mcp
    customInstructions: >-
      Source of truth: .roo/handoffs/next.json. Abort if hash mismatch.
      Emit: context-for-{nextSlug}.md and next-action.md. Log to memory-bank.
      Refuse to edit app src; delegate to specialists via handoff contracts.

  - slug: impl-specialist-fe
    name: "🧩 Frontend Implementer"
    roleDefinition: >-
      Implement minimal, tested UI changes per handoff. Follow design tokens,
      a11y rules, and TDD where feasible.
    groups:
      - read
      - - edit
        - fileRegex: '^src/(components|pages)/.*\.(tsx|ts|jsx|js|css|scss)$'
          description: Frontend sources only
      - command
    customInstructions: >-
      Work from context-for-impl-specialist-fe.md. Summarize plan, then apply
      smallest diff. If scope exceeds regex, pause and request new handoff.

  - slug: qa-tester
    name: "✅ QA Tester"
    roleDefinition: >-
      Write and run focused tests for recent changes. Report defects with steps,
      expected vs actual, and severity.
    groups:
      - read
      - - edit
        - fileRegex: '^src/.*\.(test|spec)\.(ts|tsx|js)$'
          description: Test files only
      - command
    customInstructions: >-
      Prioritize edge cases and acceptance criteria from handoff. Produce concise
      bug reports with file/line references.
```

### 8.2 Mode Schema (JSON, global `custom_modes.yaml/json` equivalent)

```json
{
  "customModes": [
    {
      "slug": "security-auditor",
      "name": "🛡️ Security Auditor",
      "roleDefinition": "Act as an expert security researcher. Identify and remediate high-risk vulnerabilities. Analyze -> Plan -> Minimal Fix -> Verify.",
      "groups": ["read", "command"],
      "customInstructions": "Document each finding with file/line and impact. Propose minimal code changes with security rationale."
    }
  ]
}
```

(Struct matches required fields and group semantics.)&#x20;

### 8.3 Handoff Contract (for Orchestrator ↔ Specialists)

**`.roo/handoffs/next.json` (authoritative pointer)**

```json
{
  "cursor": 7,
  "nextSlug": "impl-specialist-fe",
  "briefPath": ".roo/handoffs/briefs/007-fe-button-a11y.json",
  "briefHash": "sha256:....",
  "contextFiles": [
    ".roo/handoffs/context-for-impl-specialist-fe.md"
  ],
  "acceptance": [
    "Button is keyboard operable and has visible focus",
    "ARIA label matches spec",
    "Unit tests cover keyboard and ARIA"
  ]
}
```

**`context-for-impl-specialist-fe.md`**

```markdown
# Context: FE A11y Fix — Button
## Scope
- File(s): src/components/Button.tsx, src/components/Button.test.tsx
- Do not touch unrelated components or styles.

## Constraints
- Follow design tokens
- Maintain existing API and theming

## Acceptance Criteria
1) Keyboard operable with visible focus
2) ARIA label passes audit
3) Tests updated and passing

## Risks/Notes
- Avoid breaking snapshot tests; update intentionally if needed.
```

---

## 9) MCP Integration (Project-Scoped)

* Configure per project in **`.roo/mcp.json`**; include **only necessary servers**.
* Gate tools by mode: **orchestrator** gets read/mcp; **implementers** get command only if required; **auditors** often `read` + optional `command`.
  This **reduces prompt size** and **limits external access**.&#x20;

---

## 10) Memory & Logging (RooFlow)

* Use `.roo/memory-bank/activeContext.md` to track current task.
* Persist decisions in `decisionLog.md`; summarize in `progress.md`.
  Benefits: **continuity**, **audit trail**, **lower token spend**.&#x20;

---

## 11) Governance & Versioning

* Track **all** mode/rule changes via PRs with reviewers from AppSec + Tooling.
* **Changelog** entries: describe permission changes and rationale.
* **Rollout** via feature branch; test in a sandbox repo before globalizing.

---

## 12) FAQ (Short)

* **YAML vs JSON?** Use either; keep **`.roomodes`** in project root.&#x20;
* **Where do detailed playbooks live?** In `.roo/rules-{slug}/` as Markdown/text.&#x20;
* **Are `.clinerules-{slug}` still supported?** Treat as legacy; prefer rules directories.&#x20;

---

## 13) Appendix — Risk Controls Mapping

* **Principle of least privilege** → `groups` + `fileRegex`.
* **Change control** → PR reviews on `.roomodes` and rules dirs.
* **Tamper evidence** → hash fields in handoffs; decision logs.
* **Data minimization** → concise outputs, avoid secret echoing.

---
