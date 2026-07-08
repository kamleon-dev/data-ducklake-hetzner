.PHONY: all apply terraform-apply deploy init check-env duckdb wait-for-ssh destroy \
       validate lint test

all: check-env terraform-apply deploy

apply: terraform-apply

check-env:
	@echo "Checking required environment variables..."
	@test -n "$$TF_VAR_hcloud_token" || (echo "ERROR: TF_VAR_hcloud_token is not set" && exit 1)
	@test -n "$$S3_ACCESS_KEY" || (echo "ERROR: S3_ACCESS_KEY is not set" && exit 1)
	@test -n "$$S3_SECRET_KEY" || (echo "ERROR: S3_SECRET_KEY is not set" && exit 1)
	@test -n "$$TF_WORKSPACE" || (echo "ERROR: TF_WORKSPACE is not set (e.g. 'development-preproduction' or 'production')" && exit 1)
	@test -f "terraform/environments/$${TF_WORKSPACE}.tfvars" || (echo "ERROR: terraform/environments/$${TF_WORKSPACE}.tfvars does not exist" && exit 1)
	@echo "All required environment variables are set"

init:
	cd terraform && tofu init

terraform-apply: check-env
	cd terraform && (tofu workspace select "$${TF_WORKSPACE}" || tofu workspace new "$${TF_WORKSPACE}")
	cd terraform && tofu apply \
		-var-file="environments/$${TF_WORKSPACE}.tfvars" \
		-var="hetzner_storage_access_key=$$S3_ACCESS_KEY" \
		-var="hetzner_storage_secret_key=$$S3_SECRET_KEY"
	mkdir -p data
	cd terraform && tofu output -json server_ip > "../data/$${TF_WORKSPACE}_server_ip.json"
	@echo ""
	@echo "Server IP written to data/$${TF_WORKSPACE}_server_ip.json"
	@echo "Set SSH_HOST in the relevant .env.<environment> file(s) to this IP before running 'make deploy' or 'make duckdb'."

wait-for-ssh:
	@echo "Waiting for SSH on $${SSH_HOST}..."
	@until ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i "$${SSH_KEY_PATH}" root@$${SSH_HOST} true 2>/dev/null; do echo "  not ready, retrying..."; sleep 5; done
	@echo "SSH is up"

deploy: wait-for-ssh
	cd config && uv sync
	cd config && uv run pyinfra inventory.py deploy.py --key "$${SSH_KEY_PATH}" --user root

destroy: check-env
	cd terraform && (tofu workspace select "$${TF_WORKSPACE}" || tofu workspace new "$${TF_WORKSPACE}")
	cd terraform && tofu destroy \
		-var-file="environments/$${TF_WORKSPACE}.tfvars" \
		-var="hetzner_storage_access_key=$$S3_ACCESS_KEY" \
		-var="hetzner_storage_secret_key=$$S3_SECRET_KEY"

duckdb:
	@scp -i "$${SSH_KEY_PATH}" init.sql root@$${SSH_HOST}:/root/init.sql
	@ssh -t -i "$${SSH_KEY_PATH}" root@$${SSH_HOST} \
		"POSTGRES_HOST=localhost \
		 POSTGRES_DATABASE='$${POSTGRES_DATABASE}' \
		 POSTGRES_USER='$${POSTGRES_USER}' \
		 POSTGRES_DB_PASSWORD='$${POSTGRES_DB_PASSWORD}' \
		 S3_ACCESS_KEY='$${S3_ACCESS_KEY}' \
		 S3_SECRET_KEY='$${S3_SECRET_KEY}' \
		 S3_ENDPOINT='$${S3_ENDPOINT}' \
		 S3_REGION='$${S3_REGION}' \
		 S3_DATA_PATH='$${S3_DATA_PATH}' \
		 S3_USE_SSL='$${S3_USE_SSL}' \
		 duckdb -init /root/init.sql"

lint:
	tofu fmt -check -recursive terraform/
	cd config && uv run --group dev ruff check .
	cd config && uv run --group dev ruff format --check .

validate:
	cd terraform && tofu init -backend=false && tofu validate

test: lint validate
