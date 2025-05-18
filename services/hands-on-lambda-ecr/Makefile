# MAKEFLAGS += --warn-undefined-variables
SHELL := /usr/bin/env bash
# .SHELLFLAGS := -o verbose -o xtrace -o errexit -o nounset -o pipefail -o posix -c
.SHELLFLAGS := -o errexit -o nounset -o pipefail -o posix -c
.DEFAULT_GOAL := help

# --- Backend Configuration ---
# Capture environment variable or set default for the S3 bucket name.
_TERRAFORM_BACKEND_S3_BUCKET_ENV_OR_DEFAULT ?= i9wa4-terraform
# Strip any leading/trailing whitespace to prevent issues with backend configuration.
TERRAFORM_BACKEND_S3_BUCKET := $(strip $(_TERRAFORM_BACKEND_S3_BUCKET_ENV_OR_DEFAULT))

# all targets are phony
.PHONY: $(shell grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | sed 's/:.*//')

help:  ## print this help
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init:
	terraform -chdir=$(TARGET_TF_DIR) init -reconfigure \
		-backend-config="bucket=$(TERRAFORM_BACKEND_S3_BUCKET)" \
		-backend-config="key=hands-on-lambda-ecr/$(TARGET_TF_DIR)/terraform.tfstate"

validate: init
	terraform -chdir=$(TARGET_TF_DIR) validate

plan: validate
	terraform -chdir=$(TARGET_TF_DIR) plan $(TF_CMD_ARGS)

apply: plan
	terraform -chdir=$(TARGET_TF_DIR) apply -auto-approve $(TF_CMD_ARGS)

plan-destroy: validate
	terraform -chdir=$(TARGET_TF_DIR) plan -destroy $(TF_CMD_ARGS)

destroy: plan-destroy
	terraform -chdir=$(TARGET_TF_DIR) destroy -auto-approv e$(TF_CMD_ARGS)

# --- Configuration ---
ENV ?= dev
COMMON_DIR := terraform
ENVIRONMENTS_BASE_DIR := environments

# Dev - Common Resources
DEV_COMMON_TF_DIR := $(COMMON_DIR)
DEV_COMMON_TF_CMD_ARGS := -var-file=../$(ENVIRONMENTS_BASE_DIR)/dev/terraform.tfvars

# Attempt to fetch AWS Account ID and Region from the common Terraform configuration outputs.
# These commands will only succeed if 'terraform apply' has been run for the common configuration.
# Fallbacks are provided if these commands fail or return empty.
TF_OUTPUT_AWS_ACCOUNT_ID := $(shell terraform -chdir=$(DEV_COMMON_TF_DIR) output -raw aws_account_id 2>/dev/null)
TF_OUTPUT_AWS_REGION := $(shell terraform -chdir=$(DEV_COMMON_TF_DIR) output -raw aws_region 2>/dev/null)

# Set AWS_REGION: Use value from Terraform output if available, otherwise use environment variable or fallback.
AWS_REGION := $(if $(TF_OUTPUT_AWS_REGION),$(TF_OUTPUT_AWS_REGION),$(AWS_REGION))
AWS_REGION ?= ap-northeast-1 # Default fallback if not set by TF output or environment

# Set AWS_ACCOUNT_ID for ECR: Use value from Terraform output if available, otherwise use a placeholder.
# This is primarily for constructing ECR_REGISTRY.
ECR_AWS_ACCOUNT_ID := $(if $(TF_OUTPUT_AWS_ACCOUNT_ID),$(TF_OUTPUT_AWS_ACCOUNT_ID),"YOUR_AWS_ACCOUNT_ID")

# Docker image details
ECR_REGISTRY ?= $(ECR_AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
IMAGE_TAG ?= $(shell git rev-parse --short HEAD)
# LAMBDA_IMAGE_URI is typically passed to lambda apply targets, or constructed.
# For 'make lambda-build-push', it's constructed using ECR_REGISTRY, LAMBDA, IMAGE_TAG.
DEFAULT_LAMBDA_IMAGE_URI := $(ECR_REGISTRY)/$(LAMBDA):$(IMAGE_TAG)

dev-common-init: ## [dev common] Initialize Terraform
	$(MAKE) init TARGET_TF_DIR=$(DEV_COMMON_TF_DIR)

dev-common-plan: ## [dev common] Plan Terraform
	$(MAKE) plan TARGET_TF_DIR=$(DEV_COMMON_TF_DIR) TF_CMD_ARGS="$(DEV_COMMON_TF_CMD_ARGS)"

dev-common-apply: ## [dev common] Apply Terraform (prompts)
	$(MAKE) apply TARGET_TF_DIR=$(DEV_COMMON_TF_DIR) TF_CMD_ARGS="$(DEV_COMMON_TF_CMD_ARGS)"

dev-common-destroy: ## [dev common] Destroy resources (prompts)
	$(MAKE) destroy TARGET_TF_DIR=$(DEV_COMMON_TF_DIR) TF_CMD_ARGS="$(DEV_COMMON_TF_CMD_ARGS)"


# --- Lambda Specific Docker Targets ---
# Example: make lambda-build-push LAMBDA_CODE_DIR_SUFFIX=my-lambda-dir LAMBDA_ECR_NAME=my-ecr-repo-name
lambda-ecr-login: ## Log in to AWS ECR (uses ECR_REGISTRY, AWS_REGION)
	@echo "Logging in to ECR registry $(ECR_REGISTRY) in region $(AWS_REGION)"
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

lambda-build-push: lambda-ecr-login ## Build and push Docker image. Vars: LAMBDA_CODE_DIR_SUFFIX, LAMBDA_ECR_NAME, ECR_REGISTRY, IMAGE_TAG
	$(eval _LAMBDA_ROOT_DIR := $(LAMBDAS_BASE_DIR)/$(LAMBDA_CODE_DIR_SUFFIX))
	$(eval _CURRENT_LAMBDA_IMAGE_URI := $(ECR_REGISTRY)/$(LAMBDA_ECR_NAME):$(IMAGE_TAG))
	@echo "Building and pushing Docker image for lambda source $(LAMBDA_CODE_DIR_SUFFIX) to ECR repo $(LAMBDA_ECR_NAME) from build context $(_LAMBDA_ROOT_DIR)"
	@echo "Image: $(_CURRENT_LAMBDA_IMAGE_URI)"
	@if [ ! -f "$(_LAMBDA_ROOT_DIR)/Dockerfile" ]; then echo "Error: Dockerfile not found in '$(_LAMBDA_ROOT_DIR)'."; exit 1; fi
	docker build -t $(_CURRENT_LAMBDA_IMAGE_URI) $(_LAMBDA_ROOT_DIR) --platform=linux/arm64 --provenance=false
	docker push $(_CURRENT_LAMBDA_IMAGE_URI)


LAMBDA ?= hello-world # Default lambda name for targets like lambda-build-push if not specified
LAMBDAS_BASE_DIR := lambdas


# AWS Region - ensure this is set in your environment or AWS config
# Note: AWS_REGION is now primarily set using Terraform output from common config, with fallbacks.


# _AWS_ACCOUNT_ID_FROM_TF is no longer needed as we use TF_OUTPUT_AWS_ACCOUNT_ID

# Docker image details are now defined earlier, using TF outputs.


# Dev - hello-world Lambda
# LAMBDA_IMAGE_URI must be passed for plan/apply/destroy if it's a required variable.
# Example: make dev-hello-world-apply LAMBDA_IMAGE_URI="your-image-uri"
DEV_HW_LAMBDA_TF_DIR := $(LAMBDAS_BASE_DIR)/hello-world

# Calculate image tag based on the latest commit in the hello-world lambda's directory.
# Fallback to global IMAGE_TAG (repo HEAD) if directory-specific log fails or path has no commits.
_HELLO_WORLD_DIR_COMMIT_HASH := $(shell git log -1 --format=%h -- $(LAMBDAS_BASE_DIR)/hello-world 2>/dev/null)
DEV_HW_IMAGE_TAG := $(if $(_HELLO_WORLD_DIR_COMMIT_HASH),$(_HELLO_WORLD_DIR_COMMIT_HASH),$(IMAGE_TAG))

# Define the expected ECR repository name for hello-world, matching Terraform's local.effective_function_name
_EXPECTED_HW_ECR_REPO_NAME := hands-on-lambda-ecr-dev-hello-world

# Construct the default image URI for hello-world using its specific tag and correct ECR repo name.
_DEFAULT_DEV_HW_IMAGE_URI_WITH_SPECIFIC_TAG := $(ECR_REGISTRY)/$(_EXPECTED_HW_ECR_REPO_NAME):$(DEV_HW_IMAGE_TAG)

# Use LAMBDA_IMAGE_URI if provided by the user, otherwise use the hello-world specific default URI.
# Note: ECR_REGISTRY must be correctly set.
ACTUAL_DEV_HW_LAMBDA_IMAGE_URI := $(or $(LAMBDA_IMAGE_URI),$(_DEFAULT_DEV_HW_IMAGE_URI_WITH_SPECIFIC_TAG))
DEV_HW_TF_CMD_ARGS := -var-file=../../$(ENVIRONMENTS_BASE_DIR)/dev/terraform.tfvars -var="image_uri=$(ACTUAL_DEV_HW_LAMBDA_IMAGE_URI)"

dev-hello-world-init: ## [dev hello-world] Initialize Terraform
	$(MAKE) init TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR)
dev-hello-world-validate: ## [dev hello-world] Validate Terraform
	$(MAKE) validate TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR)
dev-hello-world-plan: ## [dev hello-world] Plan Terraform
	$(MAKE) plan TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_HW_TF_CMD_ARGS)"

# Internal target to apply ECR repository, IAM, and CloudWatch prerequisites for hello-world
_dev-hello-world-apply-prereqs:
	@echo "Applying ECR repository, IAM, and CloudWatch prerequisites for hello-world..."
	$(MAKE) apply TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS='$(strip $(DEV_HW_TF_CMD_ARGS)) \
		-target=aws_ecr_repository.lambda_ecr_repo \
		-target=aws_iam_role.lambda_exec_role \
		-target=aws_iam_policy.lambda_exec_policy \
		-target=aws_iam_role_policy_attachment.lambda_exec_policy_attachment \
		-target=aws_cloudwatch_log_group.lambda_log_group'

# Internal target to build and push the hello-world image
_dev-hello-world-push-image:
	@echo "Building and pushing hello-world image $(ECR_REGISTRY)/$(_EXPECTED_HW_ECR_REPO_NAME):$(DEV_HW_IMAGE_TAG)..."
	$(MAKE) lambda-build-push LAMBDA_CODE_DIR_SUFFIX=hello-world LAMBDA_ECR_NAME=$(_EXPECTED_HW_ECR_REPO_NAME) IMAGE_TAG=$(DEV_HW_IMAGE_TAG)

dev-hello-world-apply: _dev-hello-world-apply-prereqs _dev-hello-world-push-image ## [dev hello-world] Apply Terraform (Creates ECR/IAM, builds/pushes image, then applies Lambda)
	@echo "Applying all hello-world resources (including Lambda function)..."
	$(MAKE) apply TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_HW_TF_CMD_ARGS)"

dev-hello-world-destroy: ## [dev hello-world] Destroy resources
	$(MAKE) destroy TARGET_TF_DIR=$(DEV_HW_LAMBDA_TF_DIR) TF_CMD_ARGS="$(DEV_HW_TF_CMD_ARGS)"
