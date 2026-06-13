.PHONY: help run test deploy lint clean

help:
	@echo "[[PROJECT_TITLE]] — Available targets:"
	@echo "  make run      Start the application locally"
	@echo "  make test     Run test suite"
	@echo "  make deploy   Deploy to Render.com"
	@echo "  make lint     Run linter"
	@echo "  make clean    Remove build artifacts"

run:
	[[RUN_COMMAND]]

test:
	[[TEST_COMMAND]]

deploy:
	git push origin main

lint:
	[[LINT_COMMAND]]

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
