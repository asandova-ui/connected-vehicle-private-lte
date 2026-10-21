# 2026-04-28 - Manual/autonomous mode guard

## Scope

Fix `servicios/coche.py` so manual browser control does not arm or move the car while idle, and so stale/manual browser events cannot switch an active autonomous session back to manual.

## Local validation

- `python -m py_compile servicios/autonomous_driver.py servicios/coche.py servicios/roboflow_runtime.py`
- `PYTHONPATH=servicios python -m unittest tests/test_autonomous_driver.py tests/test_coche_runtime.py`
  - result: 14 tests passed
- Local HTTP smoke with `TP2_ENABLE_INFERENCE=0`:
  - neutral `POST /control` in manual returned `armed=false`, `source=neutral`
  - after `POST /mode autonomous`, stale `POST /control` returned `mode=autonomous`
  - `POST /control/neutral` preserved `mode=autonomous`
  - `POST /control/stop` returned `mode=manual`, `source=stop`
- Served UI JavaScript was extracted from `/` and checked with `node --check`.

## Operational note

`/control/neutral` is now manual-control release. It does not leave autonomous mode. The explicit operator stop path is `/control/stop`, used by the web Stop button.

## EPC deployment validation

- EPC repo fast-forwarded to `13faf4a`.
- EPC validation passed:
  - `python3 -m py_compile servicios/autonomous_driver.py servicios/coche.py servicios/roboflow_runtime.py`
  - `PYTHONPATH=servicios python3 -m unittest tests/test_autonomous_driver.py tests/test_coche_runtime.py`
  - result: 14 tests passed
- `tp2-car-control.service` was relaunched because the previous Python process was still serving the old code.
  - new `MainPID`: `51171`
  - live ports active: `172.16.0.1:20001/UDP`, `0.0.0.0:8088/TCP`
  - `GET /healthz`: `{"ok": true}`
- Live status after deployment:
  - `mode=autonomous`
  - `source=autonomous-safe`
  - `armed=false`
  - `steering=0.25`
  - `throttle=0.0`
