SHELL := /usr/bin/env bash
.SHELLFLAGS := -o errexit -o nounset -o pipefail -o posix -c
.DEFAULT_GOAL := help

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
	terraform -chdir=$(TARGET_TF_DIR) destroy -auto-approve $(TF_CMD_ARGS)

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

ecr-build-push: ecr-login
	docker build -t $(ECR_IMAGE_URI) $(APP_ROOT_DIR) --platform=linux/arm64 --provenance=false
	docker push $(ECR_IMAGE_URI)


# --- Configuration ---
TERRAFORM_BACKEND_S3_BUCKET ?= i9wa4-terraform
ENV ?= dev
COMMON_DIR := terraform
ENVIRONMENTS_BASE_DIR := environments
COMMON_TF_DIR := $(COMMON_DIR)
COMMON_TF_CMD_ARGS := '-var-file=../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars'
TF_OUTPUT_AWS_ACCOUNT_ID := $(strip $(shell terraform -chdir=$(COMMON_TF_DIR) output -raw aws_account_id 2>/dev/null))
TF_OUTPUT_AWS_REGION := $(strip $(shell terraform -chdir=$(COMMON_TF_DIR) output -raw aws_region 2>/dev/null))
AWS_REGION := $(TF_OUTPUT_AWS_REGION)
ECR_AWS_ACCOUNT_ID := $(TF_OUTPUT_AWS_ACCOUNT_ID)
ECR_REGISTRY ?= $(ECR_AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

common-plan: ## [common] Plan Terraform
	$(MAKE) plan TARGET_TF_DIR=$(COMMON_TF_DIR) TF_CMD_ARGS=$(COMMON_TF_CMD_ARGS)

common-apply: ## [common] Apply Terraform (prompts)
	$(MAKE) apply TARGET_TF_DIR=$(COMMON_TF_DIR) TF_CMD_ARGS=$(COMMON_TF_CMD_ARGS)


# --- Lambda Specific Docker Targets ---
HW_LAMBDA_ROOT_DIR := lambdas/hello-world
HW_ECR_REPO := hands-on-lambda-ecr-$(ENV)-hello-world
HW_IMAGE_TAG := $(shell git log -1 --format=%h -- $(HW_LAMBDA_ROOT_DIR) 2>/dev/null | tr -d '[:space:]')
HW_ECR_IMAGE_URI := $(ECR_REGISTRY)/$(HW_ECR_REPO):$(HW_IMAGE_TAG)
HW_TF_CMD_ARGS := '-var-file=../../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars -var='image_uri=$(HW_ECR_IMAGE_URI)''

lambda-plan:
	$(MAKE) plan \
		TARGET_TF_DIR=lambdas/$(APP_NAME) \
		TF_CMD_ARGS='-var-file=../../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars -var='image_uri=$(ECR_REGISTRY)/hands-on-lambda-ecr-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]')''

lambda-apply:
	$(MAKE) ecr-build-push \
		ECR_IMAGE_URI=$(ECR_REGISTRY)/hands-on-lambda-ecr-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]') \
		APP_ROOT_DIR=lambdas/$(APP_NAME)
	$(MAKE) apply \
		TARGET_TF_DIR=lambdas/$(APP_NAME) \
		TF_CMD_ARGS='-var-file=../../$(ENVIRONMENTS_BASE_DIR)/$(ENV)/terraform.tfvars -var='image_uri=$(ECR_REGISTRY)/hands-on-lambda-ecr-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]')''

hello-world-plan: ## [hello-world] Plan Terraform
	$(MAKE) lambda-plan APP_NAME=hello-world

hello-world-apply: ## [hello-world] Apply Terraform (prompts)
	$(MAKE) lambda-apply APP_NAME=hello-world
