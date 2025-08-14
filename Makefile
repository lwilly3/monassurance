PYTEST=python -m pytest
RUFF=python -m ruff
MYPY=python -m mypy
BANDIT=python -m bandit
COV_FILE=coverage.xml
BADGE=coverage_badge.svg
MIN_COVERAGE=73

.PHONY: test test-reports test-fast lint lint-fix format type check qa coverage badge grafana-import security security-strict

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

# B4 - CI strict: lint + type + coverage strict
check-strict: lint type test coverage-check

check: lint type test

qa: format lint-fix type test

coverage:
	$(PYTEST) --cov=backend --cov-report=xml:$(COV_FILE) --cov-report=term

coverage-check: coverage
	@echo "Vérification coverage >= $(MIN_COVERAGE)%"
	@python -c "import xml.etree.ElementTree as ET; root=ET.parse('$(COV_FILE)').getroot(); cov=float(root.attrib['line-rate'])*100; print(f'Coverage: {cov:.1f}%'); exit(0 if cov >= $(MIN_COVERAGE) else 1)"

badge: coverage
	@python scripts/gen_coverage_badge.py $(COV_FILE) $(BADGE) || echo "(TODO) Génération badge à implémenter"
	@echo "Badge (placeholder) -> $(BADGE)"

security:
	@command -v bandit >/dev/null 2>&1 || { echo 'Bandit non installé (pip install bandit)'; exit 1; }
	$(BANDIT) -q -r backend || true

security-strict:	## Analyse de sécurité stricte avec rapport JSON pour CI
	python -m bandit -r backend -f json -o bandit-report.json --skip B101,B601,B110

grafana-import:
	@python scripts/import_grafana_dashboard.py docs/grafana_dashboard_example.json || echo "Voir script pour détails"
