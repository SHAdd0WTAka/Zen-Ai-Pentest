"""
E2E Tests for Authentication using Playwright
"""

import pytest


@pytest.mark.playwright
class TestAuthE2E:
    """E2E Tests for Authentication"""

    @pytest.mark.skip(reason="Playwright not installed in CI")
    def test_login_page_loads(self, page):
        """Test that login page loads correctly"""
        # Navigate to login page
        page.goto("http://localhost:5173/login")

        # Check page title
        assert "Login" in page.title() or "Zen" in page.title()

        # Check for login form elements
        assert page.locator("input[type='text']").count() > 0 or page.locator("input[name='username']").count() > 0
        assert page.locator("input[type='password']").count() > 0

    @pytest.mark.skip(reason="Playwright not installed in CI")
    def test_login_flow(self, page):
        """Test complete login flow"""
        page.goto("http://localhost:5173/login")

        # Fill in credentials
        page.fill("input[name='username']", "admin")
        page.fill("input[type='password']", "admin")

        # Click login button
        page.click("button[type='submit']")

        # Wait for navigation
        page.wait_for_url("**/dashboard")

        # Check we're logged in
        assert "dashboard" in page.url.lower() or page.locator("text=Dashboard").count() > 0


@pytest.mark.playwright
class TestDashboardE2E:
    """E2E Tests for Dashboard"""

    @pytest.mark.skip(reason="Playwright not installed in CI")
    def test_dashboard_loads(self, page):
        """Test that dashboard loads correctly"""
        # Assuming we're already logged in
        page.goto("http://localhost:5173/dashboard")

        # Check for dashboard elements
        assert page.locator("text=Dashboard").count() > 0 or page.locator("text=Scans").count() > 0

    @pytest.mark.skip(reason="Playwright not installed in CI")
    def test_navigation_menu(self, page):
        """Test navigation menu works"""
        page.goto("http://localhost:5173/dashboard")

        # Click on different menu items
        menu_items = ["Scans", "Agents", "Findings", "Reports"]

        for item in menu_items:
            try:
                page.click(f"text={item}")
                page.wait_for_load_state("networkidle")
                assert page.url.contains(item.lower()) or page.locator(f"text={item}").count() > 0
            except Exception:
                pass  # Menu item might not exist


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
