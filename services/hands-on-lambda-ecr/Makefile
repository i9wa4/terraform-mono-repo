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
TF_BACKEND_S3_BUCKET ?= "your-default-s3-bucket"
PROJECT_NAME ?= hands-on-lambda-ecr
AWS_REGION ?= ap-northeast-1
ENV ?= dev

COMMON_DIR := terraform
COMMON_VAR_FILE_ARGS := '-var-file=../environments/$(ENV)/terraform.tfvars'
AWS_ACCOUNT_ID := $(strip $(shell terraform -chdir=$(COMMON_DIR) output -raw aws_account_id 2>/dev/null))
ECR_REGISTRY := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
PLAN_FILE_NAME := plan.tfplan
# PLAN_DESTROY_FILE_NAME := plan.destroy.tfplan

LAMBDA_VAR_FILE_ARGS := '-var-file=../../environments/$(ENV)/terraform.tfvars'

# ----------------------
# Public Targets
#
common-iam-plan: ## [common-iam] terraform plan to create initial IAM roles for GitHub Actions CI/CD bootstrap
	$(MAKE) plan \
		TARGET_DIR="$(COMMON_DIR)" \
		PLAN_FILE_ARGS="-out=$(PLAN_FILE_NAME)" \
		VAR_FILE_ARGS="$(COMMON_VAR_FILE_ARGS)" \
		TF_ARGS="-target=aws_iam_role.terraform_hands_on_lambda_ecr -target=aws_iam_role_policy_attachment.github_actions_oidc_role_admin_attachment"

common-plan: ## [common] terraform plan
	$(MAKE) plan \
		TARGET_DIR="$(COMMON_DIR)" \
		PLAN_FILE_ARGS="-out=$(PLAN_FILE_NAME)" \
		VAR_FILE_ARGS="$(COMMON_VAR_FILE_ARGS)" \
		TF_ARGS="$(COMMON_ARGS)"

common-apply: ## [common] terraform apply
	$(MAKE) apply \
		TARGET_DIR="$(COMMON_DIR)" \
		PLAN_FILE_ARGS="$(PLAN_FILE_NAME)"

hello-world-plan: ## [hello-world] terraform plan
	$(MAKE) lambda-plan APP_NAME=hello-world

hello-world-apply: ## [hello-world] terraform apply
	$(MAKE) lambda-apply APP_NAME=hello-world

# ----------------------
# Private Targets
#
init:
	terraform -chdir=$(TARGET_DIR) init -reconfigure \
		-backend-config="region=$(AWS_REGION)" \
		-backend-config="bucket=$(TF_BACKEND_S3_BUCKET)" \
		-backend-config="key=$(PROJECT_NAME)/$(TARGET_DIR)/terraform.tfstate" \
		-backend-config="encrypt=true" \
		-backend-config="use_lockfile=true"

validate: init
	terraform -chdir=$(TARGET_DIR) validate

plan: validate
	terraform -chdir=$(TARGET_DIR) plan $(PLAN_FILE_ARGS) $(VAR_FILE_ARGS) $(TF_ARGS)

apply: init
	terraform -chdir=$(TARGET_DIR) apply -auto-approve $(PLAN_FILE_ARGS)

plan-destroy: validate
	terraform -chdir=$(TARGET_DIR) plan -destroy $(PLAN_FILE_ARGS) $(VAR_FILE_ARGS) $(TF_ARGS)

destroy: plan-destroy
	terraform -chdir=$(TARGET_DIR) destroy -auto-approve $(PLAN_FILE_ARGS)

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

ecr-build-push:
	docker build -t $(ECR_IMAGE_URI) $(APP_ROOT_DIR) --platform=linux/arm64 --provenance=false
	docker push $(ECR_IMAGE_URI)

lambda-init:
	$(MAKE) init TARGET_DIR=lambdas/$(APP_NAME)

lambda-plan:
	$(MAKE) plan \
		TARGET_DIR=lambdas/$(APP_NAME) \
		VAR_FILE_ARGS=$(LAMBDA_VAR_FILE_ARGS) \
		TF_ARGS='$(LAMBDA_ARGS) -var="image_uri=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]')"' \
		PLAN_FILE_ARGS="-out=$(PLAN_FILE_NAME)"

lambda-apply:
	$(MAKE) ecr-login ECR_REGISTRY=$(ECR_REGISTRY)
	$(MAKE) ecr-build-push \
		ECR_IMAGE_URI=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]') \
		APP_ROOT_DIR=lambdas/$(APP_NAME)
	$(MAKE) apply \
		TARGET_DIR=lambdas/$(APP_NAME) \
		PLAN_FILE_ARGS=$(PLAN_FILE_NAME)

lambda-apply-gha:
	$(MAKE) ecr-build-push \
		ECR_IMAGE_URI=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]') \
		APP_ROOT_DIR=lambdas/$(APP_NAME)
	$(MAKE) apply \
		TARGET_DIR=lambdas/$(APP_NAME) \
		PLAN_FILE_ARGS=$(PLAN_FILE_NAME)
