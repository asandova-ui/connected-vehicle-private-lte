# Jetson User Rename Finalization

- Date: `2026-03-12`
- Jira: `N/A (Atlassian MCP no disponible en esta sesion)`
- Machine: `tp2-jetson`
- Scope:
  - replace the temporary `grupo4` account with the original Jetson user data
  - leave only the final `grupo4` account on the machine

## Initial State

- Hostname and Tailscale hostname were already set to `tp2-jetson`.
- SSH access already worked as `grupo4@tp2-jetson`, but that `grupo4` account was still the temporary migration user.
- The original account still existed as:
  - user: `grupo2tpii`
  - uid: `1000`
  - home: `/home/grupo2tpii`
- Temporary admin account also existed:
  - `tp2admin`

## Applied Change

- Confirmed there were no active sessions left for `grupo2tpii`.
- Removed the temporary `grupo4` account and its home directory.
- Renamed the original primary group:
  - `grupo2tpii` -> `grupo4`
- Renamed the original user:
  - `grupo2tpii` -> `grupo4`
- Moved the original home directory:
  - `/home/grupo2tpii` -> `/home/grupo4`
- Updated desktop account metadata:
  - `/var/lib/AccountsService/users/grupo4`
- Updated subordinate uid/gid mappings:
  - `/etc/subuid`
  - `/etc/subgid`
- Updated GECOS/comment field for the final account to `grupo4`.
- Removed the temporary admin user:
  - `tp2admin`

## Validation

- Final SSH access works:
  - `ssh grupo4@tp2-jetson`
- Final account identity:
  - user: `grupo4`
  - uid: `1000`
  - gid: `1000`
  - home: `/home/grupo4`
- Old user removed:
  - `getent passwd grupo2tpii` -> no result
- Temporary user removed:
  - `getent passwd tp2admin` -> no result
- Home directories:
  - `/home` contains only `grupo4`
- `sudo` works with the final account.
- `sudo apt-get check` completes without dependency errors.

## Final Access

- Primary:
  - `ssh grupo4@tp2-jetson`
- Alternate:
  - `ssh grupo4@100.115.99.8`
  - `ssh grupo4@192.168.72.127`
