# EPC Conda Environment For Car1 Manual Control

- Date: `2026-03-12`
- Machine: `tp2-EPC`

## Goal

Provision an isolated Conda environment on the EPC for `servicios/prueba.py` (car 1 manual control) and validate that the script can start on the LTE-side bind address.

## Runtime Evidence

- `conda` was not present initially on the EPC.
- Miniforge installed under:
  - `/home/tp2/miniforge3`
- Conda environment created:
  - `tp2-car1-control`
- Script deployed to runtime path:
  - `/home/tp2/servicios_tp2/prueba.py`
- Source and deployed script hashes match:
  - `sha256 d4ec3b7f34ffcf3c9575881a5db9585ac943ccab305ab70d52b44cf36e7d9c71`
- Package/import validation inside the new environment with active X display:
  - `cv2 4.10.0`
  - `numpy 2.2.6`
  - `pynput` import succeeded when `DISPLAY=:1`
- Runtime bind validation:
  - `DISPLAY=:1 timeout 8s conda run -n tp2-car1-control python -u /home/tp2/servicios_tp2/prueba.py`
  - `ss -lunp` showed listener:
    - `172.16.0.1:20001`

## Operational Notes

- SSH sessions enter the EPC without `DISPLAY`, but the machine has an active graphical session on `:1`.
- `pynput` requires a valid X display; without `DISPLAY=:1` the import fails even if the package is installed.

## Result

- The EPC now has a dedicated Conda environment for car 1 manual control.
- `prueba.py` starts successfully and binds to `172.16.0.1:20001` when launched with `DISPLAY=:1`.
