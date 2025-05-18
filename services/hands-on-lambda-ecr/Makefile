# Makefile to manage Terraform deployments for individual Lambda functions and CI/CD roles
# This Makefile is intended to be in services/hands-on-lambda-ecr/

SHELL := /usr/bin/env bash
.SHELLFLAGS := -o errexit -o nounset -o pipefail -o posix -c
.DEFAULT_GOAL := help

# all targets are phony
.PHONY: $(grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | sed 's/://')

help:  ## print this help
	@echo 'Usage: make <target>'
	@echo ''
	@echo 'Targets are generally in the format: <env>-<component_type>-<action> or <env>-<lambda_name>-<action>'
	@echo '  Example: make dev-common-plan'
	@echo '           make dev-hello-world-apply'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / { \
		if ($$1 ~ /^(init|validate|plan|apply|apply-auto|destroy|destroy-auto)$$/) { \
			# Skip generic internal targets from main help list if they have specific versions \
		} else { \
			printf "\033[36m%-40s\033[0m %s\n", $$1, $$2 \
		} \
	}' $(MAKEFILE_LIST)
	@echo ''
	@echo 'Generic internal targets (callable with ENV, COMPONENT, LAMBDA arguments):'
	@awk 'BEGIN {FS = ":.*?## "} /^(init|validate|plan|apply|apply-auto|destroy|destroy-auto):.*?## / {printf "  \033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


# --- Configuration ---
# These variables can be overridden on the command line for generic targets,
# but dedicated targets (e.g., dev-common-plan) set them appropriately.
ENV ?= dev
LAMBDA ?= hello-world # Default lambda name, used if LAMBDA is not set by a specific target
COMPONENT ?= lambda # Default component type ('lambda' or 'common')

# Base directories relative to this Makefile's location
LAMBDAS_BASE_DIR := lambdas
COMMON_DIR := terraform # Directory for common infrastructure (formerly CICD_DIR)
ENVIRONMENTS_BASE_DIR := environments

# Calculated paths
# For Lambda components:
LAMBDA_TF_DIR_TPL := $(LAMBDAS_BASE_DIR)/$(LAMBDA) # Template path, LAMBDA is substituted
LAMBDA_APP_DIR_TPL := $(LAMBDAS_BASE_DIR)/$(LAMBDA)/app # Template path
ENV_VARS_FILE_FOR_LAMBDA_TPL := ../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars # Template path

# For Common component:
COMMON_TF_DIR := $(COMMON_DIR)
ENV_VARS_FILE_FOR_COMMON := ../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars # Relative to COMMON_TF_DIR

# Docker image details (primarily for Lambda components)
# ECR_REGISTRY should be set, e.g., YOUR_AWS_ACCOUNT_ID.dkr.ecr.YOUR_AWS_REGION.amazonaws.com
ECR_REGISTRY ?= YOUR_AWS_ACCOUNT_ID.dkr.ecr.YOUR_AWS_REGION.amazonaws.com
IMAGE_TAG ?= $(shell git rev-parse --short HEAD)
# LAMBDA_IMAGE_URI is constructed or passed directly. For plan/apply, it's crucial.
# Example: make plan lambda=my_lambda env=dev LAMBDA_IMAGE_URI="123..."
LAMBDA_IMAGE_URI ?= $(ECR_REGISTRY)/$(LAMBDA):$(IMAGE_TAG) # Default construction

# AWS Region - ensure this is set in your environment or AWS config
AWS_REGION ?= ap-northeast-1

# --- Pre-flight Checks ---
check_lambda_params: ## Check if required 'lambda' parameter is provided and directory exists
ifndef LAMBDA
	$(error lambda argument is required. Usage: make <target> lambda=<lambda_name>)
endif
	@if [ ! -d "$(LAMBDAS_BASE_DIR)/$(LAMBDA)" ]; then echo "Error: Lambda directory '$(LAMBDAS_BASE_DIR)/$(LAMBDA)' does not exist."; exit 1; fi
	@if [ ! -f "$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars" ]; then echo "Error: Env tfvars file '$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars' does not exist."; exit 1; fi

check_common_params: ## Check if Common Terraform directory and environment tfvars file exist
	@if [ ! -d "$(COMMON_TF_DIR)" ]; then echo "Error: Common Terraform directory '$(COMMON_TF_DIR)' does not exist."; exit 1; fi
	@if [ ! -f "$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars" ]; then echo "Error: Env tfvars file '$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars' does not exist."; exit 1; fi


# --- Lambda Specific Docker Targets ---
# These targets still use the LAMBDA and ENV variables.
# Example: make lambda-build-push LAMBDA=my-lambda ENV=dev
lambda-ecr-login: ## Log in to AWS ECR (uses ECR_REGISTRY, AWS_REGION)
	@echo "Logging in to ECR registry $(ECR_REGISTRY) in region $(AWS_REGION)"
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

lambda-build-push: check_lambda_params lambda-ecr-login ## Build and push Docker image for the specified lambda to ECR
	@echo "Building and pushing Docker image for lambda: $(LAMBDA) from $(LAMBDA_APP_DIR)"
	@echo "Image: $(LAMBDA_IMAGE_URI)"
	@if [ ! -d "$(LAMBDA_APP_DIR)" ]; then echo "Error: Lambda app directory '$(LAMBDA_APP_DIR)' does not exist. Create it with a Dockerfile."; exit 1; fi
	docker build -t $(LAMBDA_IMAGE_URI) $(LAMBDA_APP_DIR) --platform=linux/arm64 --provenance=false
	docker push $(LAMBDA_IMAGE_URI)

# --- Generic Terraform Targets ---
# These are the core implementation targets, called by the dedicated targets below.
# They use COMPONENT, ENV, and LAMBDA (if component=lambda) variables.

# Determine target directory, vars file, and pre-flight check based on COMPONENT
ifeq ($(COMPONENT),lambda)
    # For Lambda component
    TARGET_TF_DIR := $(LAMBDAS_BASE_DIR)/$(LAMBDA)
    TARGET_ENV_VARS_FILE := ../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars # Relative to TARGET_TF_DIR
    TF_VARS_ARG := -var-file=$(TARGET_ENV_VARS_FILE) -var="image_uri=$(LAMBDA_IMAGE_URI)"
    PRE_REQ_CHECK = check_lambda_params
else ifeq ($(COMPONENT),common)
    # For Common component
    TARGET_TF_DIR := $(COMMON_TF_DIR)
    TARGET_ENV_VARS_FILE := $(ENV_VARS_FILE_FOR_COMMON) # Path is already correct relative to Makefile
    TF_VARS_ARG := -var-file=$(TARGET_ENV_VARS_FILE)
    PRE_REQ_CHECK = check_common_params
else
    # Error for invalid COMPONENT value if generic targets are called directly with wrong COMPONENT
    PRE_REQ_CHECK = $(error Invalid COMPONENT value: $(COMPONENT). Must be 'lambda' or 'common'.)
endif

init: $(PRE_REQ_CHECK) ## [Internal] Initialize Terraform for the active component and environment
	@echo "==> Initializing Terraform for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) init -backend-config="key=hands-on-lambda-ecr/$(TARGET_TF_DIR)/terraform.tfstate"

validate: $(PRE_REQ_CHECK) ## Validate Terraform configuration for the specified component
	@echo "==> Validating Terraform for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) validate

plan: init ## [Internal] Create a Terraform execution plan for the active component and environment
	@echo "==> Planning changes for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) plan $(TF_VARS_ARG)

apply: init ## [Internal] Apply Terraform changes for the active component and environment (prompts for approval)
	@echo "==> Applying changes for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) apply $(TF_VARS_ARG)

apply-auto: init ## [Internal] Apply Terraform changes for the active component and environment (auto-approves)
	@echo "==> Applying changes (auto-approve) for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) apply $(TF_VARS_ARG) -auto-approve

destroy: init ## [Internal] Destroy Terraform-managed resources for the active component and environment (prompts for approval)
	@echo "==> Destroying resources for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) destroy $(TF_VARS_ARG)

destroy-auto: init ## [Internal] Destroy Terraform-managed resources for the active component and environment (auto-approves)
	@echo "==> Destroying resources (auto-approve) for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) destroy $(TF_VARS_ARG) -auto-approve

# --- Dedicated Targets for 'dev' environment ---

# Dev - Common Resources
dev-common-init: ## [dev common] Initialize Terraform for common resources in dev
	@$(MAKE) init COMPONENT=common ENV=dev
dev-common-validate: ## [dev common] Validate Terraform for common resources in dev
	@$(MAKE) validate COMPONENT=common ENV=dev
dev-common-plan: ## [dev common] Plan Terraform for common resources in dev
	@$(MAKE) plan COMPONENT=common ENV=dev
dev-common-apply: ## [dev common] Apply Terraform for common resources in dev (prompts)
	@$(MAKE) apply COMPONENT=common ENV=dev
dev-common-apply-auto: ## [dev common] Apply Terraform for common resources in dev (auto-approves)
	@$(MAKE) apply-auto COMPONENT=common ENV=dev
dev-common-destroy: ## [dev common] Destroy common resources in dev (prompts)
	@$(MAKE) destroy COMPONENT=common ENV=dev
dev-common-destroy-auto: ## [dev common] Destroy common resources in dev (auto-approves)
	@$(MAKE) destroy-auto COMPONENT=common ENV=dev

# Dev - hello-world Lambda (example for a specific lambda)
DEV_HW_LAMBDA_NAME := hello-world # Define for clarity, matches default LAMBDA
dev-hello-world-init: ## [dev hello-world] Initialize Terraform for hello-world lambda in dev
	@$(MAKE) init COMPONENT=lambda ENV=dev LAMBDA=$(DEV_HW_LAMBDA_NAME)
dev-hello-world-validate: ## [dev hello-world] Validate Terraform for hello-world lambda in dev
	@$(MAKE) validate COMPONENT=lambda ENV=dev LAMBDA=$(DEV_HW_LAMBDA_NAME)
dev-hello-world-plan: ## [dev hello-world] Plan Terraform for hello-world lambda in dev
	@$(MAKE) plan COMPONENT=lambda ENV=dev LAMBDA=$(DEV_HW_LAMBDA_NAME)
dev-hello-world-apply: ## [dev hello-world] Apply Terraform for hello-world lambda in dev (prompts)
	@$(MAKE) apply COMPONENT=lambda ENV=dev LAMBDA=$(DEV_HW_LAMBDA_NAME)
dev-hello-world-apply-auto: ## [dev hello-world] Apply Terraform for hello-world lambda in dev (auto-approves)
	@$(MAKE) apply-auto COMPONENT=lambda ENV=dev LAMBDA=$(DEV_HW_LAMBDA_NAME)
dev-hello-world-destroy: ## [dev hello-world] Destroy hello-world lambda resources in dev (prompts)
	@$(MAKE) destroy COMPONENT=lambda ENV=dev LAMBDA=$(DEV_HW_LAMBDA_NAME)
dev-hello-world-destroy-auto: ## [dev hello-world] Destroy hello-world lambda resources in dev (auto-approves)
	@$(MAKE) destroy-auto COMPONENT=lambda ENV=dev LAMBDA=$(DEV_HW_LAMBDA_NAME)

# Add similar blocks for 'prod' environment or other lambdas as needed.
# Example for another lambda 'my-api':
# dev-my-api-plan:
#	@$(MAKE) plan COMPONENT=lambda ENV=dev LAMBDA=my-api
