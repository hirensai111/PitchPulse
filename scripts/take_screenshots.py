import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Empty state screenshot
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto("http://localhost:5173")
        await page.wait_for_selector("text=IPL Predictor", timeout=10000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/screenshots/6b_empty.png", full_page=False)
        print("Saved 6b_empty.png")
        
        # 2. MI vs CSK prediction screenshot
        # Select Team 1 = Mumbai Indians
        await page.select_option('select:has-text("Select team...")', "Mumbai Indians")
        await page.wait_for_timeout(200)
        # Select Team 2 = Chennai Super Kings
        await page.select_option('select:has-text("Select opponent...")', "Chennai Super Kings")
        await page.wait_for_timeout(200)
        # Select Venue = Wankhede Stadium
        await page.select_option('select:has-text("Select venue...")', "Wankhede Stadium")
        await page.wait_for_timeout(200)
        # Set date
        await page.fill('input[type="date"]', "2026-05-01")
        await page.wait_for_timeout(200)
        # Click Predict
        await page.click('button:has-text("Predict")')
        # Wait for results
        await page.wait_for_selector('text=Most Likely', timeout=30000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/screenshots/6b_mi_vs_csk.png", full_page=False)
        print("Saved 6b_mi_vs_csk.png")
        
        # 3. Mobile view screenshot
        await page.set_viewport_size({"width": 400, "height": 900})
        await page.reload()
        await page.wait_for_selector("text=IPL Predictor", timeout=10000)
        await page.wait_for_timeout(500)
        # Fill form again
        await page.select_option('select:has-text("Select team...")', "Mumbai Indians")
        await page.wait_for_timeout(200)
        await page.select_option('select:has-text("Select opponent...")', "Chennai Super Kings")
        await page.wait_for_timeout(200)
        await page.select_option('select:has-text("Select venue...")', "Wankhede Stadium")
        await page.wait_for_timeout(200)
        await page.fill('input[type="date"]', "2026-05-01")
        await page.wait_for_timeout(200)
        await page.click('button:has-text("Predict")')
        await page.wait_for_selector('text=Most Likely', timeout=30000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/screenshots/6b_mobile.png", full_page=True)
        print("Saved 6b_mobile.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
