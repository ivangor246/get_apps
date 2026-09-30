.PHONY: install install-backend install-frontend \
        dev dev-backend dev-frontend \
        build build-frontend start clean \
        format format-backend format-frontend

install: install-backend install-frontend

install-backend:
	cd back && poetry install
	cd back && poetry run playwright install chromium

install-frontend:
	npm --prefix front install

dev-backend:
	cd back && poetry run uvicorn app.api.app:create_app --factory --reload --host 127.0.0.1 --port 8000

dev-frontend:
	npm --prefix front run dev

dev:
	@echo "Starting backend (:8000) and frontend (:5173); Ctrl+C stops both."
	@trap 'kill 0' INT TERM; \
	  $(MAKE) dev-backend & \
	  $(MAKE) dev-frontend & \
	  wait

build: build-frontend

build-frontend:
	npm --prefix front run build

start:
	cd back && poetry run python -m app.main

clean:
	rm -rf front/dist front/node_modules/.vite

format: format-backend format-frontend

format-backend:
	cd back && poetry run ruff format src

format-frontend:
	npm --prefix front run format
