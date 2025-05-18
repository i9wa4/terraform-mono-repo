# Makefile to manage Terraform deployments for individual Lambda functions and CI/CD roles
# This Makefile is intended to be in services/hands-on-lambda-ecr/

SHELL := /usr/bin/env bash
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
# Default environment and lambda if not specified.
# Override by passing arguments: make plan lambda=my_example_lambda env=dev
ENV ?= dev
LAMBDA ?= my_example_lambda # Default lambda for lambda-specific targets
COMPONENT ?= lambda # 'lambda' or 'cicd'

# Base directories relative to this Makefile's location
LAMBDAS_BASE_DIR := lambdas
CICD_DIR := terraform # Changed from terraform_cicd
ENVIRONMENTS_BASE_DIR := environments

# Calculated paths
# For Lambda components:
LAMBDA_TF_DIR := $(LAMBDAS_BASE_DIR)/$(LAMBDA)
LAMBDA_APP_DIR := $(LAMBDAS_BASE_DIR)/$(LAMBDA)/app # Assuming app code is here
ENV_VARS_FILE_FOR_LAMBDA := ../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars # Relative to LAMBDA_TF_DIR

# For CI/CD component:
CICD_TF_DIR := $(CICD_DIR)
ENV_VARS_FILE_FOR_CICD := ../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars # Relative to CICD_TF_DIR

# Docker image details (primarily for Lambda components)
# ECR_REGISTRY should be set, e.g., 123456789012.dkr.ecr.ap-northeast-1.amazonaws.com
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
	@if [ ! -d "$(LAMBDA_TF_DIR)" ]; then echo "Error: Lambda directory '$(LAMBDA_TF_DIR)' does not exist."; exit 1; fi
	@if [ ! -f "$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars" ]; then echo "Error: Env tfvars file '$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars' does not exist."; exit 1; fi

check_cicd_params: ## Check if CI/CD Terraform directory and environment tfvars file exist
	@if [ ! -d "$(CICD_TF_DIR)" ]; then echo "Error: CI/CD Terraform directory '$(CICD_TF_DIR)' does not exist."; exit 1; fi
	@if [ ! -f "$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars" ]; then echo "Error: Env tfvars file '$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars' does not exist."; exit 1; fi


# --- Lambda Specific Docker Targets ---
lambda-ecr-login: ## Log in to AWS ECR
	@echo "Logging in to ECR registry $(ECR_REGISTRY) in region $(AWS_REGION)"
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

lambda-build-push: check_lambda_params lambda-ecr-login ## Build and push Docker image for the specified lambda to ECR
	@echo "Building and pushing Docker image for lambda: $(LAMBDA) from $(LAMBDA_APP_DIR)"
	@echo "Image: $(LAMBDA_IMAGE_URI)"
	@if [ ! -d "$(LAMBDA_APP_DIR)" ]; then echo "Error: Lambda app directory '$(LAMBDA_APP_DIR)' does not exist. Create it with a Dockerfile."; exit 1; fi
	docker build -t $(LAMBDA_IMAGE_URI) $(LAMBDA_APP_DIR) --platform=linux/arm64 --provenance=false
	docker push $(LAMBDA_IMAGE_URI)

# --- Generic Terraform Targets ---
# These targets use the COMPONENT variable to decide which directory to operate on.
TARGET_TF_DIR := $($(if $(filter lambda,$(COMPONENT)),LAMBDA,CICD)_TF_DIR)
TARGET_ENV_VARS_FILE := $($(if $(filter lambda,$(COMPONENT)),ENV_VARS_FILE_FOR_LAMBDA,ENV_VARS_FILE_FOR_CICD))
TF_VARS_ARG := -var-file=$(TARGET_ENV_VARS_FILE)
ifeq ($(COMPONENT),lambda)
    TF_VARS_ARG += -var="image_uri=$(LAMBDA_IMAGE_URI)"
    PRE_REQ_CHECK = check_lambda_params
else
    PRE_REQ_CHECK = check_cicd_params
endif

init: $(PRE_REQ_CHECK) ## Initialize Terraform for the specified component (lambda or cicd)
	@echo "==> Initializing Terraform for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) init -backend-config="key=hands-on-lambda-ecr/$(TARGET_TF_DIR)/terraform.tfstate"

validate: $(PRE_REQ_CHECK) ## Validate Terraform configuration for the specified component
	@echo "==> Validating Terraform for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) validate

plan: init ## Create a Terraform execution plan for the specified component
	@echo "==> Planning changes for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) plan $(TF_VARS_ARG)

apply: init ## Apply Terraform changes for the specified component (prompts for approval)
	@echo "==> Applying changes for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) apply $(TF_VARS_ARG)

apply-auto: init ## Apply Terraform changes for the specified component (auto-approves)
	@echo "==> Applying changes (auto-approve) for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) apply $(TF_VARS_ARG) -auto-approve

destroy: init ## Destroy Terraform-managed resources for the specified component (prompts for approval)
	@echo "==> Destroying resources for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) destroy $(TF_VARS_ARG)

destroy-auto: init ## Destroy Terraform-managed resources for the specified component (auto-approves)
	@echo "==> Destroying resources (auto-approve) for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) destroy $(TF_VARS_ARG) -auto-approve
