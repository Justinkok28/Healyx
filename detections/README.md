# Detections

Sigma is the source of truth. Wazuh rule XML in `wazuh-rules/_generated/` is compiled output — never hand-edited.

## Workflow

1. Author a rule in `sigma/healyx-<topic>-v<N>.yml`
2. Run `make compile-rules` to generate the Wazuh XML
3. Commit BOTH the Sigma source and the compiled output
4. Mount `detections/wazuh-rules/` into the manager (already wired in `docker-compose.yml`)
5. Restart manager: `docker compose restart wazuh-manager`

## Naming convention

`healyx-<surface>-<short-name>-v<N>.yml`

- surface: keycloak / host / network / sage / wazuh
- short-name: hyphenated description
- v<N>: bump on breaking changes

## Coverage matrix

See `docs/scope.md` for the planned MITRE coverage matrix. Update as rules are added.
