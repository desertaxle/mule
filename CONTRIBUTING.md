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
uv run pytest-watcher
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

### Project Structure

```
mule/
├── mule/                    # Main package
│   ├── __init__.py         # Public API exports
│   ├── _retry.py           # Core retry decorator
│   ├── stop_conditions.py  # Built-in stop conditions
│   └── _attempts/          # Attempt handling
│       ├── __init__.py
│       ├── sync.py         # Sync attempt generators
│       ├── aio.py          # Async attempt generators
│       ├── dataclasses.py  # AttemptState and Phase
│       └── protocols.py    # Type protocols
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
└── README.md              # Documentation
```

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Clear description** of the problem
2. **Minimal reproduction case** - the smallest code that demonstrates the issue
3. **Expected vs actual behavior**
4. **Environment details** (Python version, operating system)
5. **Mule version** where the bug occurs

**Template:**
```markdown
## Bug Description
Brief description of what's wrong.

## Reproduction Code
```python
from mule import retry

# Minimal code that reproduces the issue
```

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- Python version: 3.x.x
- Mule version: x.x.x
- Operating System: 
```

### Feature Requests

For feature requests, please include:

1. **Use case** - what problem does this solve?
2. **Proposed API** - how would it work?
3. **Alternatives considered** - other ways to solve the problem
4. **Backwards compatibility** - any breaking changes?

## 💡 Contributing Code

### Types of Contributions

We welcome:
- **Bug fixes** - Fix existing issues
- **New features** - Add new functionality
- **Performance improvements** - Make things faster
- **Documentation** - Improve docs and examples
- **Tests** - Increase test coverage

### Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with appropriate tests

3. **Ensure all checks pass**:
   ```bash
   uv run pytest                    # Tests pass
   uv run ruff check                # No linting errors
   uv run pyright                   # No type errors
   uv run pre-commit run --all-files # All hooks pass
   ```

4. **Write a clear commit message**:
   ```
   Add exponential backoff with jitter support
   
   - Implement jittered exponential backoff strategy
   - Add configuration for jitter percentage
   - Include comprehensive tests and documentation
   - Fixes #123
   ```

5. **Submit the pull request** with:
   - Clear title and description
   - Link to related issues
   - Screenshots/examples if applicable

### Code Style Guidelines

- **Follow existing patterns** in the codebase
- **Use type hints** for all public APIs
- **Write docstrings** for public functions and classes
- **Keep functions focused** - single responsibility
- **Prefer composition** over inheritance
- **Use descriptive names** for variables and functions

### Testing Guidelines

- **Write tests for new features** and bug fixes
- **Test both sync and async** code paths where applicable
- **Include edge cases** and error conditions
- **Use descriptive test names** that explain what's being tested
- **Keep tests focused** - one concept per test

**Example test structure:**
```python
class TestRetryDecorator:
    def test_successful_execution_returns_result(self):
        @retry(until=AttemptsExhausted(3))
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"

    def test_retries_on_exception_until_limit(self):
        attempts = 0
        
        @retry(until=AttemptsExhausted(3))
        def failing_func():
            nonlocal attempts
            attempts += 1
            raise Exception("fail")
        
        with pytest.raises(Exception):
            failing_func()
        
        assert attempts == 3
```

## 🏗️ Architecture Guidelines

### Core Principles

1. **Simplicity** - Keep the API simple and intuitive
2. **Flexibility** - Support diverse use cases without bloat
3. **Type Safety** - Full type coverage for better DX
4. **Performance** - Minimal overhead in hot paths
5. **Compatibility** - Support sync and async seamlessly

### Design Patterns

- **Protocol-based design** for extensibility
- **Context managers** for resource safety
- **Generator patterns** for lazy evaluation
- **Immutable data structures** where possible

### Adding New Features

When adding new features:

1. **Design the API first** - how will users interact with it?
2. **Consider backwards compatibility** - avoid breaking changes
3. **Think about both sync/async** - should it support both?
4. **Plan for extensibility** - how might users customize it?
5. **Document the design** - explain the approach in code comments

## 📚 Documentation

### README Updates

When adding features, update the README with:
- Clear examples showing the new functionality
- Proper imports and runnable code
- Explanation of when to use the feature

### Docstring Style

Use Google-style docstrings:

```python
def retry_function(attempts: int, wait: float) -> None:
    """Retry a function with specified parameters.
    
    Args:
        attempts: Maximum number of retry attempts.
        wait: Seconds to wait between attempts.
        
    Returns:
        None
        
    Raises:
        ValueError: If attempts is less than 1.
        
    Example:
        >>> retry_function(3, 1.0)
    """
```

## 🎯 Areas Where We Need Help

- **Performance optimization** - Make retry loops faster
- **More stop conditions** - Additional built-in conditions
- **Better error messages** - More helpful error reporting
- **Documentation examples** - Real-world use cases
- **Integration testing** - Testing with popular libraries
- **Benchmarking** - Performance comparisons

## ❓ Questions?

- **Open an issue** for questions about contributing
- **Check existing issues** to see if your question was already answered
- **Look at the test suite** for examples of how things work

## 🏆 Recognition

Contributors will be:
- Listed in the project's contributors section
- Mentioned in release notes for significant contributions
- Given credit in commit messages and pull requests

Thank you for helping make Mule better! 🫏