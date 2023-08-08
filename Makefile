.PHONY: format test lint

format:
	find chaosterraform -type f -name '*.py' | xargs isort
	find chaosterraform -type f -name '*.py' | xargs black

test:
	pytest -v tests/

lint:
	pylint chaosterraform/
