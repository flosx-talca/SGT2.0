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
