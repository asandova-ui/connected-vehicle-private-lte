# EPC Car Control And Jetson Inference Integration

## Date

- `2026-03-17`

## Scope

- unify car1 manual control into a new EPC runtime script
- keep control ownership on EPC
- wire live Roboflow inference through the same config contract used by the existing inference tools
- prepare the final path where inference is offloaded to Jetson without moving orchestration away from EPC

## Repo Changes

- added `servicios/coche.py`
  - manual car1 control on `172.16.0.1:20001`
  - keyboard + PS4 input
  - live Roboflow inference overlay on incoming camera frames
- added `servicios/roboflow_runtime.py`
  - shared inference config/client helpers reused by live control and offline tools
- changed `servicios/prueba_ps4.py`
  - now acts as compatibility wrapper to `coche.py`
- changed `servicios/inferencia.py`
  - now reuses the shared Roboflow runtime helpers
- changed `servicios/inferencia_gui_web.py`
  - now reuses the shared Roboflow runtime helpers
- changed `servicios/environment-tp2.yml`
  - declared `gradio` and `inference-sdk` in the `tp2` environment definition

## EPC Validation

- local syntax:
  - `python3 -m py_compile servicios/coche.py servicios/prueba_ps4.py servicios/roboflow_runtime.py servicios/inferencia.py servicios/inferencia_gui_web.py`
  - result: OK
- deployed updated scripts to EPC:
  - `/home/tp2/TP2_red4G/servicios/`
- validated the `tp2` conda env on EPC with `PYTHONNOUSERSITE=1`
  - `gradio` import: OK
  - `InferenceHTTPClient` import from `inference_sdk`: OK
  - `requests`, `aiohttp`, `supervision`: OK
- remote syntax on EPC:
  - `PYTHONNOUSERSITE=1 /home/tp2/miniforge3/envs/tp2/bin/python -m py_compile coche.py prueba_ps4.py roboflow_runtime.py inferencia.py inferencia_gui_web.py`
  - result: `EPC_PYCOMPILE_OK`
- runtime bind check on EPC:
  - launched `coche.py` with `DISPLAY=:1`
  - configured inference endpoint for Jetson path:
    - `TP2_INFERENCE_MODE=local`
    - `TP2_INFERENCE_TARGET=model`
    - `ROBOFLOW_LOCAL_API_URL=http://192.168.72.127:9001`
  - observed startup output:
    - `Manual control server listening on 172.16.0.1:20001`
    - `Inference: enabled (local/model) endpoint=http://192.168.72.127:9001`
    - PS4 controller detected on EPC input stack
  - `ss -lunp` confirmed:
    - `172.16.0.1:20001` listening with the new script

## Jetson Validation

- checked from EPC:
  - `curl http://192.168.72.127:9001/openapi.json`
  - result: timeout
- checked from EPC over Jetson Tailscale:
  - `curl http://100.115.99.8:9001/openapi.json`
  - result: connection refused
- checked directly on Jetson:
  - `curl http://127.0.0.1:9001/openapi.json`
  - result: connection refused
  - `systemctl status tp2-roboflow-inference.service`
  - result: unit not found
  - `docker ps`
  - result: no container exposing `9001`

## Current Operational Conclusion

- EPC side is ready for the final architecture:
  - car control remains on EPC
  - MQTT/Mosquitto path remains unchanged
  - live manual control can call a Roboflow-compatible inference endpoint by configuration
- Jetson inference is not yet live:
  - no active service on port `9001`
  - no repo checkout found on Jetson
  - no `inference` Python runtime found on Jetson
  - no `ROBOFLOW_API_KEY` set in the checked shell environment on Jetson

## Blocker For End-To-End Jetson Inference

The new EPC runtime is ready to call Jetson, but the Jetson still needs its Roboflow inference service started and configured with the user model/API key before frame inference can succeed end-to-end.
