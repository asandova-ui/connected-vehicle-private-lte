# TP2 Jira Workflow

## Jira Context

- Site: `https://tp2-2026.atlassian.net`
- Project key: `TP2`
- MCP server: `atlassian`

## Operational Scope

Only use Jira inside this implementation scope unless the user explicitly says otherwise:

- `TP2-137` `Implementación CORE (Ordenador 1)`
- `TP2-138` `Implementación EnodeB (Ordenador 2)`
- `TP2-139` `Implementación Coche`
- `TP2-140` `Implementación Jetson`
- `TP2-165` `Implementación Integración`

Direct subtasks under those five parent tasks are in scope too.

Canonical JQL:

```jql
project = TP2 AND (issuekey in (TP2-137, TP2-138, TP2-139, TP2-140, TP2-165) OR parent in (TP2-137, TP2-138, TP2-139, TP2-140, TP2-165))
```

Operational rule:

- Start every Jira check from the canonical JQL above.
- Read, comment, edit, and transition only issues returned by that filter.
- Do not browse or operate on the rest of the `TP2` backlog unless the user expands scope.

## Jira Is Part Of The Operating Loop

For non-trivial work:

1. Run the canonical implementation-scope JQL and identify the relevant issue inside that result set.
2. Confirm the issue is still open or actively in progress.
3. Perform the technical change.
4. Validate the change.
5. Add a Jira comment summarizing:
   - what changed
   - what was validated
   - any remaining blockers
6. Transition the issue only if the runtime state matches the Jira state.

## In-Scope Parent Issues

- `TP2-137`: CORE / EPC implementation
- `TP2-138`: eNodeB implementation
- `TP2-139`: car implementation
- `TP2-140`: Jetson implementation
- `TP2-165`: end-to-end integration implementation

## Commenting Standard

Use short operational comments. Include:

- machine affected
- service affected
- validation performed
- blocker if any

Example structure:

- machine: EPC
- change: aligned backend service contract and startup order
- validation: docs updated; live runtime validation still pending
- blocker: none

## Do Not

- Mark issues complete before validation.
- Update Jira based on guesses about the machine state.
- Use Jira as a substitute for real runtime checks.
