# Jimaku-DL Tests

This directory contains tests for the jimaku-dl package using pytest.

## Running Tests

To run all tests:

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```

To run a specific test file:

```bash
pytest tests/test_downloader.py
```

To run a specific test:

```bash
pytest tests/test_downloader.py::TestJimakuDownloader::test_init
```

## Test Coverage

To generate a test coverage report:

```bash
pytest --cov=jimaku_dl
```

For an HTML coverage report:

```bash
pytest --cov=jimaku_dl --cov-report=html
```

## Adding Tests

1. Create test files with the naming convention `test_*.py`
2. Create test classes with the naming convention `Test*`
3. Create test methods with the naming convention `test_*`
4. Use the fixtures defined in `conftest.py` for common functionality
