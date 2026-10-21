# EPC Manual Control LTE Bind

- Date: `2026-03-12`
- Machine: `tp2-EPC`

## Goal

Add a manual control script variant that binds to the EPC LTE-side address `172.16.0.1` without modifying the original legacy scripts.

## Runtime Evidence

- EPC UE-side interface confirmed during this task:
  - `srs_spgw_sgi` present with `172.16.0.1/24`
- New script added to repo:
  - `servicios/car1_manual_control_server_epc_lte.py`
- New script deployed to EPC runtime path:
  - `/home/tp2/servicios_tp2/car1_manual_control_server_epc_lte.py`
- Syntax validation completed:
  - local: `python3 -m py_compile servicios/car1_manual_control_server_epc_lte.py`
  - EPC: `python3 -m py_compile /home/tp2/servicios_tp2/car1_manual_control_server_epc_lte.py`
- Port occupancy check on EPC before run:
  - no active listener found on `20001/UDP` or `20003/UDP` at validation time

## Result

- A dedicated LTE/EPC manual-control script is now available with default bind `172.16.0.1:20001`.
- Original scripts remain unchanged for rollback safety.
- No live car movement test was executed in this task, so end-to-end motion remains pending operator run.
