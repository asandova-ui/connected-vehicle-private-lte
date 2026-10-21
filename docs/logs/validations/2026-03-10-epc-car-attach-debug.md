# EPC Car Attach Debug

- Date: `2026-03-10`
- Machine: `tp2-EPC` (with hop checks to `tp2-ENB`)

## Goal

Identify the current LTE UE IP of the car and diagnose attach failure.

## Runtime Evidence

- EPC reachable by Tailscale and `srsepc` running:
  - `srsepc` listening on `10.10.10.1:36412/SCTP`
  - `srsepc` listening on `10.10.10.1:2152/UDP`
- eNodeB reachable from EPC:
  - S1 association to EPC established from `10.10.10.2` to `10.10.10.1:36412`
  - `bladeRF` detected (`Nuand bladeRF 2.0 micro`)
  - two `srsenb` instances found running simultaneously (`pid 12340` and `pid 23086`)
- EPC attach logs (`/srv/tp2/logs/srsepc.log`) show:
  - `Attach request -- IMSI: 901650000052126`
  - repeated `UL NAS: Authentication Failure`
  - `Non-EPS authentication unacceptable`
- EPC UE interface state:
  - `srs_spgw_sgi` present with `172.16.0.1/24`
  - no UE neighbor entries on `srs_spgw_sgi`
  - no assigned UE address observed in logs

## Result

- Car IP could not be obtained because the UE attach does not complete.
- Current technical state is: radio signaling reaches EPC, but NAS authentication fails before PDN session/IP allocation.
- Additional risk: duplicate `srsenb` processes may cause unstable behavior and should be reduced to a single live instance.
