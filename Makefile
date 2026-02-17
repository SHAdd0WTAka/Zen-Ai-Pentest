.PHONY: test coverage coverage-html coverage-xml clean install setup help

help:
	@echo "Verfügbare Befehle:"
	@echo "  make test          - Tests ausführen"
	@echo "  make coverage      - Coverage Report (Terminal)"
	@echo "  make coverage-xml  - Coverage XML für VS Code"
	@echo "  make coverage-html - Coverage HTML Report"
	@echo "  make open-coverage - Coverage im Browser öffnen"
	@echo "  make install       - Dependencies installieren"
	@echo "  make setup         - Alles einrichten"
	@echo "  make clean         - Cache-Dateien löschen"

test:
	pytest tests/test_working_final.py -v

coverage:
	pytest tests/test_working_final.py \
		--cov=core.orchestrator \
		--cov=database.models \
		-v

coverage-xml:
	pytest tests/test_working_final.py \
		--cov=core.orchestrator \
		--cov=database.models \
		--cov=tools.ffuf_integration_enhanced \
		--cov=tools.whatweb_integration \
		--cov=tools.wafw00f_integration \
		--cov=tools.subfinder_integration \
		--cov=tools.httpx_integration \
		--cov=tools.nikto_integration \
		--cov=tools.sherlock_integration \
		--cov=tools.ignorant_integration \
		--cov=tools.tshark_integration \
		--cov=tools.amass_integration \
		--cov=tools.masscan_integration \
		--cov=tools.gobuster_integration \
		--cov=tools.nmap_integration \
		--cov=modules.super_scanner \
		--cov=agents.agent_base \
		--cov=agents.agent_orchestrator \
		--cov=autonomous.agent_loop \
		--cov=autonomous.exploit_validator \
		--cov-report=xml:coverage.xml \
		-v
	@echo "✓ coverage.xml erstellt!"

coverage-html:
	pytest tests/test_working_final.py \
		--cov=core.orchestrator \
		--cov=database.models \
		--cov=tools.ffuf_integration_enhanced \
		--cov=tools.whatweb_integration \
		--cov=tools.wafw00f_integration \
		--cov=tools.subfinder_integration \
		--cov=tools.httpx_integration \
		--cov=tools.nikto_integration \
		--cov=tools.sherlock_integration \
		--cov=tools.ignorant_integration \
		--cov=tools.tshark_integration \
		--cov=tools.amass_integration \
		--cov=tools.masscan_integration \
		--cov=tools.gobuster_integration \
		--cov=tools.nmap_integration \
		--cov=modules.super_scanner \
		--cov=agents.agent_base \
		--cov=agents.agent_orchestrator \
		--cov=autonomous.agent_loop \
		--cov=autonomous.exploit_validator \
		--cov-report=html:htmlcov \
		-v
	@echo "✓ HTML Report erstellt in htmlcov/"

open-coverage:
	python -m webbrowser htmlcov/index.html

install:
	pip install -r requirements.txt
	pip install pytest pytest-cov black isort pre-commit
	pre-commit install

setup: install
	@echo "✓ Setup abgeschlossen!"
	@echo ""
	@echo "Nächste Schritte:"
	@echo "  1. VS Code öffnen"
	@echo "  2. Extensions installieren (siehe VS_CODE_SETUP.md)"
	@echo "  3. make coverage-xml"
	@echo "  4. Coverage Gutters: Watch aktivieren"

clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage coverage.xml
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete
	@echo "✓ Aufgeräumt!"
