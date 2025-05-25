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
PROJECT_NAME ?= mcp-lambda-ecr
AWS_REGION ?= ap-northeast-1
ENV ?= dev

# Directories
COMMON_DIR := terraform
LAMBDAS_BASE_DIR := lambdas
ENV_DIR := environments/$(ENV)

# Common Infrastructure
COMMON_VAR_FILE_ARGS := '-var-file=../$(ENV_DIR)/terraform.tfvars'
APP_NAMES_ARG := '-var-file=../$(ENV_DIR)/common_auto.tfvars.json'
AWS_ACCOUNT_ID := $(strip $(shell terraform -chdir=$(COMMON_DIR) output -raw aws_account_id 2>/dev/null))
ECR_REGISTRY := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
PLAN_FILE_NAME := plan.tfplan
# PLAN_DESTROY_FILE_NAME := plan.destroy.tfplan

# Lambda Functions
LAMBDA_VAR_FILE_ARGS := '-var-file=../../$(ENV_DIR)/terraform.tfvars'

# ----------------------
# Public Targets
#
common-plan: generate_app_names_list ## [common] terraform plan
	$(MAKE) plan \
		TARGET_DIR="$(COMMON_DIR)" \
		PLAN_FILE_ARGS="-out=$(PLAN_FILE_NAME)" \
		VAR_FILE_ARGS="$(COMMON_VAR_FILE_ARGS)" \
		TF_ARGS="$(APP_NAMES_ARG) $(COMMON_ARGS)"

common-apply: ## [common] terraform apply
	$(MAKE) apply \
		TARGET_DIR="$(COMMON_DIR)" \
		PLAN_FILE_ARGS="$(PLAN_FILE_NAME)"

lambda-plan: ## [lambda] terraform plan (e.g. make lambda-plan APP_NAME=hello-world)
	$(MAKE) plan \
		TARGET_DIR=lambdas/$(APP_NAME) \
		VAR_FILE_ARGS=$(LAMBDA_VAR_FILE_ARGS) \
		TF_ARGS='$(LAMBDA_ARGS) -var="image_uri=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h 2>/dev/null | tr -d '[:space:]')"' \
		PLAN_FILE_ARGS="-out=$(PLAN_FILE_NAME)"

lambda-apply: ## [lambda] build image & terraform apply (e.g. make lambda-apply APP_NAME=hello-world)
	$(MAKE) ecr-login ECR_REGISTRY=$(ECR_REGISTRY)
	$(MAKE) ecr-build-push \
		ECR_IMAGE_URI=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h 2>/dev/null | tr -d '[:space:]') \
		APP_ROOT_DIR=lambdas/$(APP_NAME)
	$(MAKE) apply \
		TARGET_DIR=lambdas/$(APP_NAME) \
		PLAN_FILE_ARGS=$(PLAN_FILE_NAME)

lambda-apply-gha: ## [lambda] build image & terraform apply for GitHub Actions
	# No need to log in to ECR
	$(MAKE) ecr-build-push \
		ECR_IMAGE_URI=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h 2>/dev/null | tr -d '[:space:]') \
		APP_ROOT_DIR=lambdas/$(APP_NAME)
	$(MAKE) apply \
		TARGET_DIR=lambdas/$(APP_NAME) \
		PLAN_FILE_ARGS=$(PLAN_FILE_NAME)

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

generate_app_names_list:
	@echo "Finding Lambda app names and generating JSON content directly..."
	@( \
		temp_app_list_for_json="" && \
		app_names_found=$$(find $(LAMBDAS_BASE_DIR) -mindepth 1 -maxdepth 1 -type d -exec basename {} \;) && \
		if [ -n "$$app_names_found" ]; then \
			temp_app_list_for_json=$$(echo "$$app_names_found" | awk '{printf "\"%s\",", $$0}' | sed 's/,$$//'); \
		fi; \
		echo -n '{"lambda_app_names": ['; \
		if [ -n "$$temp_app_list_for_json" ]; then echo -n "$$temp_app_list_for_json"; fi; \
		echo ']}'; \
	) > $(ENV_DIR)/common_auto.tfvars.json
	@echo "Generated JSON file content:"
	@cat $(ENV_DIR)/common_auto.tfvars.json || echo "!! File not found or is empty (check permissions or path). !!"

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

ecr-build-push:
	docker build -t $(ECR_IMAGE_URI) $(APP_ROOT_DIR) --platform=linux/arm64 --provenance=false
	docker push $(ECR_IMAGE_URI)
