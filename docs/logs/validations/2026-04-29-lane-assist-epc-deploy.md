# 2026-04-29 - Lane assist deployed on EPC car runtime

## Scope

- Added `servicios/lane_detector.py`.
- Integrated lane guidance into `servicios/coche.py` autonomous forward actions.
- Kept EPC as the only control/orchestration host.
- No firmware changes.

## Validation

- Local MacBook:
  - `PYTHONPATH=servicios conda run -n vidimu python -m compileall -q servicios tests`
  - `PYTHONPATH=servicios conda run -n vidimu python -m unittest discover -s tests`
  - Result: 36 tests OK.
- EPC `/home/tp2/TP2_red4G`:
  - `PYTHONPATH=servicios conda run --no-capture-output -n tp2 python -m compileall -q servicios tests`
  - `PYTHONPATH=servicios conda run --no-capture-output -n tp2 python -m unittest discover -s tests`
  - Result: 36 tests OK.
- EPC service:
  - `tp2-car-control.service` restarted successfully.
  - `172.16.0.1:20001/UDP` listening.
  - `0.0.0.0:8088/TCP` listening.
  - `/status.json` reports `lane.enabled=true`, `lane.status=searching`, `lane.config.max_correction=0.24`.
- Synthetic UDP frame test on EPC:
  - Sent one JPEG frame with two cyan tape lines to `172.16.0.1:20001`.
  - Runtime replied with control packet `C`, steering `0.17`, throttle `0.0` while in manual neutral.
  - `/status.json` reported `lane.status=tracking`, `lane.usable=true`, `lane.guidance.source=pair`, `lane.guidance.correction=-0.051`.
  - Service was restarted after this test to clear the synthetic frame from the operator view.

## Live-car limitation

After deployment and one non-retained `AM-Cloud` MQTT publish, no new real car UDP frames arrived before this evidence file was written. The EPC service is deployed and validated with synthetic runtime input, but the real end-to-end car trajectory correction still needs a live session with the car streaming camera frames.
