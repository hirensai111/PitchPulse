import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        
        # === 1. Track Record page ===
        await page.goto("http://localhost:5173/track-record")
        await page.wait_for_selector("text=Live Forward Test Results", timeout=10000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path="docs/screenshots/6c_track_record.png", full_page=True)
        print("Saved 6c_track_record.png")
        
        # === 2. Single MatchResultCard zoomed ===
        # Screenshot the first card by finding its bounding box
        card_locator = page.locator("h3:has-text('Sunrisers Hyderabad')").first.locator("xpath=ancestor::div[contains(@class, 'rounded-lg')]")
        await card_locator.screenshot(path="docs/screenshots/6c_match_card.png")
        print("Saved 6c_match_card.png")
        
        # === 3. ExplainPopover ===
        await page.goto("http://localhost:5173")
        await page.wait_for_selector("text=IPL Predictor", timeout=10000)
        await page.wait_for_timeout(500)
        
        # Fill form and predict
        await page.select_option('select:has-text("Select team...")', "Mumbai Indians")
        await page.wait_for_timeout(300)
        await page.select_option('select:has-text("Select opponent...")', "Chennai Super Kings")
        await page.wait_for_timeout(300)
        await page.select_option('select:has-text("Select venue...")', "Wankhede Stadium")
        await page.wait_for_timeout(300)
        await page.fill('input[type="date"]', "2026-05-01")
        await page.wait_for_timeout(300)
        await page.click('button:has-text("Predict")')
        await page.wait_for_selector('text=Most Likely', timeout=30000)
        await page.wait_for_timeout(1000)
        
        # Click the first info icon
        await page.locator('button[aria-label="Explain prediction"]').first.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/screenshots/6c_explain_popover.png", full_page=False)
        print("Saved 6c_explain_popover.png")
        
        # === 4. Feature Importance Chart Dialog ===
        # Click "See all feature importances" link in the popover
        await page.click('text=See all feature importances')
        await page.wait_for_timeout(1500)
        await page.screenshot(path="docs/screenshots/6c_feature_importance.png", full_page=False)
        print("Saved 6c_feature_importance.png")
        
        # Close dialog
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
        
        # === 5. Model Card page ===
        await page.goto("http://localhost:5173/about")
        await page.wait_for_selector("text=About This Model", timeout=10000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path="docs/screenshots/6c_model_card.png", full_page=True)
        print("Saved 6c_model_card.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
