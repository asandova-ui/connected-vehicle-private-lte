# EPC To eNodeB SSH Hop Validation

- Date: `2026-03-04`
- Scope: operator access path between `tp2-EPC` and `tp2-ENB`

## Applied Change

- Generated an `ed25519` SSH key for `tp2` on the EPC because no private key existed previously
- Installed that public key into the `tp2` account on the eNodeB

## Validation

- Tailscale SSH to the EPC succeeds with `ssh tp2@100.97.19.112`
- Direct backhaul SSH from the EPC succeeds with `ssh tp2@10.10.10.2`
- The eNodeB hostname reported over the validated hop is `tp2-ENB`

## Operational Result

Future sessions can reach the eNodeB through the EPC with the standard two-step operator path and should not need to re-enter a password for the `tp2` to `tp2` hop.
