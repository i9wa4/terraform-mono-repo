SHELL := /usr/bin/env bash
# .SHELLFLAGS := -o verbose -o xtrace -o errexit -o nounset -o pipefail -o posix -c
.SHELLFLAGS := -o errexit -o nounset -o pipefail -o posix -c
.DEFAULT_GOAL := help

# all targets are phony
.PHONY: $(shell grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | sed 's/://')

help:  ## print this help
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Get the service name from the current directory
SERVICE_NAME := $(shell basename $(shell pwd))
ENVIRONMENT ?= dev
TERRAFORM_DIR := $(ENVIRONMENT)/terraform
APP_DIR := $(ENVIRONMENT)/app
TF_OPT ?=
IMAGE_TAG ?= $(shell git rev-parse HEAD)

# Variables passed from GitHub Actions or command line:
# ECR_REGISTRY, FULL_ECR_REPOSITORY_NAME, IMAGE_TAG,
# ECR_REPOSITORY_NAME, LAMBDA_FUNCTION_NAME, ECR_IMAGE_URI, TF_LOG, ENVIRONMENT
# AWS_REGION is typically handled by AWS provider configuration (e.g., credentials file or instance profile)

# Conditionally set Terraform environment variable option
# Only pass -var="environment=..." if $(ENVIRONMENT) is not "dev" (the default in variables.tf)
TF_ENVIRONMENT_VAR_OPT :=
ifneq ($(ENVIRONMENT),dev)
	TF_ENVIRONMENT_VAR_OPT := -var="environment=$(ENVIRONMENT)"
endif

# Docker build and push target
build-push: ## Build and push Docker image to ECR
	@echo "Building and pushing Docker image for $(ENVIRONMENT) from $(APP_DIR)"
	@echo "ECR Registry: $(ECR_REGISTRY)"
	@echo "Repository Name: $(FULL_ECR_REPOSITORY_NAME)"
	@echo "Image Tag: $(IMAGE_TAG)"
	cd $(APP_DIR) && docker build -t $(ECR_REGISTRY)/$(FULL_ECR_REPOSITORY_NAME):$(IMAGE_TAG) .
	docker push $(ECR_REGISTRY)/$(FULL_ECR_REPOSITORY_NAME):$(IMAGE_TAG)

# Terraform targets as called by GitHub Actions
tf-init: ## Initialize Terraform for the specified environment
	@echo "Initializing Terraform in $(TERRAFORM_DIR) for $(ENVIRONMENT)"
	terraform -chdir=$(TERRAFORM_DIR) init

tf-validate: ## Validate Terraform configuration for the specified environment
	@echo "Validating Terraform configuration in $(TERRAFORM_DIR) for $(ENVIRONMENT)"
	terraform -chdir=$(TERRAFORM_DIR) validate

tf-apply-iam: ## Apply ECR and IAM resources using Terraform
	@echo "Applying ECR and IAM resources in $(TERRAFORM_DIR) for $(ENVIRONMENT)"
	@echo "Params: ECR_REPOSITORY_NAME=$(ECR_REPOSITORY_NAME), LAMBDA_FUNCTION_NAME=$(LAMBDA_FUNCTION_NAME), TF_LOG=$(TF_LOG), ENVIRONMENT=$(ENVIRONMENT)"
	TF_LOG=$(TF_LOG) terraform -chdir=$(TERRAFORM_DIR) apply -auto-approve \
		-var="ecr_repository_name=$(ECR_REPOSITORY_NAME)" \
		-var="lambda_function_name=$(LAMBDA_FUNCTION_NAME)" \
		$(TF_ENVIRONMENT_VAR_OPT) \
		-var="ecr_image_uri=not_used_for_iam_step" \
		-target=aws_ecr_repository.app_ecr_repo \
		-target=aws_iam_role.lambda_exec_role \
		-target=aws_iam_policy.lambda_exec_policy \
		-target=aws_iam_role_policy_attachment.lambda_exec_policy_attachment

tf-apply-lambda: ## Apply Lambda function and related resources using Terraform
	@echo "Applying Lambda function in $(TERRAFORM_DIR) for $(ENVIRONMENT)"
	@echo "Params: ECR_IMAGE_URI=$(ECR_IMAGE_URI), ECR_REPOSITORY_NAME=$(ECR_REPOSITORY_NAME), LAMBDA_FUNCTION_NAME=$(LAMBDA_FUNCTION_NAME), ENVIRONMENT=$(ENVIRONMENT)"
	terraform -chdir=$(TERRAFORM_DIR) apply -auto-approve \
		-var="ecr_image_uri=$(ECR_IMAGE_URI)" \
		-var="ecr_repository_name=$(ECR_REPOSITORY_NAME)" \
		-var="lambda_function_name=$(LAMBDA_FUNCTION_NAME)" \
		$(TF_ENVIRONMENT_VAR_OPT)

# Original generic Terraform targets (can be kept for local use)
init:
	@echo "Initializing Terraform in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) init

fmt:
	@echo "Formatting Terraform files in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) fmt -recursive

validate: fmt
	@echo "Validating Terraform configuration in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) validate

plan: init validate
	@echo "Planning Terraform in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) plan -out=.terraform.plan.$(ENVIRONMENT).tfplan -no-color $(TF_OPT)

apply: init
	@echo "Applying Terraform in $(TERRAFORM_DIR)"
	# $(TF_OPT) is omitted here. This target applies a specific plan file.
	# Plan-affecting options from TF_OPT (like -target or -var) should be used during 'make plan'.
	# If TF_OPT contains a positional argument (e.g., a directory path), it conflicts with applying a specific plan file,
	# leading to a "Too many command line arguments" error.
	# If apply-specific options (like -parallelism=N) were intended via TF_OPT, they will not be used by this target.
	terraform -chdir=$(TERRAFORM_DIR) apply .terraform.plan.$(ENVIRONMENT).tfplan -auto-approve

plan-destroy: init
	@echo "Planning Terraform destroy in $(TERRAFORM_DIR)"
	terraform -chdir=$(TERRAFORM_DIR) plan -destroy -out=.terraform.plan.destroy.$(ENVIRONMENT).tfplan -no-color $(TF_OPT)

destroy: init
	@echo "Destroying Terraform resources in $(TERRAFORM_DIR)"
	# $(TF_OPT) is omitted here for the same reasons as in the 'apply' target.
	# Plan-affecting options from TF_OPT should be used during 'make plan-destroy'.
	terraform -chdir=$(TERRAFORM_DIR) destroy .terraform.plan.destroy.$(ENVIRONMENT).tfplan -auto-approve

# Environment specific aliases using ENVIRONMENT variable
dev-plan:  ## [dev] plan
	@$(MAKE) plan ENVIRONMENT=dev TF_OPT="$(TF_OPT)"

dev-apply:  ## [dev] apply
	@$(MAKE) apply ENVIRONMENT=dev TF_OPT="$(TF_OPT)"

dev-plan-destroy:  ## [dev] plan-destroy
	@$(MAKE) plan-destroy ENVIRONMENT=dev TF_OPT="$(TF_OPT)"

dev-destroy:  ## [dev] destroy
	@$(MAKE) destroy ENVIRONMENT=dev TF_OPT="$(TF_OPT)"

prod-plan:  ## [prod] plan
	@$(MAKE) plan ENVIRONMENT=prod TF_OPT="$(TF_OPT)"

prod-apply:  ## [prod] apply
	@$(MAKE) apply ENVIRONMENT=prod TF_OPT="$(TF_OPT)"

prod-plan-destroy:  ## [prod] plan-destroy
	@$(MAKE) plan-destroy ENVIRONMENT=prod TF_OPT="$(TF_OPT)"

prod-destroy:  ## [prod] destroy
	@$(MAKE) destroy ENVIRONMENT=prod TF_OPT="$(TF_OPT)"
