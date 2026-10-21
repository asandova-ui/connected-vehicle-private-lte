# Test And Validation Reference

## Layered Validation Order

1. LTE
2. UE connectivity
3. EPC application services
4. Jetson inference
5. MQTT control path
6. Car-agent behavior
7. End-to-end flow

## Minimum Checks Per Layer

## LTE

- EPC process running
- eNodeB process running
- S1 setup established

## UE Connectivity

- UE attached
- UE received IP
- UE can reach the EPC service address

## EPC Application

- backend health endpoint responds
- DB connection succeeds
- MQTT pub/sub succeeds

## Jetson

- health endpoint responds
- known-image inference succeeds

## Car

- frame upload succeeds
- command reception succeeds
- watchdog fallback verified

## End-To-End

- frame upload
- inference response
- action publish
- action reception
- movement execution
- acknowledgement

## Evidence

For meaningful work, record:

- what changed
- what was tested
- whether the result was successful
- any remaining blockers

