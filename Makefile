PYTEST=pytest
RUFF=ruff
MYPY=mypy
COV_FILE=coverage.xml
BADGE=coverage_badge.svg

.PHONY: test test-reports test-fast lint lint-fix format type check qa coverage badge grafana-import security

test:
	$(PYTEST) -q

test-reports:
	$(PYTEST) -q tests/test_reports_*.py

test-fast:
	$(PYTEST) -q -k reports

lint:
	$(RUFF) check .

lint-fix:
	$(RUFF) check . --fix

format:
	$(RUFF) format .

type:
	$(MYPY) backend

check: lint type test

coverage:
	$(PYTEST) --cov=backend --cov-report=xml:$(COV_FILE) --cov-report=term
	@echo "Coverage XML généré: $(COV_FILE)"

badge: coverage
	@python scripts/gen_coverage_badge.py $(COV_FILE) $(BADGE) || echo "(TODO) Génération badge à implémenter"
	@echo "Badge (placeholder) -> $(BADGE)"

security:
	@command -v bandit >/dev/null 2>&1 || { echo 'Bandit non installé (pip install bandit)'; exit 1; }
	bandit -q -r backend || true

grafana-import:
	@python scripts/import_grafana_dashboard.py docs/grafana_dashboard_example.json || echo "Voir script pour détails"
