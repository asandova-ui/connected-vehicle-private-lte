# Car UE IP Assignment

- Date: `2026-03-10`
- Machine: `tp2-EPC`

## Goal

Confirm the LTE IP currently assigned to the car UE and pin it to a fixed address in EPC HSS configuration.

## Runtime Evidence

- `srsepc` log shows successful UE session for IMSI `901650000052126` with:
  - `IMSI: 901650000052126, UE IP: 172.16.0.2`
- EPC HSS DB (`/home/tp2/.config/srsran/user_db.csv`) before change:
  - IMSI `901650000052126` had `IP_alloc=dynamic`
- EPC HSS DB after change:
  - IMSI `901650000052126` set to `IP_alloc=172.16.0.2`
- Safety backup created before edit:
  - `/home/tp2/.config/srsran/user_db.csv.bak_static_ip_20260310_115235`

## Result

- Car UE is now explicitly mapped to `172.16.0.2` in the EPC user database.
- No service restart was forced during this check; the fixed mapping is persisted for subsequent attach cycles.
