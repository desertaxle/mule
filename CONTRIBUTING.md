# Contributing to Mule

Thank you for your interest in contributing to Mule! We welcome contributions of all kinds, from bug reports and feature requests to code improvements and documentation updates.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management

### Setting Up Your Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/mule.git
   cd mule
   ```

2. **Install dependencies**
   ```bash
   uv sync --dev
   ```

3. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

4. **Verify your setup**
   ```bash
   uv run pytest
   uv run ruff check
   uv run pyright
   ```

## 🧪 Development Workflow

### Running Tests

Run the full test suite:
```bash
uv run pytest
```

Run tests with coverage:
```bash
uv run pytest --cov=mule --cov-report=html
```

Run tests in watch mode during development:
```bash
uv run ptw --now .
```

### Code Quality

We use several tools to maintain code quality:

- **Ruff** for linting and formatting:
  ```bash
  uv run ruff check          # Check for issues
  uv run ruff format         # Format code
  uv run ruff check --fix    # Auto-fix issues
  ```

- **Pyright** for type checking:
  ```bash
  uv run pyright
  ```

- **Pre-commit** runs all checks automatically:
  ```bash
  uv run pre-commit run --all-files
  ```