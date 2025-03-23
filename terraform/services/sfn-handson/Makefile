SHELL := /usr/bin/env bash
# .SHELLFLAGS := -o verbose -o xtrace -o errexit -o nounset -o pipefail -o posix -c
.SHELLFLAGS := -o errexit -o nounset -o pipefail -o posix -c
.DEFAULT_GOAL := help

# all targets are phony
.PHONY: $(grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | sed 's/://')

help:  ## print this help
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Get the service name from the current directory
SERVICE_NAME := $(shell basename $(shell pwd))
ENV ?= dev
TERRAFORM_DIR := $(ENV)
TF_OPT ?=

init:
	@echo "Initializing Terraform in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) init $(TF_OPT)

fmt:
	@echo "Formatting Terraform files in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) fmt -recursive

validate: fmt
	@echo "Validating Terraform configuration in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) validate

plan: init validate
	@echo "Planning Terraform in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) plan -no-color -out=.terraform.plan.$(ENV).tfplan $(TF_OPT)

apply: plan
	@echo "Applying Terraform in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) apply .terraform.plan.$(ENV).tfplan -auto-approve $(TF_OPT)

destroy: init
	@echo "Destroying Terraform resources in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) destroy -auto-approve $(TF_OPT)

dev-plan:  ## [dev] plan
	@$(MAKE) plan ENV=dev TF_OPT="$(TF_OPT)"

dev-apply:  ## [dev] apply
	@$(MAKE) apply ENV=dev TF_OPT="$(TF_OPT)"

dev-destroy:  ## [dev] destroy
	@$(MAKE) destroy ENV=dev TF_OPT="$(TF_OPT)"

prod-plan:  ## [prod] plan
	@$(MAKE) plan ENV=prod TF_OPT="$(TF_OPT)"

prod-apply:  ## [prod] apply
	@$(MAKE) apply ENV=prod TF_OPT="$(TF_OPT)"

prod-destroy:  ## [prod] destroy
	@$(MAKE) destroy ENV=prod TF_OPT="$(TF_OPT)"
