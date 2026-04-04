#!/usr/bin/env python3
"""
Take screenshots of Zen-AI-Pentest Web UI using Playwright
"""

import asyncio

from playwright.async_api import async_playwright

URL = "https://5158f5b7.zen-alpha-pentest-dmn.pages.dev"


async def main():
    async with async_playwright() as p:
        # Launch browser in headless mode for screenshot
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(viewport={"width": 1920, "height": 1080})

        page = await context.new_page()

        print(f"📸 Taking screenshot of {URL}...")

        # Navigate to page
        await page.goto(URL, wait_until="networkidle")
        await asyncio.sleep(3)

        # Screenshot 1: Full page
        await page.screenshot(path="/home/atakan/Zen-Ai-Pentest/web_ui_screenshot_1.png", full_page=True)
        print("✅ Screenshot 1 saved: web_ui_screenshot_1.png")

        # Check if we're on login page and fill in credentials
        try:
            # Look for login form
            username_field = await page.query_selector('input[type="text"], input[name="username"], #username')
            if username_field:
                print("🔐 Login form detected, filling credentials...")
                await username_field.fill("admin")

                password_field = await page.query_selector('input[type="password"], #password')
                if password_field:
                    await password_field.fill("admin")

                    # Screenshot 2: Login form filled
                    await page.screenshot(path="/home/atakan/Zen-Ai-Pentest/web_ui_screenshot_2.png")
                    print("✅ Screenshot 2 saved: web_ui_screenshot_2.png")

                    # Click login button
                    login_btn = await page.query_selector(
                        'button[type="submit"], button:has-text("Login"), button:has-text("Sign In")'
                    )
                    if login_btn:
                        await login_btn.click()
                        await asyncio.sleep(5)

                        # Screenshot 3: After login
                        await page.screenshot(path="/home/atakan/Zen-Ai-Pentest/web_ui_screenshot_3.png", full_page=True)
                        print("✅ Screenshot 3 saved: web_ui_screenshot_3.png")
        except Exception as e:
            print(f"Note: {e}")

        # Get console logs
        logs = []
        page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
        await asyncio.sleep(2)

        print("\n📋 Console logs:")
        for log in logs[-10:]:  # Last 10 logs
            print(f"   {log}")

        await browser.close()
        print("\n🎉 Done! Check the screenshots.")


if __name__ == "__main__":
    asyncio.run(main())
