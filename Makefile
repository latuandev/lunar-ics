PYTHON ?= python3
DATA_DIR ?= ./data
APP_PORT ?= 8000
NGINX_HOST_PORT ?= 18080

.PHONY: build-dataset verify serve smoke-test test lint typecheck docker-up docker-down

build-dataset:
	$(PYTHON) -m app.main build-dataset --from-year 2000 --to-year 2100 --data-dir $(DATA_DIR)

verify:
	$(PYTHON) -m app.main verify --from-year 2000 --to-year 2100 --data-dir $(DATA_DIR)

serve:
	$(PYTHON) -m app.main serve --host 0.0.0.0 --port $(APP_PORT) --data-dir $(DATA_DIR)

smoke-test:
	$(PYTHON) -m app.main smoke-test --base-url http://127.0.0.1:$(APP_PORT)

test:
	pytest -q

lint:
	ruff check app tests

typecheck:
	mypy app

docker-up:
	NGINX_HOST_PORT=$(NGINX_HOST_PORT) docker compose up --build -d

docker-down:
	docker compose down

