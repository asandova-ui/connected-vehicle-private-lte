# eNodeB MIMO 2x2 Configuration

## Scope

- Machine: `tp2-ENB`
- Target file: `/home/tp2/.config/srsran/enb.conf`
- Requested change: configure the eNodeB for 2x2 MIMO after adding two antennas to the `bladeRF`.

## Change

Created a timestamped backup on the eNodeB:

```text
/home/tp2/.config/srsran/enb.conf.bak_mimo2x2_20260430_092210
```

Updated the active eNodeB config:

```ini
tm = 4
nof_ports = 2
```

The resulting diff against the backup only changed the prepared MIMO lines:

```diff
-#tm = 4
-#nof_ports = 2
+tm = 4
+nof_ports = 2
```

## Validation

- Access path:
  - MacBook to EPC: `ssh tp2@100.97.19.112 hostname` returned `tp2-EPC`.
  - EPC to eNodeB: `ssh tp2@10.10.10.2 hostname` returned `tp2-ENB`.
- Config check:
  - `grep -nE '^(tm|nof_ports) *=' /home/tp2/.config/srsran/enb.conf` returned:
    - `31:tm = 4`
    - `32:nof_ports = 2`
  - `srsenb --help` on the eNodeB confirmed supported config keys `--enb.tm` and `--enb.nof_ports`.
- Hardware check:
  - `bladeRF-cli -p` detected `Nuand bladeRF 2.0`.
- Process check:
  - `tp2-srsenb.service` was `inactive`.
  - No live `srsenb` process was present.
  - `tp2-srsepc.service` on EPC was also `inactive`.
- Reachability check:
  - EPC ping to `10.10.10.2` succeeded with `0%` packet loss.

## Notes

No radio service was started or restarted during this change because both LTE services were inactive. The new MIMO profile will be used on the next `srsenb` start. Full LTE validation still requires starting `srsepc`, starting `srsenb`, verifying S1, and confirming UE attach.
