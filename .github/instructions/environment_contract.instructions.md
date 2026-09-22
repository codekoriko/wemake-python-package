---
description: "Use when: writing or updating Python files."
applyTo: "**/*.py"
---

# Environment Contract

## Technical Stack

- **Language:** Python {{cookiecutter.python_version}}
- **Task Runner:** `poethepoet` (poe)

## Environment Setup

The `wemake-python` conda environment activates automatically.

## Testing

- Run tests: `poe test-agent`

## Code Quality Contract

- Full validation: `poe check-all`
- Linting:
  1. `poe py-lint-ruff`
  2. `poe py-lint-flake8`
- Type checking:
  1. `poe type-check-mypy`
  2. `poe type-check-pyright`
