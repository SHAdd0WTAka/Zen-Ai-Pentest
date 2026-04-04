#!/usr/bin/env python3
"""
Open Zen-AI-Pentest Web UI in Playwright browser
"""

import asyncio

from playwright.async_api import async_playwright

URL = "https://5158f5b7.zen-alpha-pentest-dmn.pages.dev"


async def main():
    async with async_playwright() as p:
        # Launch browser with visible window
        browser = await p.chromium.launch(headless=False, args=["--window-size=1400,900"])

        # Create context with larger viewport
        context = await browser.new_context(viewport={"width": 1400, "height": 900})

        # Open page
        page = await context.new_page()

        print(f"🌐 Opening {URL}...")
        await page.goto(URL, wait_until="networkidle")

        # Wait a bit for the page to fully load
        await asyncio.sleep(3)

        print("✅ Web UI is now open!")
        print("   URL:", URL)
        print("   Press Ctrl+C to close...")

        # Keep browser open
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Closing browser...")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
