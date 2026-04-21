# AGENTS.md - SGT 2.1

## Project rules
- This repository is a Flask application.
- Use SQLAlchemy/Flask-SQLAlchemy for persistence.
- Use OR-Tools CP-SAT for monthly shift optimization.
- Keep rules in the database as configurable data.
- Implement rule families in code as generic evaluators.
- Maintain multi-tenant separation by client and branch.
- Keep entities activatable/deactivatable instead of hard deleting them.
- Respect Chilean labor constraints.
- Prefer monthly global planning over greedy assignment.

## Files to read first
- PROJECT_CONTEXT.md
- especificacion-funcional-sistema-turnos.md
- .cursor/rules/sgt-context.mdc
- .cursor/rules/scheduling.mdc

## Editing constraints
- Do not change business rules without updating the context documents.
- Do not add new rule types without defining their family and evaluator pattern.
- If a new rule requires special handling, document it in the context first.
