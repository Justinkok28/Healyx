# Project Healyx (OSS Edition)

> A self-improving purple-team SOC lab on Oracle Cloud Free Tier, built entirely with open source tooling.

## The feedback loop

```mermaid
flowchart LR
    subgraph RED[Red side]
        Planner[LLM Planner<br/>Hermes 3 70B]
        Scenarios[8 UNC3944 scenarios]
        Planner --> Scenarios
    end

    subgraph LAB[Halcyon Care lab]
        Keycloak[Keycloak IdP]
        Sage[Sage chatbot]
        VM[Oracle VM]
    end

    subgraph BLUE[Blue side]
        Wazuh[Wazuh SIEM]
        Sigma[Sigma rules<br/>→ Wazuh XML]
        Triage[Triage Agent<br/>Hermes 3 70B]
    end

    subgraph TUNE[Tuning]
        Patch[Rule tuning]
    end

    Scenarios -.attacks.-> Keycloak
    Scenarios -.attacks.-> Sage
    Scenarios -.attacks.-> VM
    Keycloak --> Wazuh
    Sage --> Wazuh
    VM --> Wazuh
    Wazuh -- alerts --> Triage
    Sigma -- compiled rules --> Wazuh
    Triage -- suggested tuning --> Patch
    Patch -- updated detections --> Sigma
    Patch -. informs next round .-> Planner
```

## What this is

A solo portfolio project modeling **Halcyon Care Pte Ltd**, a fictional 25-person Singaporean healthcare-SaaS. Red attacks, blue detects, the triage agent proposes detection tuning, the rules sharpen, and the red side adapts.

## The stack at a glance

- **Host:** Oracle Cloud Always Free ARM VM
- **SIEM:** Wazuh
- **Identity:** Keycloak
- **Observability:** Grafana + Loki
- **Detections:** Sigma → Wazuh XML
- **LLM API:** OpenRouter, default Nous Hermes 3 70B
- **Targets:** Sage (vulnerable chatbot) + the lab VM itself

## Where to start

- New to the project? Read [Architecture](architecture.md) and [Scope](scope.md).
- Starting a build session? Open the [weekly playbook](weeks/week-01-bootstrap.md) for the week you're on.
- Migrating from the Azure version? See the [pivot guide](https://github.com/justinkok28/Healyx/blob/main/PIVOT_FROM_AZURE.md) in the repo root.
