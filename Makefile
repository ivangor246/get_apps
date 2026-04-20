DB ?=
FOLDER ?=
CONCURRENCY ?=
BATCH_SIZE ?=
HOST ?=
PORT ?=

.PHONY: install collect-categories collect-apps index serve

install:
	poetry install
	poetry run playwright install chromium

collect-categories:
	poetry run python -m app.main categories

collect-apps:
	@test -n "$(DB)" || (echo "DB argument is required: make collect-apps DB=myname" && exit 1)
	poetry run python -m app.main apps --db $(DB) $(if $(FOLDER),--folder $(FOLDER),) $(if $(CONCURRENCY),--concurrency $(CONCURRENCY),)

index:
	@test -n "$(DB)" || (echo "DB argument is required: make index DB=myname" && exit 1)
	poetry run python -m app.main index --db $(DB) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(CONCURRENCY),--concurrency $(CONCURRENCY),)

serve:
	@test -n "$(DB)" || (echo "DB argument is required: make serve DB=myname" && exit 1)
	poetry run python -m app.main serve --db $(DB) $(if $(HOST),--host $(HOST),) $(if $(PORT),--port $(PORT),)
