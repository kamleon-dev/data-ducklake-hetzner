.PHONY: all apply terraform-apply deploy init check-env duckdb wait-for-ssh destroy \
       validate lint test

all: check-env terraform-apply deploy

apply: terraform-apply

check-env:
	@echo "Checking required environment variables..."
	@test -n "$$TF_VAR_hcloud_token" || (echo "ERROR: TF_VAR_hcloud_token is not set" && exit 1)
	@test -n "$$S3_ACCESS_KEY" || (echo "ERROR: S3_ACCESS_KEY is not set" && exit 1)
	@test -n "$$S3_SECRET_KEY" || (echo "ERROR: S3_SECRET_KEY is not set" && exit 1)
	@test -n "$$POSTGRES_DB_PASSWORD" || (echo "ERROR: POSTGRES_DB_PASSWORD is not set" && exit 1)
	@echo "All required environment variables are set"

init:
	cd terraform && tofu init

terraform-apply: check-env
	cd terraform && tofu apply -var="hetzner_storage_access_key=$$S3_ACCESS_KEY" -var="hetzner_storage_secret_key=$$S3_SECRET_KEY" -var="s3_bucket_name=$$S3_BUCKET_NAME"
	mkdir -p data
	cd terraform && tofu output -json ducklake_postgres_ip > ../data/ducklake_postgres_ip.json

wait-for-ssh:
	@echo "Waiting for SSH on $$(cat data/ducklake_postgres_ip.json | tr -d '\"')..."
	@until ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i "$${SSH_KEY_PATH}" root@$$(cat data/ducklake_postgres_ip.json | tr -d '\"') true 2>/dev/null; do echo "  not ready, retrying..."; sleep 5; done
	@echo "SSH is up"

deploy: wait-for-ssh
	cd config && uv sync
	cd config && pyinfra inventory.py deploy.py --key "$${SSH_KEY_PATH}" --user root

destroy:
	cd terraform && tofu destroy -var="hetzner_storage_access_key=$$S3_ACCESS_KEY" -var="hetzner_storage_secret_key=$$S3_SECRET_KEY" -var="s3_bucket_name=$$S3_BUCKET_NAME"

duckdb:
	duckdb -init init.sql

lint:
	tofu fmt -check -recursive terraform/
	cd config && uv run --group dev ruff check .
	cd config && uv run --group dev ruff format --check .

validate:
	cd terraform && tofu init -backend=false && tofu validate

test: lint validate
