# 2026-04-30 - Live tuning and retraining UI validation

## Scope

- Added runtime control tuning to `servicios/coche.py` for manual throttle, autonomous cruise/turn pulse values, steering trim, and lane-assist correction.
- Added host-local persistence for current control defaults through `POST /settings/defaults`.
- Improved `servicios/session_replayer.py` with MP4 playback, timeline/jump navigation, faster relabel controls, session metadata editing, safe session rename, and manifest-safe frame image rename.

## Local validation

Commands run from repo root:

```bash
python -m py_compile servicios/coche.py servicios/roboflow_runtime.py servicios/session_replayer.py servicios/autonomous_driver.py servicios/lane_detector.py
PYTHONPATH=servicios python -m unittest discover -s tests
node -e '...new Function(inline script from servicios/coche.py and servicios/session_replayer.py)...'
```

Result:

- `52` tests passed.
- No Python compile errors.
- Live and replayer inline JavaScript parsed successfully with Node.

Runtime smoke test:

- Started `servicios/coche.py` locally with:
  - `TP2_BIND_IP=127.0.0.1`
  - `TP2_BIND_PORT=23001`
  - `TP2_WEB_PORT=18088`
  - `TP2_ENABLE_INFERENCE=0`
  - `TP2_SESSION_RECORD_DIR=/tmp/tp2-session-record`
  - `TP2_CONTROL_DEFAULTS_PATH=/tmp/tp2-session-defaults.json`
- Sent one synthetic `I + pickle(jpeg)` UDP frame.
- Confirmed response packet type `C`.
- Confirmed `GET /status.json` reported:
  - `video.has_video=true`
  - `video.frames=1`
  - `udp.packets.I=1`
  - `settings.values` present
- Confirmed `POST /settings` updated `cruise_throttle=0.42`, `steering_trim=-0.30`, and `turn_pulse_enabled=false`.
- Confirmed `POST /settings/defaults` wrote `/tmp/tp2-session-defaults.json`.
- Confirmed `POST /replayer/start` opened the replayer on `18090`.
- Confirmed `GET /api/sessions` listed the recorded session.
- Confirmed `POST /api/session/meta` wrote review metadata.
- Confirmed `POST /api/frame/rename` renamed the selected frame image and updated `manifest.jsonl`.
- Confirmed `GET /video.mp4` with `Range: bytes=0-31` returned `32` bytes.

## EPC pre-deploy check

Read-only check before deployment:

- SSH to `tp2@100.97.19.112` succeeded with key-based auth.
- Hostname: `tp2-EPC`.
- `/home/tp2/TP2_red4G` was on `main...origin/main`.
- Existing unrelated EPC worktree state: `D servicios/test.jpg`.
- `tp2-srsepc.service` and `tp2-car-control.service` were inactive before the final pull/start validation.
- No `20001/UDP`, `8088/TCP`, or `8090/TCP` listener was present before starting the runtime services.

## EPC deployment validation

Deployment:

- Pushed `main` to GitHub at commit `71a5efd`.
- Ran `git pull --ff-only` in `/home/tp2/TP2_red4G`; EPC fast-forwarded from `34cdfaa` to `71a5efd`.
- Existing unrelated EPC state remained: `D servicios/test.jpg`.

Remote checks on EPC:

```bash
python -m py_compile servicios/coche.py servicios/roboflow_runtime.py servicios/session_replayer.py servicios/autonomous_driver.py servicios/lane_detector.py
PYTHONPATH=servicios python -m unittest discover -s tests
curl -fsS http://127.0.0.1:8088/healthz
curl -fsS http://127.0.0.1:8088/settings.json
curl -fsS -X POST -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:8088/replayer/start
```

Result:

- EPC Python compile passed in conda env `tp2`.
- EPC test suite passed: `52` tests.
- EPC did not have `node` installed, so JS syntax was validated locally only.
- Started `tp2-srsepc.service` and `tp2-car-control.service`; both reported `active`.
- `ss` showed:
  - `172.16.0.1:20001/UDP`
  - `0.0.0.0:8088/TCP`
  - `0.0.0.0:8090/TCP`
- `GET /healthz` returned `{"ok":true}`.
- `GET /settings.json` returned `settings.values` with `28` runtime controls including steering trim, cruise throttle, turn pulse, lane assist, and turn compensation.
- Sent one synthetic `I + pickle(jpeg)` UDP frame on EPC loopback and received response packet type `C`.
- `GET /status.json` after the frame reported:
  - `udp.packets.I=1`
  - `udp.tx_packets=61`
  - `video.has_video=true`
  - `video.frames=1`
  - `control.mode=manual`
  - `replayer.active=true`
- `GET /api/sessions` on port `8090` returned the existing session `20260430-111803` with `444` frames and `has_video=true`.
