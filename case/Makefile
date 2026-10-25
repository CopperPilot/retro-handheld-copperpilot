# ==============================================================================
# CopperPilot Retro Handheld 3D Snap-Fit Enclosure - Generation & Verification Makefile
# ==============================================================================

UV            := $(shell command -v uv 2>/dev/null || echo "$$HOME/.local/bin/uv")
ifneq ($(wildcard $(UV)),)
PYTHON        ?= $(UV) run --with trimesh --with numpy --with matplotlib --with Pillow python
PYTEST        ?= $(UV) run --with pytest --with trimesh --with numpy --with scipy --with networkx --with rtree --with manifold3d --with python-fcl pytest
else
PYTHON        ?= python3
PYTEST        ?= $(shell if python3 -m pytest --version >/dev/null 2>&1; then echo "python3 -m pytest"; else echo "pytest"; fi)
endif

MODELS_DIR    := models
RENDERS_DIR   := renders

.PHONY: all help generate render test fmt fmt-check lint clean

all: generate test

help:
	@echo "CopperPilot Retro Handheld Enclosure (case/) Targets:"
	@echo "  make generate  - Synthesize parametric 3D CAD models (front bezel, rear shell, door, buttons)"
	@echo "  make render    - Render 4K isometric, front, rear, and exploded visual projections"
	@echo "  make test      - Run automated 15-point PyTest enclosure verification suite"
	@echo "  make fmt       - Format Python source and test code with ruff"
	@echo "  make fmt-check - Non-destructive formatting compliance check"
	@echo "  make lint      - Run static analysis and linting with ruff"
	@echo "  make clean     - Remove generated meshes, temporary files, and test caches"

$(MODELS_DIR):
	@mkdir -p $(MODELS_DIR)

$(RENDERS_DIR):
	@mkdir -p $(RENDERS_DIR)

generate: $(MODELS_DIR)
	@echo "==> Synthesizing parametric 3D enclosure CAD models..."
	@$(PYTHON) generate_case.py

render: $(RENDERS_DIR)
	@echo "==> Rendering 3D enclosure visualization projections..."
	@$(PYTHON) render_case.py

test:
	@echo "==> Running automated enclosure test suite with PyTest..."
	@$(PYTEST) ../tests/test_case.py -v

fmt:
	@echo "==> Formatting case Python sources..."
	@if command -v ruff > /dev/null; then \
		ruff format generate_case.py render_case.py; \
	elif [ -n "$(wildcard $(UV))" ]; then \
		$(UV) run --with ruff ruff format generate_case.py render_case.py; \
	else \
		echo "Notice: ruff not installed. Skipping Python formatting."; \
	fi

fmt-check:
	@echo "==> Checking case Python formatting compliance..."
	@if command -v ruff > /dev/null; then \
		ruff format --check generate_case.py render_case.py; \
	elif [ -n "$(wildcard $(UV))" ]; then \
		$(UV) run --with ruff ruff format --check generate_case.py render_case.py; \
	else \
		echo "Notice: ruff not installed. Skipping Python format check."; \
	fi

lint:
	@echo "==> Running case Python static analysis..."
	@if command -v ruff > /dev/null; then \
		ruff check generate_case.py render_case.py; \
	elif [ -n "$(wildcard $(UV))" ]; then \
		$(UV) run --with ruff ruff check generate_case.py render_case.py; \
	else \
		echo "Notice: ruff not installed. Skipping Python linting."; \
	fi

clean:
	@rm -rf __pycache__ .pytest_cache
	@echo "Case build artifacts and test caches cleaned."
