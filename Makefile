# ==============================================================================
# GKD Pixel ESP32-S3 Handheld Console - Unified Root Build & Verification Makefile
# ==============================================================================

PROJECT_NAME := gameboy-copperpilot
PCB_FILE     := $(PROJECT_NAME).kicad_pcb
SCH_FILE     := $(PROJECT_NAME).kicad_sch
PRO_FILE     := $(PROJECT_NAME).kicad_pro
BUILD_DIR    := build
GERBER_DIR   := $(BUILD_DIR)/gerbers
RELEASE_ZIP  := $(BUILD_DIR)/$(PROJECT_NAME)_LionCircuits_Release.zip

UV           := $(shell command -v uv 2>/dev/null || echo "$$HOME/.local/bin/uv")
ifneq ($(wildcard $(UV)),)
PYTHON       ?= $(UV) run --with pytest --with trimesh --with numpy --with matplotlib --with Pillow python
PYTEST       ?= $(UV) run --with pytest --with trimesh --with numpy pytest
else
PYTHON       ?= python3
PYTEST       ?= $(shell if python3 -m pytest --version >/dev/null 2>&1; then echo "python3 -m pytest"; else echo "pytest"; fi)
endif

KICAD_CLI    := kicad-cli

.PHONY: all help erc drc lint test test-pcb test-case gerbers drill zip-gerbers pos cpl bom d356 pdf spec fab bundle build-case render-case clean distclean

# Default target executes automated hardware and mechanical test suites
all: test drc erc

help:
	@echo "======================================================================"
	@echo "GKD Pixel ESP32-S3 Handheld Console - Build & Verification System"
	@echo "======================================================================"
	@echo "Verification Targets:"
	@echo "  make test        - Run full 35-point automated test suite (PyTest PCB + 3D Enclosure)"
	@echo "  make test-pcb    - Run 25-point automated PCB hardware verification suite"
	@echo "  make test-case   - Run 15-point automated 3D mechanical enclosure suite"
	@echo "  make drc         - Run KiCad CLI Design Rule Check on PCB layout (asserts 0 errors, 100% routed)"
	@echo "  make erc         - Run KiCad CLI Electrical Rule Check on schematic (asserts 0 errors)"
	@echo "  make lint        - Run DRC, ERC, and structural design checks"
	@echo ""
	@echo "Manufacturing & Release Targets (Lion Circuits 4-Layer Turnkey PCBA):"
	@echo "  make fab         - Package complete release zip (Gerbers, Drill, CPL, BOM, D356, PDFs, SPEC)"
	@echo "  make gerbers     - Export 4-layer RS-274X Gerbers for Lion Circuits"
	@echo "  make drill       - Export Excellon NC drill files (plated + non-plated)"
	@echo "  make zip-gerbers - Package Gerbers and drill files into zip archive"
	@echo "  make pos / cpl   - Export SMT pick-and-place component centroid file (CPL/POS)"
	@echo "  make bom         - Export structured Bill of Materials with 100% verified MPN mapping"
	@echo "  make d356        - Export IPC-D-356 electrical test netlist"
	@echo "  make pdf         - Export schematic and multi-layer PCB assembly PDFs"
	@echo "  make spec        - Generate Lion Circuits ORDER_SPEC.md manufacturing specification"
	@echo ""
	@echo "3D Enclosure CAD Targets:"
	@echo "  make build-case  - Synthesize parametric 3D snap-fit enclosure CAD models (STLs)"
	@echo "  make render-case - Render 4K multi-view isometric, exploded, front, and rear projections"
	@echo ""
	@echo "Housekeeping:"
	@echo "  make clean       - Remove intermediate build outputs, temporary reports, and test caches"
	@echo "  make distclean   - Deep clean removing build directory and virtual caches"

$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)
	@mkdir -p $(GERBER_DIR)

# ------------------------------------------------------------------------------
# Hardware Verification
# ------------------------------------------------------------------------------
erc: $(BUILD_DIR)
	@echo "==> Running KiCad Electrical Rule Check (ERC)..."
	@$(KICAD_CLI) sch erc --format json -o $(BUILD_DIR)/erc_report.json $(SCH_FILE) > /dev/null
	@python3 -c "import json, sys; \
		data = json.load(open('$(BUILD_DIR)/erc_report.json')); \
		errors = [v for s in data.get('sheets', []) for v in s.get('violations', []) if v.get('severity') == 'error']; \
		print(f'ERC Results: {len(errors)} errors'); \
		sys.exit(1 if errors else 0)"
	@rm -f $(BUILD_DIR)/erc_report.json
	@echo "ERC Clean: 0 errors."

drc: $(BUILD_DIR)
	@echo "==> Running KiCad Design Rule Check (DRC)..."
	@$(KICAD_CLI) pcb drc --format json --refill-zones -o $(BUILD_DIR)/drc_report.json $(PCB_FILE) > /dev/null
	@python3 -c "import json, sys; \
		data = json.load(open('$(BUILD_DIR)/drc_report.json')); \
		errors = [v for v in data.get('violations', []) if v.get('severity') == 'error']; \
		unconnected = data.get('unconnected_items', []); \
		print(f'DRC Results: {len(errors)} errors, {len(unconnected)} unconnected items'); \
		sys.exit(1 if (errors or unconnected) else 0)"
	@rm -f $(BUILD_DIR)/drc_report.json
	@echo "DRC Clean: 0 errors, 0 unconnected items (100% routed)."

lint: erc drc

test:
	@echo "==> Running full automated test suite (PyTest)..."
	@$(PYTEST) tests/ -v

test-pcb:
	@echo "==> Running automated PCB hardware test suite..."
	@$(PYTEST) tests/test_pcb.py -v

test-case:
	@echo "==> Running automated 3D enclosure test suite..."
	@$(PYTEST) tests/test_case.py -v

# ------------------------------------------------------------------------------
# Manufacturing & Fabrication Release
# ------------------------------------------------------------------------------
gerbers: $(BUILD_DIR)
	@python3 export_manufacturing.py --gerbers

drill: $(BUILD_DIR)
	@python3 export_manufacturing.py --drill

zip-gerbers: $(BUILD_DIR)
	@python3 export_manufacturing.py --zip-gerbers

pos: $(BUILD_DIR)
	@python3 export_manufacturing.py --cpl

cpl: pos

bom: $(BUILD_DIR)
	@python3 export_manufacturing.py --bom

d356: $(BUILD_DIR)
	@python3 export_manufacturing.py --d356

pdf: $(BUILD_DIR)
	@python3 export_manufacturing.py --pdf

spec: $(BUILD_DIR)
	@python3 export_manufacturing.py --spec

fab: $(BUILD_DIR)
	@echo "==> Packaging complete turnkey manufacturing release bundle for Lion Circuits..."
	@python3 export_manufacturing.py --all

bundle: fab

# ------------------------------------------------------------------------------
# 3D Enclosure CAD
# ------------------------------------------------------------------------------
build-case:
	@$(MAKE) -C case generate

render-case:
	@$(MAKE) -C case render

# ------------------------------------------------------------------------------
# Cleaning
# ------------------------------------------------------------------------------
clean:
	@rm -rf $(BUILD_DIR) .pytest_cache tests/__pycache__ *.json *.rpt
	@$(MAKE) -C case clean
	@echo "Workspace cleaned."

distclean: clean
	@rm -rf build .pytest_cache tests/.pytest_cache case/.pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
	@echo "Distclean complete: all caches, temporaries, and generated files removed."
