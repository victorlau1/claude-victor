# Claude-Victor Makefile
# Cross-platform automation for installation, testing, and verification

.PHONY: all install setup-python setup-dev configure-gh configure-mcp configure-plugin \
        test-unit test-integration test-bdd test-all verify clean help

# Detect OS and set commands accordingly
ifeq ($(OS),Windows_NT)
    include Makefile.windows
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        INSTALL_GH = brew install gh
        PYTHON = python3
        PIP = pip3
    else ifeq ($(UNAME_S),Linux)
        INSTALL_GH = sudo apt-get install -y gh || sudo dnf install -y gh
        PYTHON = python3
        PIP = pip3
    endif
    RM = rm -rf
    MKDIR = mkdir -p
    SEP = /
endif

# Default target
all: help

# Install GitHub CLI
install:
	@echo "Installing GitHub CLI..."
	@which gh > /dev/null 2>&1 || $(INSTALL_GH)
	@echo "GitHub CLI installed successfully"

# Install Python runtime dependencies
setup-python:
	@echo "Installing Python dependencies..."
	$(PIP) install -r requirements.txt
	@echo "Runtime dependencies installed"

# Install development dependencies
setup-dev: setup-python
	@echo "Installing development dependencies..."
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .
	@echo "Development environment ready"

# Configure GitHub CLI authentication
configure-gh:
	@echo "Configuring GitHub CLI..."
	@gh auth status || gh auth login
	@echo "GitHub CLI configured"

# Configure memory-keeper MCP
configure-mcp:
	@echo "Memory-keeper MCP configuration..."
	@echo "Note: memory-keeper MCP should be configured in Claude Code settings"
	@echo "See mcp/memory-keeper.json for reference"

# Configure Claude Code plugin (adds local marketplace to known_marketplaces.json)
configure-plugin:
	@$(PYTHON) scripts/configure_plugin.py
	@echo ""
	@echo "To complete installation:"
	@echo "  1. Restart Claude Code"
	@echo "  2. Run: /plugin install claude-victor@local"

# Run unit tests
test-unit:
	@echo "Running unit tests..."
	$(PYTHON) -m pytest tests/unit -v --tb=short
	@echo "Unit tests complete"

# Run integration tests
test-integration:
	@echo "Running integration tests..."
	$(PYTHON) -m pytest tests/integration -v --tb=short -m integration
	@echo "Integration tests complete"

# Run BDD tests
test-bdd:
	@echo "Running BDD tests..."
	$(PYTHON) -m behave tests/bdd/features
	@echo "BDD tests complete"

# Run all tests
test-all: test-unit test-integration test-bdd
	@echo "All tests complete"

# Verify all artifacts exist and work
verify:
	@echo "Running verification checks..."
	@PASS=0; FAIL=0; \
	check() { \
		if eval "$$1" > /dev/null 2>&1; then \
			echo "✓ $$2"; \
			PASS=$$((PASS + 1)); \
		else \
			echo "✗ $$2"; \
			FAIL=$$((FAIL + 1)); \
		fi; \
	}; \
	check "test -f Makefile" "Makefile exists"; \
	check "test -f pyproject.toml" "pyproject.toml exists"; \
	check "test -d src/claude_victor" "Source directory exists"; \
	check "test -d tests/unit" "Unit tests directory exists"; \
	check "test -d tests/bdd/features" "BDD features directory exists"; \
	check "test -f .claude-plugin/plugin.json" "Plugin manifest exists"; \
	check "$(PYTHON) -c 'import claude_victor'" "Package importable"; \
	check "which gh" "GitHub CLI available"; \
	echo ""; \
	echo "Verification complete"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	$(RM) build/
	$(RM) dist/
	$(RM) *.egg-info/
	$(RM) src/*.egg-info/
	$(RM) .pytest_cache/
	$(RM) .coverage
	$(RM) htmlcov/
	$(RM) reports/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"

# Show help
help:
	@echo "Claude-Victor Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install         Install GitHub CLI"
	@echo "  setup-python    Install Python runtime dependencies"
	@echo "  setup-dev       Install development dependencies"
	@echo "  configure-gh    Configure GitHub CLI authentication"
	@echo "  configure-mcp   Show memory-keeper MCP configuration info"
	@echo "  configure-plugin Add local marketplace to Claude Code settings"
	@echo "  test-unit       Run unit tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-bdd        Run BDD tests"
	@echo "  test-all        Run all tests"
	@echo "  verify          Verify all artifacts exist"
	@echo "  clean           Remove build artifacts"
	@echo "  help            Show this help message"
