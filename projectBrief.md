# Project Brief

This brief provides a high‑level overview of the SPARC12 template and its intended use within the Roo Code ecosystem.  It is designed to give agents and human collaborators enough background to understand the project's scope, goals and workflow without exposing unnecessary implementation details.

## Purpose and Scope

The SPARC12 repository is a template for building AI‑assisted software projects using Roo Code.  It codifies the **SPARC** methodology, which breaks development into clearly defined phases: **S**pecification, **P**seudocode design, **A**rchitecture, **R**ealisation (implementation), **C**ode quality and security review, QA/Integration, Deployment and Documentation.  Each phase is represented by a custom mode with its own tool permissions and instructions.  The template also defines a **memory bank** directory for persistent context and a `.rooignore` file to enforce least‑privilege file access.

## Goals

* Provide a structured starting point for multi‑agent software development using Roo Code.
* Demonstrate best practices around mode configuration, file organisation, security and quality gates.
* Encourage the use of a central memory bank for storing artefacts such as pseudocode, architecture decisions and phase summaries.
* Facilitate integration with external tools via the Model Context Protocol (MCP) through a project‑level `.roo/mcp.json` file.

## Overview of the SPARC Workflow

1. **Specification:** Capture and refine requirements, define acceptance criteria and scope the work.  Artefacts are stored in `docs/`.
2. **Domain Intelligence:** Gather domain knowledge and contextual information to inform design decisions.  Results are recorded in `docs/` and referenced throughout the project.
3. **Pseudocode Design:** Translate specifications into algorithmic blueprints and implementation strategies.  Drafts are stored in `memory‑bank/pseudocode.md`.
4. **Architecture:** Design system components, technology choices and integration patterns.  Decisions live in `memory‑bank/architecture.md` and `memory‑bank/context/`.
5. **Implementation & Testing:** Implement code following the designs, accompanied by test‑driven development and security reviews.  Source lives in `apps/`, `packages/` or `src/`, and tests in `tests/`.
6. **Quality Assurance & Integration:** Validate functionality, performance and accessibility, then ensure all components work together before delivery.
7. **Deployment & Documentation:** Prepare CI/CD pipelines and infrastructure, then produce user and technical documentation.

## Usage Notes

* Populate the **memory bank** with relevant context as the project progresses.  Use files like `pseudocode.md`, `architecture.md` and `context/architectural-decisions.md` to record design rationales and important decisions.
* Configure at least one MCP server in `.roo/mcp.json` if modes request `mcp` access.  This file contains placeholders which should be replaced with actual command and environment details.
* Review and update the `.roomodes` file whenever new modes are added or existing ones change.  Duplicate group entries have been consolidated in this version to comply with Roo Code schema guidelines.

This brief should evolve alongside the project.  As new requirements, constraints or decisions arise, update this document to reflect the current state of the project and to aid future contributors.