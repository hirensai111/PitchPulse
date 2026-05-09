import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 400, "height": 900})
        
        await page.goto("http://localhost:5173")
        await page.wait_for_selector("text=IPL Predictor", timeout=10000)
        await page.wait_for_timeout(1500)
        
        # Wait for selects to be populated
        await page.wait_for_selector('select option[value="Mumbai Indians"]', timeout=10000)
        
        # Fill form with explicit waits
        await page.select_option('select:has-text("Select team...")', "Mumbai Indians")
        await page.wait_for_timeout(500)
        
        await page.wait_for_selector('select option[value="Chennai Super Kings"]', timeout=10000)
        await page.select_option('select:has-text("Select opponent...")', "Chennai Super Kings")
        await page.wait_for_timeout(500)
        
        await page.select_option('select:has-text("Select venue...")', "Wankhede Stadium")
        await page.wait_for_timeout(500)
        
        await page.fill('input[type="date"]', "2026-05-01")
        await page.wait_for_timeout(500)
        
        # Click Predict
        await page.click('button:has-text("Predict")')
        
        # Wait for network idle + extra time for React to render
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(5000)
        
        # Wait for either likely list or error
        try:
            await page.wait_for_selector('text=Most Likely', timeout=15000)
        except:
            pass
        
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path="docs/screenshots/6b_mobile.png", full_page=True)
        print("Saved 6b_mobile.png")
        
        # Debug: get page text
        text = await page.content()
        if "Count of batter fours" in text:
            print("Predictions loaded successfully")
        else:
            print("WARNING: Predictions not found in page content")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
