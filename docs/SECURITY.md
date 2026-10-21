# TP2 Security Boundaries

## Secret Handling

- Do not store SSH passwords in repository files.
- Do not commit tokens for Jira, GitHub, or any external service.
- Use local environment configuration or external auth flows only.

## Remote Operations

- Prefer read-only inspection before changes.
- Avoid restarting working network services without a clear reason.
- Avoid changing multiple remote machines at once.

## Service Exposure

- PostgreSQL should not be exposed to the UE directly.
- The Jetson inference API should only be reachable from trusted internal hosts, ideally the EPC.
- MQTT should be exposed only as required for the car.

## Safety Of Motion Commands

- Always keep a watchdog path on the car.
- Missing, delayed, or invalid commands must degrade to a safe action.
- Inference confidence alone should not bypass operational safety rules.

## Change Control

- For destructive remote actions, stop and confirm first.
- If the live state is unclear, inspect more before changing Jira or services.

