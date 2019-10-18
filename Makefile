clean: ## Clean local environment
	@find . -name "*.pyc" | xargs rm -rf
	@find . -name "*.pyo" | xargs rm -rf
	@find . -name "__pycache__" -type d | xargs rm -rf
	@rm -f .coverage
	@rm -rf htmlcov/
	@rm -f coverage.xml
	@rm -f *.log

test: clean ## Run tests
	@py.test -x -p no:sugar tests/

requirements-dev: ## Install development dependencies
	@pip install -U -r requirements.txt

run:
	@python rastreiobot.py
