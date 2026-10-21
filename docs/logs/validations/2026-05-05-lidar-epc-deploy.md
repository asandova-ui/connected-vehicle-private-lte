# LiDAR EPC Deployment

## Scope

- Target machine: `tp2-EPC`
- Repo path: `/home/tp2/TP2_red4G`
- Deployed commit: `9515db8 Add LiDAR safety and live web view`
- No LTE service was started.
- `tp2-car-control.service` was inactive before and after the deployment.
- No firmware was touched.

## Deployment

Read-only inspection first:

```text
hostname -> tp2-EPC
git status --short --branch -> ## main...origin/main, with existing local deletion: D servicios/test.jpg
systemctl is-active tp2-car-control.service -> inactive
```

The existing local deletion of `servicios/test.jpg` was not reverted.

Deployment command:

```text
cd /home/tp2/TP2_red4G
git pull --ff-only origin main
```

Result:

```text
Updating 4124c63..9515db8
Fast-forward
```

## Validation

Remote compile check in the EPC `tp2` Conda environment:

```text
/home/tp2/miniforge3/bin/conda run --no-capture-output -n tp2 python -m py_compile servicios/lidar_processor.py servicios/coche.py
```

Result: success, no output.

Temporary localhost smoke check, with inference disabled and non-production bind:

```text
TP2_BIND_IP=127.0.0.1 TP2_BIND_PORT=23001 TP2_WEB_HOST=127.0.0.1 TP2_WEB_PORT=18088 TP2_ENABLE_INFERENCE=0 TP2_SESSION_RECORD_AUTOSTART=0 \
  /home/tp2/miniforge3/bin/conda run --no-capture-output -n tp2 python servicios/coche.py

curl -fsS http://127.0.0.1:18088/healthz
curl -fsS http://127.0.0.1:18088/status.json
```

Result:

```text
{"ok":true}
{'ok': True, 'lidar': 'searching', 'mode': 'manual'}
```

The temporary smoke process was stopped after validation. `tp2-car-control.service` remained inactive.

## Remaining Real-Lab Validation

- Start a real session with `ops/bin/tp2-up`.
- Confirm the car sends actual LiDAR packets as `L` or LiDAR-bearing `D`.
- Confirm `/status.json` reports `lidar.frames > 0`.
- Confirm the web LiDAR reconstruction from `http://100.97.19.112:8088/`.
- Validate `lidar-stop` and `lidar-slow` with a controlled obstacle before autonomous free-driving.
