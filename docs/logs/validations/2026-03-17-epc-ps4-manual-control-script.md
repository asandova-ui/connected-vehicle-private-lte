# EPC PS4 Manual Control Script

- Date: `2026-03-17`
- Machine: `tp2-EPC`

## Goal

Add a car1 manual-control script that preserves the current keyboard flow and also accepts a PS4 controller on the EPC.

## Runtime Evidence

- New script added to repo:
  - `servicios/prueba_ps4.py`
- Script deployed to current EPC runtime path:
  - `/home/tp2/TP2_red4G/servicios/prueba_ps4.py`
- Local syntax validation:
  - `python3 -m py_compile servicios/prueba_ps4.py`
- EPC syntax validation:
  - `python3 -m py_compile /home/tp2/TP2_red4G/servicios/prueba_ps4.py`
- EPC runtime imports validated inside Conda env `tp2`:
  - `evdev`
  - `cv2`
  - `numpy`
  - `pynput`
- Startup validation:
  - `DISPLAY=:1 timeout 6s conda run -n tp2 python -u /home/tp2/TP2_red4G/servicios/prueba_ps4.py`
  - `ss -lunp` showed listener:
    - `172.16.0.1:20001`

## Operational Notes

- The script auto-detects PS4-like devices from Linux `evdev` names (`Wireless Controller`, `DualShock`, `Sony`, `PS4`).
- Keyboard input remains available at the same time.
- PS4 control mapping:
  - left stick: steering
  - `R2`: forward
  - `L2`: reverse
  - `R1` / `L1`: forward/reverse boost
  - `X`: emergency neutral
- The EPC user `tp2` was observed without the `input` group during this task, so PS4 event access may require a one-time operator change:
  - `sudo usermod -aG input tp2`
  - then start a new login/session before running the script again
- No car-side configuration changes are required beyond the existing manual/cloud control path.

## Result

- `prueba_ps4.py` is ready on the EPC and preserves the current car1 manual control bind on `172.16.0.1:20001`.
- Keyboard control works through the existing EPC operator flow.
- PS4 support is implemented and should work once the controller is connected to the EPC and the operator account can read `/dev/input/event*`.
