# Jetson Identity And Apt Repair

- Date: `2026-03-12`
- Jira: `N/A (Atlassian MCP no disponible en esta sesion)`
- Machine: `tp2-jetson` (previous hostname: `grupo2tpii-desktop`)
- Scope:
  - normalize Jetson SSH identity
  - repair broken `apt` state caused by CUDA package dependency conflicts

## Initial State

- SSH access worked to the Jetson over Tailscale.
- Active Jetson identity:
  - hostname: `grupo2tpii-desktop`
  - user: `grupo2tpii`
  - Tailscale IP: `100.115.99.8`
  - management LAN IP: `192.168.72.127`
- `apt` was broken with unmet dependencies involving:
  - `cuda-libraries-12-6`
  - `nvidia-cuda`
- `apt-get -s install` reported missing CUDA `12.6` dependencies.
- `apt --fix-broken install` initially failed because several CUDA packages tried to overwrite identical symlink paths under:
  - `/usr/local/cuda-12.6/lib64`
  - `/usr/local/cuda-12.6/include`
- A live local GNOME session was active for `grupo2tpii`, so an in-place rename of the logged-in user was not safe without terminating that session.

## Applied Change

- Changed the system hostname to:
  - `tp2-jetson`
- Updated the Tailscale hostname to:
  - `tp2-jetson`
- Created a new primary admin user:
  - `grupo4`
- Added `grupo4` to the relevant admin and device groups:
  - `adm`
  - `sudo`
  - `audio`
  - `dip`
  - `video`
  - `plugdev`
  - `render`
  - `i2c`
  - `lpadmin`
  - `gdm`
  - `sambashare`
  - `weston-launch`
  - `gpio`
- Migrated the home content from `/home/grupo2tpii` to `/home/grupo4` with `rsync`, excluding transient trash data.
- Repaired the broken CUDA package state by running:
  - `sudo apt-get -o Dpkg::Options::="--force-overwrite" --fix-broken install -y`
- This was required because the CUDA `12.6` packages from the Jetson repos shipped identical symlinks and `dpkg` otherwise stopped on file-overwrite conflicts.

## Validation

- SSH validated over Tailscale with the new account:
  - `ssh grupo4@tp2-jetson`
- Remote identity validated:
  - user: `grupo4`
  - hostname: `tp2-jetson`
  - Tailscale IP: `100.115.99.8`
- `sudo apt-get check` completed without dependency errors.
- `dpkg --audit` returned no pending broken-package state.
- `apt-get -s install` reported:
  - `0 upgraded, 0 newly installed, 0 to remove`

## Current Access

- Primary:
  - `ssh grupo4@tp2-jetson`
- Alternate:
  - `ssh grupo4@100.115.99.8`
  - `ssh grupo4@192.168.72.127`

## Remaining Note

- The legacy account `grupo2tpii` remains present temporarily because the original graphical desktop session was still active during this remote change window.
- If you later want a strict in-place cleanup, the next safe step is:
  - log out the old desktop session
  - then retire or rename the legacy account from `grupo4`
