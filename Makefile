DB ?=
FOLDER ?=
CONCURRENCY ?=

.PHONY: install collect-categories collect-apps

install:
	poetry install
	poetry run playwright install chromium

collect-categories:
	poetry run python -m app.main categories

collect-apps:
	@test -n "$(DB)" || (echo "DB argument is required: make collect-apps DB=myname" && exit 1)
	poetry run python -m app.main apps --db $(DB) $(if $(FOLDER),--folder $(FOLDER),) $(if $(CONCURRENCY),--concurrency $(CONCURRENCY),)
