import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        await page.goto("http://localhost:5173")
        await page.wait_for_selector("text=IPL Predictor", timeout=10000)
        await page.wait_for_timeout(1000)
        
        print("Filling form...")
        await page.select_option('select:has-text("Select team...")', "Mumbai Indians")
        await page.wait_for_timeout(500)
        await page.select_option('select:has-text("Select opponent...")', "Chennai Super Kings")
        await page.wait_for_timeout(500)
        await page.select_option('select:has-text("Select venue...")', "Wankhede Stadium")
        await page.wait_for_timeout(500)
        await page.fill('input[type="date"]', "2026-05-01")
        await page.wait_for_timeout(500)
        
        print("Clicking Predict...")
        await page.click('button:has-text("Predict")')
        
        await page.wait_for_timeout(5000)
        await page.screenshot(path="docs/screenshots/debug_after_click.png")
        print("Saved debug screenshot")
        
        # Check if button is disabled
        disabled = await page.evaluate('''() => {
            const btn = document.querySelector('button:has-text("Predict")');
            return btn ? btn.disabled : "not found";
        }''')
        print(f"Button disabled: {disabled}")
        
        # Check page HTML for clues
        html = await page.content()
        if "Most Likely" in html:
            print("Most Likely found in HTML")
        else:
            print("Most Likely NOT found in HTML")
        if "Skeleton" in html or "skeleton" in html:
            print("Skeleton found in HTML")
        if "loading" in html.lower():
            print("Loading text found")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
