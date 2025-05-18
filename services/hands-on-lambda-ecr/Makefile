# Makefile to manage Terraform deployments for individual Lambda functions and CI/CD roles
# This Makefile is intended to be in services/hands-on-lambda-ecr/

SHELL := /usr/bin/env bash
.SHELLFLAGS := -o errexit -o nounset -o pipefail -o posix -c
.DEFAULT_GOAL := help

# --- Configuration ---
# Default environment and lambda if not specified.
# Override by passing arguments: make plan lambda=my_example_lambda env=dev
ENV ?= dev
LAMBDA ?= my_example_lambda # Default lambda for lambda-specific targets
COMPONENT ?= lambda # 'lambda' or 'cicd'

# Base directories relative to this Makefile's location
LAMBDAS_BASE_DIR := lambdas
CICD_DIR := terraform_cicd
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

# --- Helper Targets ---
.PHONY: help
help:
	@echo "Usage: make <target> [lambda=<lambda_name>] [env=<environment_name>] [LAMBDA_IMAGE_URI=<image_uri>] [component=lambda|cicd]"
	@echo ""
	@echo "Common Targets (specify component=lambda or component=cicd, lambda=... if component=lambda):"
	@echo "  init        Initialize Terraform for the specified component."
	@echo "  validate    Validate Terraform configuration."
	@echo "  plan        Create an execution plan."
	@echo "  apply       Apply the changes (prompts for approval)."
	@echo "  apply-auto  Apply the changes (auto-approves)."
	@echo "  destroy     Destroy resources (prompts for approval)."
	@echo "  destroy-auto Destroy resources (auto-approves)."
	@echo ""
	@echo "Lambda Specific Targets (component=lambda is implicit):"
	@echo "  lambda-ecr-login   Login to ECR."
	@echo "  lambda-build-push  Build and push Docker image for the specified lambda."
	@echo ""
	@echo "Arguments:"
	@echo "  lambda      Name of the lambda function directory under '$(LAMBDAS_BASE_DIR)/'. Default: $(LAMBDA)"
	@echo "  env         Environment name (e.g., dev, prod). Default: $(ENV)"
	@echo "  component   'lambda' or 'cicd'. Default: lambda"
	@echo "  LAMBDA_IMAGE_URI Image URI for the lambda function. Default: $(LAMBDA_IMAGE_URI)"
	@echo ""
	@echo "Examples:"
	@echo "  make plan lambda=my_example_lambda env=dev"
	@echo "  make apply lambda=my_example_lambda env=dev LAMBDA_IMAGE_URI=$(ECR_REGISTRY)/my_example_lambda:v1.2.3"
	@echo "  make plan component=cicd env=dev"

# --- Pre-flight Checks ---
check_lambda_params:
ifndef LAMBDA
	$(error lambda argument is required. Usage: make <target> lambda=<lambda_name>)
endif
	@if [ ! -d "$(LAMBDA_TF_DIR)" ]; then echo "Error: Lambda directory '$(LAMBDA_TF_DIR)' does not exist."; exit 1; fi
	@if [ ! -f "$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars" ]; then echo "Error: Env tfvars file '$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars' does not exist."; exit 1; fi

check_cicd_params:
	@if [ ! -d "$(CICD_TF_DIR)" ]; then echo "Error: CI/CD Terraform directory '$(CICD_TF_DIR)' does not exist."; exit 1; fi
	@if [ ! -f "$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars" ]; then echo "Error: Env tfvars file '$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars' does not exist."; exit 1; fi


# --- Lambda Specific Docker Targets ---
.PHONY: lambda-ecr-login lambda-build-push
lambda-ecr-login:
	@echo "Logging in to ECR registry $(ECR_REGISTRY) in region $(AWS_REGION)"
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

lambda-build-push: check_lambda_params lambda-ecr-login
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

.PHONY: init validate plan apply apply-auto destroy destroy-auto
init: $(PRE_REQ_CHECK)
	@echo "==> Initializing Terraform for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) init -backend-config="key=hands-on-lambda-ecr/$(TARGET_TF_DIR)/terraform.tfstate"

validate: $(PRE_REQ_CHECK)
	@echo "==> Validating Terraform for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) validate

plan: init
	@echo "==> Planning changes for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) plan $(TF_VARS_ARG)

apply: init
	@echo "==> Applying changes for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) apply $(TF_VARS_ARG)

apply-auto: init
	@echo "==> Applying changes (auto-approve) for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) apply $(TF_VARS_ARG) -auto-approve

destroy: init
	@echo "==> Destroying resources for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) destroy $(TF_VARS_ARG)

destroy-auto: init
	@echo "==> Destroying resources (auto-approve) for component: $(COMPONENT)$(if $(filter lambda,$(COMPONENT)), (lambda: $(LAMBDA)),) in env: $(ENV) from $(TARGET_TF_DIR)"
	terraform -chdir=$(TARGET_TF_DIR) destroy $(TF_VARS_ARG) -auto-approve
