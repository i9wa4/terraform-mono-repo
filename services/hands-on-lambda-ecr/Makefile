SHELL := /usr/bin/env bash
.SHELLFLAGS := -o verbose -o xtrace -o errexit -o nounset -o pipefail -o posix -c
.DEFAULT_GOAL := help

.PHONY: $(shell grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | sed 's/:.*//')

help: ## print this help
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --------------------
# Variables
#
TF_BACKEND_S3_BUCKET ?= "your-default-s3-bucket" # Will be overridden by GitHub Actions env
PROJECT_NAME ?= hands-on-lambda-ecr
AWS_REGION ?= ap-northeast-1
AWS_ACCOUNT_ID ?= "your-default-aws-account-id" # Will be overridden by GitHub Actions env

ENV ?= dev
COMMON_TF_DIR := terraform
COMMON_TF_CMD_ARGS := '-var-file=../environments/$(ENV)/terraform.tfvars'

ECR_REGISTRY ?= $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

PLAN_FILE_NAME ?= plan.tfplan
PLAN_FILE_OUTPUT_OPTION ?=
PLAN_FILE_INPUT_ARG ?=

# ----------------------
# Public Targets
#
common-plan: ## [common] terraform plan
	$(MAKE) plan TARGET_TF_DIR=$(COMMON_TF_DIR) TF_CMD_ARGS=$(COMMON_TF_CMD_ARGS) PLAN_FILE_OUTPUT_OPTION="-out=$(PLAN_FILE_NAME)"

common-apply: ## [common] terraform apply
	$(MAKE) apply TARGET_TF_DIR=$(COMMON_TF_DIR) PLAN_FILE_INPUT_ARG=$(PLAN_FILE_NAME)

hello-world-plan: ## [hello-world] terraform plan
	$(MAKE) lambda-plan APP_NAME=hello-world

hello-world-apply: ## [hello-world] terraform apply
	$(MAKE) lambda-apply APP_NAME=hello-world

# ----------------------
# Private Targets
#
init:
	terraform -chdir=$(TARGET_TF_DIR) init -reconfigure \
		-backend-config="region=$(AWS_REGION)" \
		-backend-config="bucket=$(TF_BACKEND_S3_BUCKET)" \
		-backend-config="key=$(PROJECT_NAME)/$(TARGET_TF_DIR)/terraform.tfstate" \
		-backend-config="encrypt=true" \
		-backend-config="use_lockfile=true"

validate: init
	terraform -chdir=$(TARGET_TF_DIR) validate

plan: validate
	terraform -chdir=$(TARGET_TF_DIR) plan $(TF_CMD_ARGS) $(PLAN_FILE_OUTPUT_OPTION)

apply: init
	terraform -chdir=$(TARGET_TF_DIR) apply -auto-approve $(PLAN_FILE_INPUT_ARG)

plan-destroy: validate
	terraform -chdir=$(TARGET_TF_DIR) plan -destroy $(TF_CMD_ARGS) $(PLAN_FILE_OUTPUT_OPTION)

destroy: plan-destroy
	terraform -chdir=$(TARGET_TF_DIR) destroy -auto-approve $(PLAN_FILE_INPUT_ARG)

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

ecr-build-push: ecr-login
	docker build -t $(ECR_IMAGE_URI) $(APP_ROOT_DIR) --platform=linux/arm64 --provenance=false
	docker push $(ECR_IMAGE_URI)

lambda-init:
	$(MAKE) init TARGET_TF_DIR=lambdas/$(APP_NAME)

lambda-plan:
	$(MAKE) plan \
		TARGET_TF_DIR=lambdas/$(APP_NAME) \
		TF_CMD_ARGS='-var-file=../../environments/$(ENV)/terraform.tfvars -var="image_uri=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]')"'\
		PLAN_FILE_OUTPUT_OPTION="-out=$(PLAN_FILE_NAME)"

lambda-apply:
	$(MAKE) ecr-build-push \
		ECR_IMAGE_URI=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]') \
		APP_ROOT_DIR=lambdas/$(APP_NAME)
	$(MAKE) apply \
		TARGET_TF_DIR=lambdas/$(APP_NAME) \
		PLAN_FILE_INPUT_ARG=$(PLAN_FILE_NAME)
