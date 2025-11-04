# 🤝 Contributing to FlyMind

Thank you for your interest in contributing to **FlyMind**! We welcome contributions from developers of all skill levels. This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Documentation](#documentation)

## 🤝 Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for containerized development)

### Quick Setup

```bash
# Fork and clone the repository
git clone https://github.com/AbdirahmanNomad/flymind.git
cd flymind

# Install dependencies
pip install -r api/requirements.txt

# Install Playwright browsers
playwright install chromium

# Start development servers
# Terminal 1: API
cd api && uvicorn api:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: Streamlit UI
streamlit run streamlit_app.py
```

## 💡 How to Contribute

### Types of Contributions

- **🐛 Bug Fixes**: Fix issues and improve stability
- **✨ New Features**: Add new functionality
- **📚 Documentation**: Improve docs, tutorials, examples
- **🧪 Testing**: Add or improve test coverage
- **🎨 UI/UX**: Enhance user interface and experience
- **🔧 DevOps**: Improve deployment, CI/CD, monitoring

### Finding Issues to Work On

1. Check [GitHub Issues](https://github.com/AbdirahmanNomad/flymind/issues) for open tasks
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on issues you'd like to work on to avoid duplicate work

## 🛠️ Development Setup

### Local Development Environment

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black api/ streamlit_app.py
```

### Docker Development

```bash
# Build development container
docker build -t flymind-dev -f api/Dockerfile.dev api/

# Run with hot reload
docker run -p 8001:8001 -v $(pwd):/app flymind-dev
```

### Environment Variables

Create a `.env` file in the `api/` directory:

```bash
# API Configuration
PORT=8001
ENVIRONMENT=development
APP_NAME=FlyMind

# Optional: AI API Keys for testing
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here

# Optional: External services
REDIS_URL=redis://localhost:6379
```

## 📝 Submitting Changes

### 1. Create a Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 2. Make Your Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add: Brief description of your changes

- More detailed explanation
- What problem this solves
- Any breaking changes"
```

### 4. Push and Create Pull Request

```bash
# Push your branch
git push origin your-branch-name

# Create a Pull Request on GitHub
# - Go to your fork on GitHub
# - Click "Compare & pull request"
# - Fill out the PR template
# - Request review from maintainers
```

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: Explain what changes and why
- **Screenshots**: For UI changes
- **Testing**: How to test the changes
- **Breaking Changes**: Clearly marked if any

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the issue
- **Steps to Reproduce**: Step-by-step instructions
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, browser
- **Screenshots/Logs**: If applicable

### Feature Requests

For new features, please include:

- **Problem**: What problem does this solve?
- **Solution**: Proposed solution
- **Alternatives**: Other approaches considered
- **Use Cases**: Who would use this and how?

## 📚 Documentation

### Code Documentation

- Use docstrings for all public functions/classes
- Follow Google/NumPy docstring format
- Include type hints where possible

```python
def search_flights(
    origin: str,
    destination: str,
    depart_date: str,
    adults: int = 1
) -> FlightSearchResult:
    """Search for flights between two locations.

    Args:
        origin: Departure airport code or city name
        destination: Arrival airport code or city name
        depart_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers

    Returns:
        FlightSearchResult containing flight options

    Raises:
        FlightSearchError: If search fails
    """
```

### API Documentation

- All API endpoints are automatically documented via FastAPI
- Access docs at `http://localhost:8001/docs` when running locally
- Update OpenAPI specs for breaking changes

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=streamlit_app

# Run specific test file
pytest tests/test_api.py

# Run tests in verbose mode
pytest -v
```

### Writing Tests

- Use `pytest` framework
- Place tests in `tests/` directory
- Follow naming convention: `test_*.py`
- Use descriptive test names

```python
def test_flight_search_basic():
    """Test basic flight search functionality."""
    # Arrange
    search_params = {
        "origin": "JFK",
        "destination": "LAX",
        "depart_date": "2025-12-25"
    }

    # Act
    result = search_flights(**search_params)

    # Assert
    assert result.success is True
    assert len(result.flights) > 0
    assert all(flight.price > 0 for flight in result.flights)
```

## 🎨 Code Style

### Python Style

- Follow PEP 8
- Use Black for formatting
- Use isort for import sorting
- Maximum line length: 88 characters (Black default)

### Commit Messages

- Use conventional commits format:
  ```
  type(scope): description

  [optional body]

  [optional footer]
  ```

- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Example: `feat(api): add price alert endpoints`

### Branch Naming

- Feature branches: `feature/description`
- Bug fixes: `fix/issue-number-description`
- Documentation: `docs/update-readme`

## 🔧 Development Tools

### Pre-commit Hooks

This project uses pre-commit hooks to maintain code quality:

```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Code Quality Tools

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security scanning

## 📞 Getting Help

- **📖 Documentation**: Check the README and API docs first
- **💬 Discussions**: Use [GitHub Discussions](https://github.com/AbdirahmanNomad/flymind/discussions) for questions
- **🐛 Issues**: Report bugs via [GitHub Issues](https://github.com/AbdirahmanNomad/flymind/issues)
- **📧 Contact**: Reach out via GitHub for private matters

## 🙏 Recognition

Contributors will be recognized in:
- Repository README
- Release notes
- Project website (future)

Thank you for contributing to FlyMind! 🚀
