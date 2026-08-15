# Contributing to `logic-prover`

Thank you for your interest in contributing to **`logic-prover`**! We welcome contributions of all kinds, including bug reports, documentation improvements, feature requests, new logical theories/axioms, and performance optimizations.

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.

---

## Getting Started

### Prerequisites

- **Python**: Version `3.10` or higher.
- **Git**: For version control.
- **C Compiler (Optional)**: GCC, Clang, or MSVC if compiling optional native Cython extensions for maximum performance. Pure Python fallback is supported if a compiler is not available.

### Repository Setup

1. **Fork and clone** the repository:
   ```bash
   git clone https://github.com/<your-username>/logic.git
   cd logic
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install the package in editable mode with development dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev,vis]"
   ```

4. **(Optional) Build Cython C extensions locally**:
   ```bash
   python setup.py build_ext --inplace
   ```

---

## Development Workflow

### Branching Strategy

- Create a descriptive branch from `main` for your work:
  ```bash
  git checkout -b feature/add-tableau-prover
  # or
  git checkout -b fix/parser-associativity
  ```

### Code Style & Formatting

We maintain code quality using modern Python tooling:

- **Linter & Formatter**: [`ruff`](https://docs.astral.sh/ruff/)
  ```bash
  # Check for lint issues
  ruff check .

  # Auto-fix lint issues
  ruff check --fix .

  # Check code formatting
  ruff format --check .
  ```

- **Type Checker**: [`mypy`](http://mypy-lang.org/)
  ```bash
  mypy logic_prover
  ```

- **Docstrings**: We use Google-style docstrings with clear parameter, return, and exception descriptions.

---

## Testing

We use [`pytest`](https://docs.pytest.org/) and [`hypothesis`](https://hypothesis.readthedocs.io/) for unit and property-based testing.

### Running Tests

```bash
# Run all tests with coverage report
pytest

# Run a specific test module
pytest tests/test_prover.py

# Run only fast tests (skip slow solvers)
pytest -m "not slow"
```

### Coverage Requirement

New contributions should maintain or improve our branch test coverage (>85%). When adding a new feature or fixing a bug, please include corresponding unit tests in the `tests/` directory.

---

## Documentation

API documentation is generated from source code docstrings and reflection:

```bash
# Generate markdown documentation into docs/
python -m logic_prover docs --output-dir docs
```

When you add new classes, methods, or public functions, ensure they include comprehensive docstrings so that the automated documentation generator captures them accurately.

---

## Commit Guidelines

We encourage clear and structured commit messages following [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: ...` for new features or capabilities
- `fix: ...` for bug fixes
- `perf: ...` for performance optimizations
- `docs: ...` for documentation changes
- `refactor: ...` for code refactoring without behavior changes
- `test: ...` for adding or improving tests
- `chore: ...` for build scripts, dependencies, or maintenance

---

## Submitting a Pull Request

1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a Pull Request on GitHub targeting the `main` branch.
3. Fill out the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) with details on what you changed and why.
4. Ensure all CI tests, linter checks, and documentation checks pass.
5. Address any review feedback promptly.

Thank you for contributing to the logic-prover ecosystem!
