# A connected vehicle on a private LTE network

A small car as user equipment on a 4G network built from scratch with software radio, traffic-sign detection with a model trained for it, driving decisions taken in the network core, and a plan to deploy the same service on 104 km of motorway: radio planning, traffic forecast, cost and licensing.

Taller de Proyectos 2, Master's in Telecommunications Engineering, University of Valladolid, 2025–2026. With Mario Medrano and Luis F. Sánchez. Project site: [asandova-ui.github.io/connected-vehicle-private-lte](https://asandova-ui.github.io/connected-vehicle-private-lte/).

<p align="center">
  <img src="docs/assets/readme/demo.webp" width="640" alt="The demonstration">
</p>

## Network

srsRAN 4G end to end. The EPC (MME, HSS, SPGW) runs on one machine at 10.10.10.1 and hands UEs addresses in 172.16.0.0/24; the eNodeB runs `srsenb` on a bladeRF 2.0 xA9 on a second machine, band 7, 10 MHz FDD, MIMO 2×2 TM4, S1-MME over SCTP and GTP-U over UDP to the core. The car attaches as a UE through an LTE modem. Measured from the UE with `ping` and `iperf3`: 38 ms mean ICMP latency, 15.0 Mbit/s up and 23.5 Mbit/s down over TCP, a 5 Mbit/s UDP stream with 0 % loss and 4.7 ms jitter.

## Vision

A traffic-sign detector trained on a dataset built for the project, 4,985 images and 10,962 annotations of the signs on the test track, 300 epochs on a YOLO backbone: mAP@50 95.5 %, precision 94.0 %, recall 91.6 %. Served behind a Roboflow-compatible inference endpoint on a Jetson Orin Nano, with a local fallback on the EPC. Sessions are recorded as annotated video plus a frame manifest so hard cases can be relabelled and the model retrained without touching the control path.

## Control

Everything that decides lives in the core, not in the car. `servicios/coche.py` receives camera frames, battery, IMU and LiDAR over UDP and answers with a compact steering/throttle packet.

- A deterministic state machine turns detections into actions: 90° turns on confirmed signs with an area and persistence threshold, speed-limit signs set a throttle ramp for three seconds, STOP holds neutral for five, stale frames or predictions fall back to neutral.
- OpenCV lane assistance on the taped track corrects steering, only on forward autonomous actions.
- A bounded PID on the throttle from BMI160 IMU speed estimates.
- LiDAR safety on a 45-beam front sector: stop under 0.15 m, throttle limited to 0.85 m, steering correction to 1.35 m. It overrides the camera; a stale LiDAR does not.
- A browser console for live video, manual and autonomous modes, hot tuning of cruise throttle, trim, lane gain and LiDAR sectors, and session recording.

`ops/` brings the four machines up and down with systemd units and validation scripts; `tests/` covers the decisions, lane detection, LiDAR processing and runtime behaviour.

## Deployment on the A-601

The second half of the work takes the service to the Valladolid–Segovia motorway, km 0 to 104, on 10 MHz of band 7 ceded by Vodafone under an academic contract (2540–2550 / 2660–2670 MHz).

- **Traffic**: IMD series 2010–2024 from the nine Ministry counting stations on the stretch, projected to 2026 with a weighted least-squares fit (pandemic years at weight 0.3), aggregated by sub-section length. About 11,000 vehicles a day on the corridor.
- **Radio planning**: COST-231 Hata with a rural correction fitted to the corridor, 25 sites (20 co-located on existing masts, 5 new), 50 sectors, simulated in Xirio-Online. 92.2 % of the served area above RSRP −110 dBm, mean sector RSRP −96.9 dBm, 44 of 50 sectors effective over the carriageway.
- **Cost**: CAPEX (civil works, radio equipment, engineering, permits), recurring OPEX (co-location, power, maintenance) and the first-year total.
- **Licensing**: Ley 11/2022, RD 123/2017, RD 1066/2001 on exposure limits, the procedure before SETID and registration with the CNMC.

Data and dashboards are in `docs/`.

<p align="center">
  <img src="docs/assets/readme/site-traffic-a601.png" width="395" alt="A-601 traffic" hspace="4">
  <img src="docs/assets/readme/site-coverage-a601.png" width="395" alt="A-601 coverage" hspace="4">
</p>

## Layout

```
servicios/     runtime: car control, inference client, autonomous policy, lane and LiDAR logic, replayer
ops/           bring-up, shutdown, validation, systemd units
docs/          architecture, runbooks per machine, network contract, inference notes, the site and the A-601 data
docs/logs/     validation evidence
tests/         unit tests
SoftARTEMIS/   vehicle-side files
```

```bash
PYTHONPATH=servicios python -m unittest discover -s tests
```

Python, NumPy, OpenCV; srsRAN 4G on bladeRF; Roboflow Inference on a Jetson Orin Nano; Xirio-Online for the radio study; systemd, Bash and SSH for the lab. The lab is physical, so there is no one-command demo.
