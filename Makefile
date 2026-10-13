.PHONY: help install dev test test-fast lint lint-fix format format-check typecheck build audit-artifact clean bench serve serve-workers-smoke serve-model-smoke serve-soak fault-injection reproduce fidelity docs docs-check lock lock-check check-urls verify-metrics site site-test site-unit-test site-pages-test audit-python audit-critical audit

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

dev: ## Install with development dependencies
	pip install -e ".[dev]"

test: ## Run tests with coverage
	pytest tests/

test-fast: ## Run tests without coverage
	pytest tests/ -v

lint: ## Run linter
	ruff check .

lint-fix: ## Run linter with auto-fix
	ruff check --fix .

format: ## Format code
	ruff format .

format-check: ## Verify formatting without changing files
	ruff format --check .

typecheck: ## Type checker
	mypy morel/

build: ## Build the package
	python -m build

audit-artifact: build ## Install and import-test the exact wheel artifact
	@tmp=$$(mktemp -d) && trap 'rm -rf "$$tmp"' EXIT && \
	wheel=$$(ls -t dist/*.whl | head -n 1) && \
	python -m pip install --disable-pip-version-check --quiet --no-deps --target "$$tmp" "$$wheel" && \
	PYTHONPATH="$$tmp:$${PYTHONPATH:-}" python -c 'from importlib.metadata import distribution; import morel; dist = distribution("morel"); assert any(entry.name == "morel" and entry.value == "morel.cli:main" for entry in dist.entry_points), "missing console entry point"; assert morel.__version__ != "0.0.0+unknown", "version metadata was not embedded"; print(f"verified wheel {dist.version}")'

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

demo: ## Run the demo script
	python examples/demo.py

bench: ## Run benchmarks
	pytest benchmarks/ --benchmark-only --benchmark-min-rounds=20

serve: ## Run the inference server
	python -m morel serve --host 0.0.0.0 --port 8080

serve-workers-smoke: ## Verify the local two-worker serving lifecycle
	python scripts/serve_workers_smoke.py

serve-model-smoke: ## Verify model-backed two-worker inference
	python scripts/serve_model_smoke.py

serve-soak: ## Run the bounded concurrent two-worker HTTP soak gate
	python scripts/serve_soak.py

fault-injection: ## Exercise loader, HTTP, updater, and checkpoint failure paths
	pytest -q --no-cov tests/unit/serve/serve.py tests/unit/serve/updater.py tests/unit/train/checkpoint.py tests/property/http.py tests/property/checkpoint.py -k 'factory_failure or factory_timeout or build_capacity or interrupt or hides_internal_error or update_is_atomic or feedback or payload or schema or malformed'

reproduce: ## Run end-to-end reproduction
	python -m morel train completion

fidelity: ## Render the fidelity report
	python -m morel render-fidelity docs/FIDELITY.md docs/FIDELITY.json

docs: ## Build documentation
	mkdocs build --strict

docs-check: ## Verify documentation examples use the current public API
	python scripts/check_docs.py

lock: ## Regenerate requirements.lock (hash-pinned, targets the CI platform)
	uv pip compile pyproject.toml --extra serve \
		--python-platform linux --python-version 3.11 \
		--generate-hashes --upgrade -o requirements.lock

lock-check: ## Fail if requirements.lock is out of date with pyproject.toml
	@tmp=$$(mktemp) && trap 'rm -f "$$tmp"' EXIT && \
	uv pip compile pyproject.toml --extra serve \
		--python-platform linux --python-version 3.11 \
		--generate-hashes --upgrade 2>/dev/null | grep -v '^#' > "$$tmp" && \
	grep -v '^#' requirements.lock | diff -u - "$$tmp" \
		&& echo "requirements.lock is up to date"

check: lint test ## Run lint and tests

site: ## Build the product site
	cd site && pnpm build

site-test: ## Run the root-hosted product-site browser contract suite
	cd site && pnpm test:e2e --project=chromium

site-unit-test: ## Run product-site unit tests
	cd site && pnpm test:unit

site-pages-test: ## Run the product-site suite against the GitHub Pages base path
	cd site && GITHUB_PAGES=1 pnpm build && BASE_URL=http://127.0.0.1:4173/morel/ pnpm exec playwright test --project=chromium

audit-python: lint format-check typecheck test audit-artifact ## Run Python quality and package gates
	pip install --disable-pip-version-check --quiet twine pip-audit
	twine check dist/*
	pip-audit --strict --disable-pip --requirement requirements.lock

audit-critical: ## Enforce coverage floors for critical runtime subsystems
	python -m coverage erase
	python -m coverage run -m pytest tests/unit/serve --no-cov
	python -m coverage report --include='morel/serve/*' --fail-under=70
	python -m coverage erase
	python -m coverage run -m pytest tests/unit/pipeline --no-cov
	python -m coverage report --include='morel/pipeline/*' --fail-under=70
	python -m coverage erase
	python -m coverage run -m pytest tests/unit/cli --no-cov
	python -m coverage report --include='morel/cli/*' --fail-under=70
	python -m coverage erase
	python -m coverage run -m pytest tests/unit/train/checkpoint.py --no-cov
	python -m coverage report --include='morel/train/checkpoint.py' --fail-under=70

audit: audit-python audit-critical docs-check fault-injection serve-workers-smoke serve-model-smoke serve-soak site site-unit-test site-test site-pages-test ## Run the local release-quality audit

check-urls: ## Fail CI if any tracked file references the legacy repo URL
	@if grep -rln 'robust-multimodal-recommendation' \
	    --include='*.md' --include='*.toml' --include='*.yml' --include='*.yaml' \
	    --include='*.cff' --include='*.py' --include='*.txt' --include='*.cfg' \
	    --include='*.json' . 2>/dev/null | grep -v -E '\.git/|site/' | grep -v '^./requirements.lock' >/dev/null; then \
	    echo "tracked files reference the legacy 'robust-multimodal-recommendation' URL:"; \
	    grep -rln 'robust-multimodal-recommendation' \
	        --include='*.md' --include='*.toml' --include='*.yml' --include='*.yaml' \
	        --include='*.cff' --include='*.py' --include='*.txt' --include='*.cfg' \
	        --include='*.json' . 2>/dev/null | grep -v -E '\.git/|site/' | grep -v '^./requirements.lock'; \
	    exit 1; \
	fi
	@echo "all references point at the canonical morel repo"

verify-metrics: ## Verify audit, docs, and site metrics match the latest test report
	python scripts/check_verification.py
