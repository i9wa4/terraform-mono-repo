# MAKEFLAGS += --warn-undefined-variables
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


# --- Configuration ---
# These are base paths and default values.
# Dedicated targets will often override ENV and LAMBDA.
ENV ?= dev
LAMBDA ?= hello-world # Default lambda name for targets like lambda-build-push if not specified
LAMBDAS_BASE_DIR := lambdas
COMMON_DIR := terraform
ENVIRONMENTS_BASE_DIR := environments

# Docker image details
ECR_REGISTRY ?= YOUR_AWS_ACCOUNT_ID.dkr.ecr.YOUR_AWS_REGION.amazonaws.com # MUST BE SET for lambda-build-push
IMAGE_TAG ?= $(shell git rev-parse --short HEAD)
# LAMBDA_IMAGE_URI is typically passed to lambda apply targets, or constructed.
# For 'make lambda-build-push', it's constructed using ECR_REGISTRY, LAMBDA, IMAGE_TAG.
DEFAULT_LAMBDA_IMAGE_URI := $(ECR_REGISTRY)/$(LAMBDA):$(IMAGE_TAG)

# AWS Region - ensure this is set in your environment or AWS config
AWS_REGION ?= ap-northeast-1


# --- Lambda Specific Docker Targets ---
# Example: make lambda-build-push LAMBDA=my-lambda
lambda-ecr-login: ## Log in to AWS ECR (uses ECR_REGISTRY, AWS_REGION)
	@echo "Logging in to ECR registry $(ECR_REGISTRY) in region $(AWS_REGION)"
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

lambda-build-push: lambda-ecr-login ## Build and push Docker image for a lambda to ECR. Vars: LAMBDA, ECR_REGISTRY, IMAGE_TAG
	$(eval CURRENT_LAMBDA_APP_DIR := $(LAMBDAS_BASE_DIR)/$(LAMBDA)/app)
	$(eval CURRENT_LAMBDA_IMAGE_URI := $(ECR_REGISTRY)/$(LAMBDA):$(IMAGE_TAG))
	@echo "Building and pushing Docker image for lambda: $(LAMBDA) from $(CURRENT_LAMBDA_APP_DIR)"
	@echo "Image: $(CURRENT_LAMBDA_IMAGE_URI)"
	@if [ ! -d "$(CURRENT_LAMBDA_APP_DIR)" ]; then echo "Error: Lambda app directory '$(CURRENT_LAMBDA_APP_DIR)' does not exist. Create it with a Dockerfile."; exit 1; fi
	docker build -t $(CURRENT_LAMBDA_IMAGE_URI) $(CURRENT_LAMBDA_APP_DIR) --platform=linux/arm64 --provenance=false
	docker push $(CURRENT_LAMBDA_IMAGE_URI)

# --- Generic (Internal) Terraform Targets ---
# These targets expect TARGET_TF_DIR and TF_CMD_ARGS to be set by the calling dedicated target.
init: ## [Internal] Initialize Terraform for the active component and environment
	@echo "==> Initializing Terraform in $(TARGET_TF_DIR) for S3 key: hands-on-lambda-ecr/$(TARGET_TF_DIR)/terraform.tfstate"
	terraform -chdir=$(TARGET_TF_DIR) init -backend-config="key=hands-on-lambda-ecr/$(TARGET_TF_DIR)/terraform.tfstate"

validate: ## [Internal] Validate Terraform configuration for the active component
	@echo "==> Validating Terraform in $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) validate

plan: init ## [Internal] Create a Terraform execution plan for the active component
	@echo "==> Planning changes in $(TARGET_TF_DIR) with args: $(TF_CMD_ARGS)"
	terraform -chdir=$(TARGET_TF_DIR) plan $(TF_CMD_ARGS)

apply: init ## [Internal] Apply Terraform changes for the active component (prompts for approval)
	@echo "==> Applying changes in $(TARGET_TF_DIR) with args: $(TF_CMD_ARGS)"
	terraform -chdir=$(TARGET_TF_DIR) apply $(TF_CMD_ARGS)

apply-auto: init ## [Internal] Apply Terraform changes for the active component (auto-approves)
	@echo "==> Applying changes (auto-approve) in $(TARGET_TF_DIR) with args: $(TF_CMD_ARGS)"
	terraform -chdir=$(TARGET_TF_DIR) apply -auto-approve $(TF_CMD_ARGS)

destroy: init ## [Internal] Destroy Terraform-managed resources for the active component (prompts for approval)
	@echo "==> Destroying resources in $(TARGET_TF_DIR) with args: $(TF_CMD_ARGS)"
	terraform -chdir=$(TARGET_TF_DIR) destroy $(TF_CMD_ARGS)

destroy-auto: init ## [Internal] Destroy Terraform-managed resources for the active component (auto-approves)
	@echo "==> Destroying resources (auto-approve) in $(TARGET_TF_DIR) with args: $(TF_CMD_ARGS)"
	terraform -chdir=$(TARGET_TF_DIR) destroy -auto-approve $(TF_CMD_ARGS)

# --- Dedicated Targets for 'dev' environment ---

# Dev - Common Resources
DEV_COMMON_TF_DIR := $(COMMON_DIR)
DEV_COMMON_TF_CMD_ARGS := -var-file=../$(ENVIRONMENTS_BASE_DIR)/dev/terraform.tfvars

dev-common-init: ## [dev common] Initialize Terraform
	@$(MAKE) init TARGET_TF_DIR=$(DEV_COMMON_TF_DIR)
dev-common-validate: ## [dev common] Validate Terraform
	@$(MAKE) validate TARGET_TF_DIR=$(DEV_COMMON_TF_DIR)
dev-common-plan: ## [dev common] Plan Terraform
	@$(MAKE) plan TARGET_TF_DIR=$(DEV_COMMON_TF_DIR) TF_CMD_ARGS="$(DEV_COMMON_TF_CMD_ARGS)"
dev-common-apply: ## [dev common] Apply Terraform (prompts)
	@$(MAKE) apply TARGET_TF_DIR=$(DEV_COMMON_TF_DIR) TF_CMD_ARGS="$(DEV_COMMON_TF_CMD_ARGS)"
dev-common-apply-auto: ## [dev common] Apply Terraform (auto-approves)
	@$(MAKE) apply-auto TARGET_TF_DIR=$(DEV_COMMON_TF_DIR) TF_CMD_ARGS="$(DEV_COMMON_TF_CMD_ARGS)"
dev-common-destroy: ## [dev common] Destroy resources (prompts)
	@$(MAKE) destroy TARGET_TF_DIR=$(DEV_COMMON_TF_DIR) TF_CMD_ARGS="$(DEV_COMMON_TF_CMD_ARGS)"
dev-common-destroy-auto: ## [dev common] Destroy resources (auto-approves)
	@$(MAKE) destroy-auto TARGET_TF_DIR=$(DEV_COMMON_TF_DIR) TF_CMD_ARGS="$(DEV_COMMON_TF_CMD_ARGS)"

# Dev - hello-world Lambda
# LAMBDA_IMAGE_URI must be passed for plan/apply/destroy if it's a required variable.
# Example: make dev-hello-world-apply LAMBDA_IMAGE_URI="your-image-uri"
DEV_HW_LAMBDA_TF_DIR := $(LAMBDAS_BASE_DIR)/hello-world
DEV_HW_TF_CMD_ARGS := -var-file=../../$(ENVIRONMENTS_BASE_DIR)/dev/terraform.tfvars -var="image_uri=$(LAMBDA_IMAGE_URI)"

dev-hello-world-init: ## [dev hello-world] Initialize Terraform
	@$(MAKE) init TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR)
dev-hello-world-validate: ## [dev hello-world] Validate Terraform
	@$(MAKE) validate TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR)
dev-hello-world-plan: ## [dev hello-world] Plan Terraform (Requires LAMBDA_IMAGE_URI if var is not defaulted)
	@$(MAKE) plan TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_HW_TF_CMD_ARGS)"
dev-hello-world-apply: ## [dev hello-world] Apply Terraform (Requires LAMBDA_IMAGE_URI, prompts)
	@$(MAKE) apply TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_HW_TF_CMD_ARGS)"
dev-hello-world-apply-auto: ## [dev hello-world] Apply Terraform (Requires LAMBDA_IMAGE_URI, auto-approves)
	@$(MAKE) apply-auto TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_HW_TF_CMD_ARGS)"
dev-hello-world-destroy: ## [dev hello-world] Destroy resources (Requires LAMBDA_IMAGE_URI, prompts)
	@$(MAKE) destroy TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_HW_TF_CMD_ARGS)"
dev-hello-world-destroy-auto: ## [dev hello-world] Destroy resources (Requires LAMBDA_IMAGE_URI, auto-approves)
	@$(MAKE) destroy-auto TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_HW_TF_CMD_ARGS)"

# Add similar blocks for 'prod' environment or other lambdas as needed.
# Example for another lambda 'my-api' in dev:
# DEV_MYAPI_LAMBDA_TF_DIR := $(LAMBDAS_BASE_DIR)/my-api
# DEV_MYAPI_TF_CMD_ARGS := -var-file=../../$(ENVIRONMENTS_BASE_DIR)/dev/terraform.tfvars -var="image_uri=$(LAMBDA_IMAGE_URI)"
# dev-my-api-plan:
#	@$(MAKE) plan TARGET_TF_DIR=$(DEV_MYAPI_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_MYAPI_TF_CMD_ARGS)"
