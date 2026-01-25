#!/usr/bin/env python3
"""
Visual test for multi-template functionality
Tests that the system returns multiple templates when starting redlining
"""
import asyncio
import json
from playwright.async_api import async_playwright
import sys

async def test_multi_template_redlining():
    """Test multi-template redlining with Chrome visible"""

    async with async_playwright() as p:
        # Launch Chrome in headed mode (visible)
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized'],
            slow_mo=1000  # Slow down for visibility
        )

        context = await browser.new_context(viewport=None)
        page = await context.new_page()

        print("🌐 Opening application...")
        await page.goto('http://localhost:5173')
        await page.wait_for_load_state('networkidle')

        # Take initial screenshot
        await page.screenshot(path='/tmp/01_homepage.png')
        print("📸 Screenshot: Homepage")

        # Navigate to Redlining mode
        print("\n🔍 Navigating to Redlining mode...")
        redlining_button = page.locator('text=Redlining')
        if await redlining_button.count() > 0:
            await redlining_button.click()
            await page.wait_for_timeout(1000)
            await page.screenshot(path='/tmp/02_redlining_mode.png')
            print("📸 Screenshot: Redlining Mode")
        else:
            print("⚠️  Redlining button not found - might be in different mode")

        # Set up network listener to capture API response
        multi_template_response = None

        async def handle_response(response):
            nonlocal multi_template_response
            if 'start-progressive' in response.url:
                try:
                    data = await response.json()
                    multi_template_response = data
                    print(f"\n✅ Captured API response from {response.url}")
                    print(f"📊 Response data:")
                    print(json.dumps(data, indent=2))
                except:
                    pass

        page.on('response', handle_response)

        # Upload a test document
        print("\n📤 Looking for file upload...")

        # Look for file input or upload button
        file_input = page.locator('input[type="file"]')
        if await file_input.count() > 0:
            print("📎 Found file input, uploading test contract...")

            # Use the test contract file
            test_file = '/Users/ryan.hooley@bmcjax.com/Documents/VS Projects/Contracts-AI/test_contract_nda.txt'
            await file_input.set_input_files(test_file)
            await page.wait_for_timeout(1000)

            await page.screenshot(path='/tmp/03_file_selected.png')
            print("📸 Screenshot: File Selected")

            # Look for category selector
            category_buttons = page.locator('[class*="category"]')
            if await category_buttons.count() > 0:
                print("📋 Selecting category...")
                # Try to click Employment category
                employment = page.locator('text=Employment')
                if await employment.count() > 0:
                    await employment.click()
                    await page.wait_for_timeout(500)

            # Click Start Redlining button
            start_button = page.locator('button:has-text("Start Redlining")')
            if await start_button.count() > 0:
                print("🚀 Clicking 'Start Redlining'...")
                await start_button.click()

                # Wait for API response
                print("⏳ Waiting for multi-template analysis...")
                await page.wait_for_timeout(3000)

                await page.screenshot(path='/tmp/04_analysis_started.png')
                print("📸 Screenshot: Analysis Started")

                # Check if we captured the multi-template response
                if multi_template_response:
                    print("\n" + "="*60)
                    print("🎉 MULTI-TEMPLATE RESPONSE CAPTURED!")
                    print("="*60)

                    if 'templates' in multi_template_response:
                        templates = multi_template_response['templates']
                        print(f"\n✅ Found {len(templates)} templates in response:")
                        for i, template in enumerate(templates, 1):
                            print(f"\n  Template #{i}:")
                            print(f"    • ID: {template.get('id', 'N/A')[:16]}...")
                            print(f"    • Category: {template.get('category', 'N/A')}")
                            print(f"    • Similarity: {template.get('similarity_score', 0):.3f}")

                        if len(templates) >= 2:
                            print(f"\n✅ SUCCESS: Multi-template comparison working!")
                            print(f"   System is comparing against {len(templates)} templates")
                        else:
                            print(f"\n⚠️  Only 1 template found (expected 3)")
                    else:
                        print("\n❌ 'templates' key not found in response")
                        print(f"   Response keys: {list(multi_template_response.keys())}")
                else:
                    print("\n⚠️  Did not capture start-progressive API response")

                # Wait for progress modal
                await page.wait_for_timeout(5000)
                await page.screenshot(path='/tmp/05_progress_modal.png')
                print("\n📸 Screenshot: Progress Modal")

                # Wait for analysis to complete
                print("\n⏳ Waiting for analysis to complete...")
                await page.wait_for_timeout(15000)

                await page.screenshot(path='/tmp/06_review_screen.png')
                print("📸 Screenshot: Review Screen")

            else:
                print("⚠️  'Start Redlining' button not found")
        else:
            print("⚠️  File input not found")

        print("\n" + "="*60)
        print("📸 All screenshots saved to /tmp/")
        print("="*60)

        # Keep browser open for manual inspection
        print("\n👁️  Browser will stay open for 30 seconds for manual inspection...")
        await page.wait_for_timeout(30000)

        await browser.close()

        # Return test results
        return multi_template_response is not None and len(multi_template_response.get('templates', [])) >= 2

if __name__ == '__main__':
    result = asyncio.run(test_multi_template_redlining())

    if result:
        print("\n✅ TEST PASSED: Multi-template functionality working!")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED: Multi-template response not captured or insufficient templates")
        sys.exit(1)
