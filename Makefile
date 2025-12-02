.PHONY: help install install-dev lint format type-check test clean run-gcmap run-mpl fetch-realtime realtime-demo notebook example

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package and dependencies
	pip install -e .

install-dev:  ## Install package with development dependencies
	pip install -e ".[dev,notebook]"
	pre-commit install

lint:  ## Run linting checks
	ruff check .

format:  ## Format code with black and fix linting issues
	black .
	ruff check . --fix

type-check:  ## Run type checking with mypy
	mypy plot_gcmap.py plot_mpl.py --ignore-missing-imports

test:  ## Run tests
	python -c "import plot_gcmap; import plot_mpl"
	python plot_gcmap.py --help
	python plot_mpl.py --help

clean:  ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -f .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-gcmap:  ## Generate map with GCMapper
	python plot_gcmap.py -v

run-mpl:  ## Generate map with Matplotlib
	python plot_mpl.py -v

fetch-realtime:  ## Fetch current flights from ADS-B Exchange
	python fetch_flights.py -o realtime.csv --min-flights 2 -v

track-flight:  ## Track a specific flight (e.g., make track-flight FLIGHT=UA262)
	python track_flight_opensky.py $(FLIGHT) -v

visualize:  ## Visualize a flight track CSV (e.g., make visualize FILE=example_ual2212_track.csv)
	python visualize_track_simple.py $(FILE) -o $(FILE:.csv=_analysis.png)

realtime-demo:  ## Run complete real-time workflow demo
	python realtime_example.py

notebook:  ## Start Jupyter notebook
	jupyter notebook notebooks/flight_analysis_tutorial.ipynb

example:  ## Run advanced usage example
	python example_advanced_usage.py

pre-commit:  ## Run pre-commit hooks on all files
	pre-commit run --all-files

check: lint type-check test  ## Run all checks
	@echo "All checks passed!"

all: format check  ## Format code and run all checks
	@echo "Code formatted and all checks passed!"
