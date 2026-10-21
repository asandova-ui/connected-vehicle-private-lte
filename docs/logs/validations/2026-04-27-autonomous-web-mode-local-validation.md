# 2026-04-27 - Autonomous Web Mode Local Validation

## Scope

Add EPC-owned autonomous driving to the existing `coche.py` web runtime without moving orchestration to Jetson or the car.

Changed files:

- `servicios/autonomous_driver.py`
- `servicios/coche.py`
- `tests/test_autonomous_driver.py`
- operating docs that describe the web runtime and EPC control contract

## Remote Read-Only Baseline

The live EPC runtime was checked before deployment-impacting work.

- `GET http://100.97.19.112:8088/status.json` responded successfully.
- UDP bind reported by status: `172.16.0.1:20001`.
- Web listener reported by SSH: `0.0.0.0:8088`.
- Active process: `python3 coche.py`.
- `tp2-car-control.service` was `inactive`, matching the current manual process state.
- Live status showed camera frames arriving (`I` packets) and Jetson-backed inference configured at `http://100.115.99.8:9001`.

No live service restart was performed during this validation.

## Local Checks

Compile:

```bash
python3 -m py_compile servicios/autonomous_driver.py servicios/coche.py servicios/roboflow_runtime.py
```

Result: OK.

Autonomous policy tests:

```bash
PYTHONPATH=servicios python3 -m unittest tests/test_autonomous_driver.py
```

Result: `Ran 6 tests ... OK`.

Local runtime smoke test:

```bash
TP2_BIND_IP=127.0.0.1 TP2_BIND_PORT=29001 TP2_WEB_HOST=127.0.0.1 TP2_WEB_PORT=18088 TP2_ENABLE_INFERENCE=0 /Users/mario/miniconda3/envs/test/bin/python -u servicios/coche.py
```

Then a fake `I` packet was sent to `127.0.0.1:29001` and the web API was exercised:

- `POST /control` accepted manual steering/throttle and returned `mode=manual`.
- `POST /mode` accepted `autonomous`.
- `GET /status.json` returned `control.mode=autonomous`, `video.has_video=true`, and `udp.packets={"I": 2}`.
- With inference disabled in this smoke test, autonomous mode correctly reported `safe-neutral`.

## Result

The new autonomous layer is implemented and locally validated. It remains EPC-owned, uses the existing Roboflow prediction stream, exposes the web toggle, and falls back to neutral when detections cannot be trusted.

Live activation still requires deploying the updated files to EPC and restarting the active `python3 coche.py` process or replacing it with the systemd unit in a controlled window.
