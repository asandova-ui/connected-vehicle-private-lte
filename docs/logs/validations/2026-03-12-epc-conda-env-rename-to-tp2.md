# EPC Conda Environment Rename To tp2

- Date: `2026-03-12`
- Machine: `tp2-EPC`

## Goal

Rename the car 1 manual-control Conda environment from `tp2-car1-control` to `tp2`.

## Runtime Evidence

- Environment list before change:
  - `base`
  - `tp2-car1-control`
- New environment created by clone:
  - `tp2`
- Validation inside the renamed environment with active X display:
  - `DISPLAY=:1 conda run -n tp2 python -c "import cv2, numpy, pynput; ..."`
  - observed:
    - `cv2 4.10.0`
    - `numpy 2.2.6`
    - `pynput` import succeeded
- Runtime bind validation:
  - `DISPLAY=:1 timeout 8s conda run -n tp2 python -u /home/tp2/servicios_tp2/prueba.py`
  - `ss -lunp` showed listener:
    - `172.16.0.1:20001`
- Old environment removed after validation:
  - `conda remove -y -n tp2-car1-control --all`
- Environment list after change:
  - `base`
  - `tp2`

## Result

- The EPC Conda environment for car 1 manual control is now named `tp2`.
- `prueba.py` still starts correctly from the renamed environment and binds to `172.16.0.1:20001`.
