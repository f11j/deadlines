ifndef VERBOSE
    MAKEFLAGS += --no-print-directory
endif

SHELL = /bin/bash

# Terminal output
GREEN := "\e[32m"
YELLOW := "\e[1;33m"
RED := "\e[1;31m"
NC := "\e[0m"
INFO := @bash -c 'printf $(YELLOW); echo "$$1"; printf $(NC)' MESSAGE
SUCCESS := @bash -c 'printf $(GREEN); echo "  $$1"; printf $(NC)' MESSAGE
ERROR := bash -c 'printf $(RED); echo "$$1"; printf $(NC)' MESSAGE

# Comand line arguments for rule (make <rule> [args])
ARGS := $(filter-out --,$(filter-out $(firstword $(MAKECMDGOALS)),$(MAKECMDGOALS)))
FIRST_ARG := $(word 1, $(ARGS))
SECOND_ARG := $(word 2, $(ARGS))

.DEFAULT_GOAL := help

.PHONY: help
help: ## Print comments starting with double slash
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} \
	/^[$$()% a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } \
	/^##/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

.PHONY: aptget
aptget: ## Install Linux requirements
	@sed 's/\#.*//' "$$PROJECT_DIR"/requirements/x86_64/*.list


-include [Mm]akefile.local*
-include .config/[Mm]akefile.local*