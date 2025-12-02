# Contributing to Flights Analysis

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A GitHub account

### Setting Up Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/flights-analysis.git
   cd flights-analysis
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## 🔧 Development Workflow

### Code Style

This project follows modern Python best practices:

- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **MyPy** for type checking
- **Pre-commit hooks** enforce these automatically

### Running Checks Locally

Before committing, run these checks:

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check . --fix

# Type check with MyPy
mypy plot_gcmap.py plot_mpl.py --ignore-missing-imports
```

Or let pre-commit handle it:
```bash
pre-commit run --all-files
```

### Testing

Currently, the project includes:
- Import verification tests
- CI/CD pipeline validation
- Cross-platform compatibility tests

To test manually:
```bash
# Test imports
python -c "import plot_gcmap; import plot_mpl"

# Test CLI
python plot_gcmap.py --help
python plot_mpl.py --help
```

## 📝 Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-projection`
- `fix/color-gradient-bug`
- `docs/update-readme`
- `refactor/improve-performance`

### Commit Messages

Follow conventional commits format:
```
type(scope): brief description

Longer explanation if needed

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(cli): add support for custom projections
fix(visualization): correct color scaling for print mode
docs(readme): add CLI usage examples
```

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit:**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

3. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a Pull Request:**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template with details about your changes

5. **Wait for review:**
   - Address any feedback from maintainers
   - CI checks must pass before merging

## 🎯 What to Contribute

### Good First Issues

- Documentation improvements
- Adding new color schemes
- Example notebooks for specific regions
- Bug fixes
- Performance optimizations

### Feature Ideas

- Support for additional map projections
- Interactive web-based visualizations
- Data validation and cleaning tools
- Animation support for time-series data
- Additional output formats (SVG, PDF)
- Route clustering and analysis

### Documentation

- Tutorial improvements
- Additional examples
- API documentation
- Video tutorials
- Blog posts about usage

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Minimal code to reproduce the bug
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**:
   - Python version
   - Operating system
   - Package versions (`pip list`)
6. **Screenshots**: If applicable

## 💡 Suggesting Features

When suggesting features:

1. **Use case**: Describe the problem or use case
2. **Proposed solution**: Your idea for solving it
3. **Alternatives**: Other approaches you've considered
4. **Additional context**: Mockups, examples, references

## 📦 Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a new release on GitHub
4. CI will automatically publish to PyPI (when configured)

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information

## 📧 Contact

- GitHub Issues: For bugs and feature requests
- Discussions: For questions and general discussion

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Flights Analysis! 🎉
