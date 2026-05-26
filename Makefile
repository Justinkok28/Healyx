# Project Healyx — Makefile
# All operations go through here so Claude Code, CI, and humans all use the same commands.

.PHONY: help up down restart logs ps test lint format compile-rules \
        agent-redteam agent-triage docs-serve docs-build clean check-env

SHELL := /bin/bash

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

check-env: ## Verify .env exists
	@if [ ! -f .env ]; then \
	  echo "ERROR: .env not found. Copy .env.example to .env and fill it in."; \
	  exit 1; \
	fi

# ---------- Infrastructure ----------

up: check-env ## Start the full stack (docker compose up -d)
	cd infra && docker compose --env-file ../.env up -d

down: ## Stop the stack
	cd infra && docker compose down

restart: down up ## Restart everything

ps: ## Show running containers
	cd infra && docker compose ps

logs: check-env ## Tail logs for one service: make logs SERVICE=wazuh
	@if [ -z "$(SERVICE)" ]; then \
	  cd infra && docker compose logs -f --tail=200; \
	else \
	  cd infra && docker compose logs -f --tail=200 $(SERVICE); \
	fi

# ---------- Agents ----------

agent-redteam: check-env ## Run one red-team scenario: make agent-redteam SCENARIO=mfa_fatigue
	@if [ -z "$(SCENARIO)" ]; then \
	  echo "Usage: make agent-redteam SCENARIO=<scenario_name>"; \
	  echo "Available: mfa_fatigue helpdesk_password_reset oauth_consent_grant priv_role_burst sp_credential_addition port_scan_then_ssh_bf cloud_storage_exfil chatbot_prompt_injection"; \
	  exit 1; \
	fi
	cd agent && python -m redteam.main run --scenario $(SCENARIO)

agent-redteam-plan: check-env ## Let the LLM planner pick scenarios for a round
	cd agent && python -m redteam.main plan --rounds 3

agent-triage: check-env ## Start the triage agent webhook server (foreground)
	cd agent && uvicorn triage.main:app --host 0.0.0.0 --port 8001 --reload

agent-eval: check-env ## Run the A/B model comparison harness
	cd agent && python -m eval.score

# ---------- Detections ----------

compile-rules: ## Compile Sigma → Wazuh rule XML (and KQL for archive)
	python scripts/compile_sigma.py \
	  --in detections/sigma \
	  --out-wazuh detections/wazuh-rules/_generated \
	  --out-kql detections/kql/_generated

validate-sigma: ## Lint Sigma rules
	python scripts/validate_sigma.py detections/sigma

# ---------- Quality ----------

test: ## Run pytest across agent code
	cd agent && pytest -v

lint: ## Run ruff
	ruff check agent/ scripts/ chatbot/sage/
	ruff format --check agent/ scripts/ chatbot/sage/

format: ## Auto-format with ruff
	ruff format agent/ scripts/ chatbot/sage/
	ruff check --fix agent/ scripts/ chatbot/sage/

# ---------- Docs ----------

docs-serve: ## Preview docs site locally at http://localhost:8000
	mkdocs serve

docs-build: ## Build the docs site to ./site
	mkdocs build --strict

# ---------- Cleanup ----------

clean: ## Remove generated artifacts (keeps data volumes)
	rm -rf site/ build/ dist/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	rm -rf detections/wazuh-rules/_generated detections/kql/_generated
