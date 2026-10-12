.PHONY: test test-build

test:
	docker compose --profile test run --rm --build test

test-build:
	docker compose --profile test build test
