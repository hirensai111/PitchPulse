import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # === DESKTOP: Empty state ===
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto("http://localhost:5173")
        await page.wait_for_selector("text=IPL Predictor", timeout=10000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/screenshots/6b_empty.png", full_page=False)
        print("Saved 6b_empty.png")
        
        # === DESKTOP: Fill form and predict ===
        await page.select_option('select:has-text("Select team...")', "Mumbai Indians")
        await page.wait_for_timeout(300)
        await page.select_option('select:has-text("Select opponent...")', "Chennai Super Kings")
        await page.wait_for_timeout(300)
        await page.select_option('select:has-text("Select venue...")', "Wankhede Stadium")
        await page.wait_for_timeout(300)
        await page.fill('input[type="date"]', "2026-05-01")
        await page.wait_for_timeout(300)
        
        await page.click('button:has-text("Predict")')
        
        # Wait longer for predictions - backend might be slow
        await page.wait_for_timeout(25000)
        
        # Check if predictions loaded
        html = await page.content()
        if "Most Likely" in html and "Count of batter fours" in html:
            print("Predictions loaded")
        else:
            print("WARNING: Predictions may not have loaded fully")
        
        await page.screenshot(path="docs/screenshots/6b_mi_vs_csk.png", full_page=False)
        print("Saved 6b_mi_vs_csk.png")
        
        # === MOBILE: Resize the SAME page ===
        await page.set_viewport_size({"width": 400, "height": 900})
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/screenshots/6b_mobile.png", full_page=True)
        print("Saved 6b_mobile.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
