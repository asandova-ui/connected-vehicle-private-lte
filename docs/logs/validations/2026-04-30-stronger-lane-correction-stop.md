# 2026-04-30 - Stronger lane correction and immediate STOP

## Scope

- Increased rightward physical trim to `TP2_STEERING_TRIM=-0.24`.
- Increased lane assist authority to `TP2_LANE_MAX_CORRECTION=0.75`.
- Preferred the right corridor when several tape corridors are visible, to recover if the car drifts into the opposite lane.
- Reduced recovery throttle to `0.35`.
- STOP detections now stop immediately instead of using `approach-stop`.
- Lane assist still does not compete with open turn maneuvers.
- No firmware changes.

## Validation

- Local real-frame replay from EPC captures:
  - sampled frames stayed detected as `partial-edge-lane-pair`
  - lane corrections were `-0.118` to `-0.137`
  - neutral-forward effective steering with trim and lane correction was about `-0.11` to `-0.13`
- Local MacBook:
  - `PYTHONPATH=servicios python -m compileall -q servicios tests`
  - `PYTHONPATH=servicios python -m unittest discover -s tests`
  - Result: 41 tests OK.
