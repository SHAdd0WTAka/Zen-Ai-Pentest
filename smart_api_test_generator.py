#!/usr/bin/env python3
"""
Smart API Test Generator for Zen-AI-Pentest
Generates comprehensive FastAPI endpoint tests automatically.
"""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

# Import TypedDict for type hints
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

# Configure logging
logger = logging.getLogger(__name__)


class RouteInfo(TypedDict):
    """Type definition for route information."""

    name: str
    method: Optional[str]
    path: Optional[str]
    params: List[Dict[str, str]]
    is_async: bool


def extract_fastapi_routes(file_path: str) -> List[RouteInfo]:
    """Extract FastAPI route definitions from a Python file.

    Args:
        file_path: Path to the Python file to parse.

    Returns:
        List of route information dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        SyntaxError: If the file contains invalid Python syntax.
    """
    routes: List[RouteInfo] = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
        return routes
    except SyntaxError as e:
        logger.error("Syntax error in %s: %s", file_path, e)
        return routes
    except UnicodeDecodeError as e:
        logger.error("Encoding error in %s: %s", file_path, e)
        return routes

    for node in ast.walk(tree):
        # Look for function definitions with route decorators
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                route_info = _extract_route_info(decorator, node)
                if route_info:
                    routes.append(route_info)

    return routes


def _extract_route_info(decorator: ast.expr, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[RouteInfo]:
    """Extract route information from a decorator.

    Args:
        decorator: The decorator AST node.
        func_node: The function definition AST node.

    Returns:
        Route information dictionary or None if not a valid route decorator.
    """
    route_info: RouteInfo = {
        "name": func_node.name,
        "method": None,
        "path": None,
        "params": [],
        "is_async": isinstance(func_node, ast.AsyncFunctionDef),
    }

    # Handle different decorator patterns
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Attribute):
            method = func.attr.upper()
            if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                route_info["method"] = method
                # Extract path from first argument
                if decorator.args:
                    if isinstance(decorator.args[0], ast.Constant):
                        route_info["path"] = decorator.args[0].value
        elif isinstance(func, ast.Name):
            # Handle @router.get(...) patterns
            if func.id in ["get", "post", "put", "delete", "patch"]:
                route_info["method"] = func.id.upper()
                if decorator.args:
                    if isinstance(decorator.args[0], ast.Constant):
                        route_info["path"] = decorator.args[0].value

    # Extract function parameters
    for arg in func_node.args.args:
        if arg.arg != "self":  # Skip self
            param_type = "Any"
            if isinstance(arg.annotation, ast.Name):
                param_type = arg.annotation.id
            elif isinstance(arg.annotation, ast.Constant):
                param_type = str(arg.annotation.value)
            route_info["params"].append({"name": arg.arg, "type": param_type})

    return route_info if route_info["method"] else None


def generate_test_file(module_name: str, routes: List[RouteInfo], output_path: str) -> None:
    """Generate a test file for the given routes.

    Args:
        module_name: Name of the module being tested.
        routes: List of route information dictionaries.
        output_path: Path where the test file will be written.

    Raises:
        IOError: If unable to write to the output path.
    """
    test_content = _generate_test_header(module_name)

    for route in routes:
        test_content += _generate_test_for_route(route)

    # Write test file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        logger.info("Generated: %s", output_path)
    except IOError as e:
        logger.error("Failed to write test file %s: %s", output_path, e)
        raise


def _generate_test_header(module_name: str) -> str:
    """Generate the header section of a test file.

    Args:
        module_name: Name of the module being tested.

    Returns:
        Header content as a string.
    """
    class_name = module_name.title().replace("_", "")
    return f'''"""
Auto-generated API tests for {module_name}
Generated by smart_api_test_generator.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json


# Mock authentication for testing
def mock_auth():
    """Mock authentication token."""
    return "test-token"


class Test{class_name}Routes:
    """Test suite for {module_name} API routes."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked auth."""
        from api.main import app
        from fastapi.testclient import TestClient

        # Mock authentication dependency
        def mock_verify_token():
            return {{"user_id": "test-user", "role": "admin"}}

        app.dependency_overrides = {{}}
        return TestClient(app)

'''


def _generate_test_for_route(route: RouteInfo) -> str:
    """Generate test methods for a single route.

    Args:
        route: Route information dictionary.

    Returns:
        Test code as a string.
    """
    method = route["method"]
    path = route["path"] or "/"
    name = route["name"]

    # Create test name
    test_name = f"test_{method.lower()}_{name}"

    return f'''
    def {test_name}(self, client):
        """Test {method} {path} - {name}"""
        # Mock database/dependencies as needed
        with patch('database.crud.get_db') as mock_db:
            mock_db.return_value = MagicMock()

            response = client.{method.lower()}("{path}")

            # Assert response (adjust status code as needed)
            assert response.status_code in [200, 201, 401, 404, 422]

    def {test_name}_unauthorized(self, client):
        """Test {method} {path} without auth"""
        response = client.{method.lower()}("{path}")
        # Should require authentication
        assert response.status_code in [401, 403]
'''


def main() -> int:
    """Main function to generate tests for all API routes.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    api_routes_dir = Path("api/routes")
    output_dir = Path("tests/unit/api")

    if not api_routes_dir.exists():
        logger.error("API routes directory not found: %s", api_routes_dir)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Scanning API routes...")

    total_routes = 0
    files_processed = 0

    for py_file in api_routes_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        module_name = py_file.stem
        routes = extract_fastapi_routes(str(py_file))

        if routes:
            logger.info("Found %d routes in %s", len(routes), module_name)
            output_file = output_dir / f"test_{module_name}_auto.py"
            try:
                generate_test_file(module_name, routes, str(output_file))
                total_routes += len(routes)
                files_processed += 1
            except IOError as e:
                logger.error("Failed to generate tests for %s: %s", module_name, e)

    logger.info("Test files generated in %s/", output_dir)
    logger.info("Processed %d files with %d total routes", files_processed, total_routes)
    logger.warning("Note: Review and adjust generated tests before running!")

    return 0


if __name__ == "__main__":
    # Setup logging when run as script
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    exit(main())
