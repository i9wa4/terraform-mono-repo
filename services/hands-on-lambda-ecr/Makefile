SHELL := /usr/bin/env bash
.SHELLFLAGS := -o errexit -o nounset -o pipefail -o posix -c
.DEFAULT_GOAL := help

# All targets are phony
.PHONY: $(shell grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | sed 's/:.*//')

help:  ## print this help
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --------------------
# Variables
#
# Required for backend
TF_BACKEND_S3_BUCKET ?= "$${TF_BACKEND_S3_BUCKET}"
PROJECT_NAME ?= hands-on-lambda-ecr
AWS_REGION ?= ap-northeast-1

# Common
ENV ?= dev
COMMON_TF_DIR := terraform
COMMON_TF_CMD_ARGS := '-var-file=../environments/$(ENV)/terraform.tfvars'
AWS_ACCOUNT_ID := $(strip $(shell terraform -chdir=$(COMMON_TF_DIR) output -raw aws_account_id 2>/dev/null))

# Lambda
ECR_REGISTRY ?= $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

# ----------------------
# Public Targets
#
common-plan: ## [common] terraform plan
	$(MAKE) plan TARGET_TF_DIR=$(COMMON_TF_DIR) TF_CMD_ARGS=$(COMMON_TF_CMD_ARGS)

common-apply: ## [common] terraform apply
	$(MAKE) apply TARGET_TF_DIR=$(COMMON_TF_DIR) TF_CMD_ARGS=$(COMMON_TF_CMD_ARGS)

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
		-backend-config="key=$(PROJECT_NAME)/$(TARGET_TF_DIR)/terraform.tfstate"

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

lambda-plan:
	$(MAKE) plan \
		TARGET_TF_DIR=lambdas/$(APP_NAME) \
		TF_CMD_ARGS='-var-file=../../environments/$(ENV)/terraform.tfvars -var='image_uri=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]')''

lambda-apply:
	$(MAKE) ecr-build-push \
		ECR_IMAGE_URI=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]') \
		APP_ROOT_DIR=lambdas/$(APP_NAME)
	$(MAKE) apply \
		TARGET_TF_DIR=lambdas/$(APP_NAME) \
		TF_CMD_ARGS='-var-file=../../environments/$(ENV)/terraform.tfvars -var='image_uri=$(ECR_REGISTRY)/$(PROJECT_NAME)-$(ENV)-$(APP_NAME):$(shell git log -1 --format=%h -- lambdas/$(APP_NAME) 2>/dev/null | tr -d '[:space:]')''
