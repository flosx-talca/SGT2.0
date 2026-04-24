# SGT 2.1 - Project Context

## Overview
SGT 2.1 is a multi-company, multi-branch shift scheduling system for clients such as gas stations and Pronto branches.

## Core concepts
- Super Admin: full access.
- Client: manages its own company context.
- Administrator: manages a selected company context.
- Branches may be separated by RUT.
- Areas include Gasolinera and Pronto.
- Workers may belong to one or both areas when authorized.
- Shifts are configurable per client.
- The current business uses Mañana, Tarde, Intermedio, and Noche as a reference, but this is not fixed.
- Planning is monthly and global.
- Use Flask + SQLAlchemy/Flask-SQLAlchemy + OR-Tools CP-SAT.

## Rule engine principles
- Rules are stored as configuration in the database.
- The code contains generic evaluators by rule family.
- Prefer generic patterns before adding custom code.
- All major entities should support activation/deactivation.

## Main files
- especificacion-funcional-sistema-turnos.md
- .cursor/rules/sgt-context.mdc
- .cursor/rules/scheduling.mdc
- AGENTS.md

## Working rules
- Keep the architecture modular.
- Keep business rules auditable.
- Preserve legal constraints and worker restrictions.
- Do not use greedy scheduling as the primary engine.
- **Sensitive Files (.env)**: Do NOT add `.env` or other sensitive configuration files to `.gitignore`. Since this is a private repository, all sensitive configuration files must be committed and tracked in version control to ensure consistency across the team.
- **Database Schema**: We must maintain a file named `proyecto.sql` in the repository where we will save and update the database schema model in raw SQL format.
- **Agent Behavior**: AI Agents must ALWAYS consult `documentacion/especificacion-funcional-sistema-turnos.md` to understand the project context, but MUST explicitly ask for the user's approval before writing code or making modifications.
- **Roadmap & GitHub Tracking**: We must maintain a development Roadmap broken down into Features and Issues (to be mirrored in the GitHub repository). These Features and Issues must be negotiated and approved by the user.
- **Database Modeling workflow**: During the creation of mantenedores or new modules, the AI must first propose the database tables and their relationships. The user will review, provide observations, and approve the schema before any implementation begins.
- **Rules Engine (REGLAS)**: The "REGLAS" feature is critically important. Agents must deeply understand its context and logic before interacting with it or proposing changes.
- **Multi-Tenant Architecture**: The system is strictly multi-company (multiempresa). All core entities (workers, shifts, rules, branches, etc.) must ALWAYS be associated with a specific company.
- **Progress Tracking & Documentation Language**: We must maintain a progress tracking file (e.g., `documentacion/AVANCES.md`) guided by `especificacion-funcional-sistema-turnos.md`. While this context file is in English, all generated documentation, roadmaps, and progress tracking files MUST be written in Spanish.
- **Frontend Rendering Rule (CRITICAL)**: Data must ALWAYS be loaded on the server BEFORE being displayed to the user. This means:
  - **Modals**: The backend route must query the database, inject all data into the Jinja2 template, and return the fully rendered HTML. The frontend JavaScript must only call `.modal('show')` AFTER the AJAX response is complete and the HTML is already injected into the DOM. Never show a modal and then load data into it.
  - **DataTables / Tables**: Tables must be rendered server-side with data already present in the HTML (via Jinja2 `{% for %}` loops). The DataTable JS plugin is only for UI enhancement (search, sort, pagination), not for data loading.
  - **No skeleton loaders or lazy-fill patterns**: Avoid any pattern where the UI appears first and data is filled in afterwards.
