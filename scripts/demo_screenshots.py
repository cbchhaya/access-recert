"""
ARAS Demo Screenshots Script
============================

Uses Playwright to automate the demo flow and capture screenshots.

Author: Chiradeep Chhaya
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, Page

# Output directory for screenshots
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_screenshots")
BASE_URL = "http://localhost:3000"


async def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Screenshots will be saved to: {OUTPUT_DIR}")


async def screenshot(page: Page, name: str, description: str = ""):
    """Take a screenshot with a descriptive name."""
    filename = f"{name}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    await page.screenshot(path=filepath, full_page=False)
    print(f"  [OK] {filename}" + (f" - {description}" if description else ""))
    return filepath


async def wait_for_load(page: Page):
    """Wait for page to fully load."""
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(0.5)  # Small buffer for animations


async def demo_dashboard(page: Page):
    """Capture dashboard screenshots."""
    print("\n1. Dashboard Overview")
    await page.goto(BASE_URL)
    await wait_for_load(page)
    await screenshot(page, "01_dashboard", "Main dashboard with statistics")


async def demo_campaign_list(page: Page):
    """Capture campaign list screenshots."""
    print("\n2. Campaign List")
    await page.goto(f"{BASE_URL}/campaigns")
    await wait_for_load(page)
    await screenshot(page, "02_campaign_list", "Campaign list page")

    # Show archived toggle if there are archived campaigns
    show_archived = page.locator("text=Show archived")
    if await show_archived.count() > 0:
        await show_archived.click()
        await wait_for_load(page)
        await screenshot(page, "02b_campaign_list_with_archived", "Campaign list showing archived")
        await show_archived.click()  # Toggle back
        await wait_for_load(page)


async def demo_create_campaign(page: Page):
    """Capture campaign creation with tooltips."""
    print("\n3. Campaign Creation")
    await page.goto(f"{BASE_URL}/campaigns")
    await wait_for_load(page)

    # Click New Campaign button
    new_campaign_btn = page.locator("button:has-text('New Campaign')")
    if await new_campaign_btn.count() > 0:
        await new_campaign_btn.click()
        await asyncio.sleep(0.3)
        await screenshot(page, "03_create_campaign_modal", "New campaign creation modal")

        # Hover over tooltips to show them
        help_icons = page.locator("button:has(svg.lucide-help-circle)")
        if await help_icons.count() > 0:
            await help_icons.first.hover()
            await asyncio.sleep(0.3)
            await screenshot(page, "03b_campaign_tooltip", "Campaign creation with tooltip visible")

        # Close modal
        close_btn = page.locator("button:has-text('Cancel')")
        if await close_btn.count() > 0:
            await close_btn.click()
            await asyncio.sleep(0.2)


async def wait_for_table_data(page: Page, timeout: int = 15000):
    """Wait for table to have actual data rows (not skeleton loaders)."""
    try:
        # Wait for either real data rows or "No review items found" message
        await page.wait_for_selector(
            "table tbody tr:not(:has(.animate-pulse)), table tbody tr:has(td[colspan])",
            timeout=timeout
        )
        await asyncio.sleep(0.3)  # Small buffer for rendering
    except:
        print("    [WARN] Table data may not have loaded completely")


async def demo_campaign_detail(page: Page) -> str:
    """Capture campaign detail and review items. Returns campaign ID."""
    print("\n4. Campaign Detail & Review Items")

    # Find an active campaign (campaigns are cards, not table rows)
    await page.goto(f"{BASE_URL}/campaigns")
    await wait_for_load(page)

    # Click on first campaign card link (look for Active status if possible)
    active_campaign = page.locator("a[href^='/campaigns/']").first
    if await active_campaign.count() > 0:
        await active_campaign.click()
        await wait_for_load(page)

        # Wait for table data to actually load
        await wait_for_table_data(page)

        # Get campaign ID from URL
        campaign_id = page.url.split("/campaigns/")[-1].split("?")[0]

        await screenshot(page, "04_campaign_detail", "Campaign detail with review items")

        # Filter by Auto-Approved
        status_filter = page.locator("select").first
        if await status_filter.count() > 0:
            await status_filter.select_option("Auto-Approved")
            await wait_for_load(page)
            await wait_for_table_data(page)
            await screenshot(page, "04b_auto_approved_filter", "Review items filtered by Auto-Approved")

        # Filter by Needs-Review
        if await status_filter.count() > 0:
            await status_filter.select_option("Needs-Review")
            await wait_for_load(page)
            await wait_for_table_data(page)
            await screenshot(page, "04c_needs_review_filter", "Review items filtered by Needs-Review")

        # Reset filter
        if await status_filter.count() > 0:
            await status_filter.select_option("")
            await wait_for_load(page)

        return campaign_id

    print("    [SKIP] No campaigns found")
    return ""


async def demo_auto_approved_item(page: Page):
    """Capture auto-approved item detail."""
    print("\n5. Auto-Approved Item Detail")

    # Navigate to campaigns and find an ACTIVE campaign (only Active campaigns have review items)
    await page.goto(f"{BASE_URL}/campaigns")
    await wait_for_load(page)

    # Look for a card containing a green "Active" badge and click its link
    active_card = page.locator("div.bg-white.rounded-lg:has(span.bg-green-100) a[href^='/campaigns/']").first
    if await active_card.count() == 0:
        # Fallback: try any campaign
        active_card = page.locator("a[href^='/campaigns/']").first

    if await active_card.count() > 0:
        await active_card.click()
        await wait_for_load(page)

        # Wait for the filter selects to appear (they render after data loads)
        try:
            await page.wait_for_selector("select", timeout=5000)
        except:
            print("    [SKIP] No filter selects found - campaign may not be Active")
            return

        # Filter by Auto-Approved
        status_filter = page.locator("select").first
        if await status_filter.count() > 0:
            await status_filter.select_option("Auto-Approved")
            await wait_for_load(page)
            await wait_for_table_data(page)

            # Click on first auto-approved item row in the table (not skeleton)
            item_row = page.locator("table tbody tr:not(:has(.animate-pulse))").first
            if await item_row.count() > 0:
                await item_row.click()
                await wait_for_load(page)
                await screenshot(page, "05_auto_approved_detail", "Auto-approved item showing high score")

                # Highlight the Ask AI button
                ai_btn = page.locator("text=Ask AI to Explain")
                if await ai_btn.count() > 0:
                    await ai_btn.hover()
                    await asyncio.sleep(0.2)
                    await screenshot(page, "05b_ai_explain_button", "Ask AI to Explain button highlighted")
            else:
                print("    [SKIP] No auto-approved items found")
        else:
            print("    [SKIP] No status filter found")
    else:
        print("    [SKIP] No campaigns found")


async def demo_needs_review_item(page: Page) -> str:
    """Capture needs-review item detail. Returns item ID for chat demo."""
    print("\n6. Needs-Review Item Detail")

    # Navigate to campaigns and find an ACTIVE campaign
    await page.goto(f"{BASE_URL}/campaigns")
    await wait_for_load(page)

    # Look for a card containing a green "Active" badge and click its link
    # The Active badge has bg-green-100 class
    active_card = page.locator("div.bg-white.rounded-lg:has(span.bg-green-100) a[href^='/campaigns/']").first
    if await active_card.count() == 0:
        # Fallback: try any campaign
        active_card = page.locator("a[href^='/campaigns/']").first

    if await active_card.count() > 0:
        await active_card.click()
        await wait_for_load(page)

        # Wait for the filter selects to appear (they render after data loads)
        try:
            await page.wait_for_selector("select", timeout=5000)
        except:
            print("    [SKIP] No filter selects found - campaign may not be Active")
            return ""

        # Filter by Needs-Review
        status_filter = page.locator("select").first
        if await status_filter.count() > 0:
            await status_filter.select_option("Needs-Review")
            await wait_for_load(page)
            await wait_for_table_data(page)

            # Click on first needs-review item row in the table (not skeleton)
            item_row = page.locator("table tbody tr:not(:has(.animate-pulse))").first
            if await item_row.count() > 0:
                await item_row.click()
                await wait_for_load(page)
                await screenshot(page, "06_needs_review_detail", "Needs-review item with warnings")

                # Check for human review reason warning
                warning = page.locator("text=Human Review Required")
                if await warning.count() > 0:
                    await screenshot(page, "06b_human_review_warning", "Human review reason with system suggestion")

                # Get item ID from URL for chat demo
                item_id = page.url.split("/review/")[-1]
                return item_id
            else:
                print("    [SKIP] No needs-review items found")
        else:
            print("    [SKIP] No status filter found")
    else:
        print("    [SKIP] No campaigns found")

    return ""


async def demo_chat_interface(page: Page, item_id: str = ""):
    """Capture chat assistant screenshots."""
    print("\n7. Chat Assistant")

    await page.goto(f"{BASE_URL}/chat")
    await wait_for_load(page)
    await screenshot(page, "07_chat_initial", "Chat assistant initial view")

    # If we have an item ID, navigate with explain parameter
    if item_id:
        await page.goto(f"{BASE_URL}/chat?explain={item_id}")
        await wait_for_load(page)

        # Wait for the AI response (may take a few seconds)
        print("    Waiting for AI response...")
        try:
            # Wait for "Thinking..." to appear and then disappear
            await page.wait_for_selector("text=Thinking...", timeout=5000)
            await page.wait_for_selector("text=Thinking...", state="hidden", timeout=60000)
            await asyncio.sleep(0.5)
            await screenshot(page, "07b_chat_explain_response", "Chat explaining a review item")
        except:
            # If no API key configured, still take a screenshot
            await screenshot(page, "07b_chat_explain_attempt", "Chat explain request sent")


async def demo_bulk_actions(page: Page):
    """Capture bulk action UI."""
    print("\n8. Bulk Actions")

    # Navigate to campaigns and find an ACTIVE campaign
    await page.goto(f"{BASE_URL}/campaigns")
    await wait_for_load(page)

    # Look for a card containing a green "Active" badge and click its link
    active_card = page.locator("div.bg-white.rounded-lg:has(span.bg-green-100) a[href^='/campaigns/']").first
    if await active_card.count() == 0:
        # Fallback: try any campaign
        active_card = page.locator("a[href^='/campaigns/']").first

    if await active_card.count() > 0:
        await active_card.click()
        await wait_for_load(page)

        # Wait for the filter selects to appear
        try:
            await page.wait_for_selector("select", timeout=5000)
        except:
            print("    [SKIP] No filter selects found - campaign may not be Active")
            return

        # Don't filter - use all items to demonstrate bulk selection
        # Wait for actual data to load (not loading skeletons)
        # Look for checkboxes which only appear in real data rows
        try:
            await page.wait_for_selector("table tbody tr input[type='checkbox']", timeout=10000)
        except:
            print("    [SKIP] No table data loaded (only skeletons)")
            return

        # Select multiple checkboxes
        checkboxes = page.locator("table tbody tr input[type='checkbox']")
        count = await checkboxes.count()
        print(f"    Found {count} checkboxes in table")
        if count >= 2:
            await checkboxes.nth(0).check()
            await checkboxes.nth(1).check()
            await asyncio.sleep(0.3)
            await screenshot(page, "08_bulk_selection", "Bulk selection with certify/revoke buttons")
        elif count == 1:
            await checkboxes.nth(0).check()
            await asyncio.sleep(0.3)
            await screenshot(page, "08_bulk_selection", "Bulk selection with certify/revoke buttons")
        else:
            print(f"    [SKIP] No items for bulk selection (found {count})")
    else:
        print("    [SKIP] No campaigns found")


async def demo_campaign_menu(page: Page):
    """Capture campaign 3-dot menu."""
    print("\n9. Campaign Management Menu")

    await page.goto(f"{BASE_URL}/campaigns")
    await wait_for_load(page)

    # Click on 3-dot menu - look for the MoreVertical icon button
    menu_btn = page.locator("button").filter(has=page.locator("svg")).first
    # Try finding by looking for buttons near campaign cards
    all_buttons = page.locator("div.bg-white.rounded-lg button")
    count = await all_buttons.count()

    if count > 0:
        # Find the menu button (usually last button in a card)
        for i in range(count):
            btn = all_buttons.nth(i)
            # Try clicking it
            try:
                await btn.click()
                await asyncio.sleep(0.3)
                # Check if a menu appeared
                menu = page.locator("text=Rename")
                if await menu.count() > 0:
                    await screenshot(page, "09_campaign_menu", "Campaign 3-dot menu with rename/archive options")
                    # Click elsewhere to close menu
                    await page.click("body", position={"x": 10, "y": 10})
                    break
            except:
                continue
    else:
        print("    [SKIP] No campaign menu buttons found")


async def run_demo():
    """Run the full demo and capture all screenshots."""
    print("=" * 60)
    print("ARAS Demo Screenshot Generator")
    print("=" * 60)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    await ensure_output_dir()

    async with async_playwright() as p:
        # Launch browser
        print("\nLaunching browser...")
        browser = await p.chromium.launch(headless=False)  # headless=False to see what's happening

        # Create context with specific viewport for consistent screenshots
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1
        )

        page = await context.new_page()

        try:
            # Run demo sections
            await demo_dashboard(page)
            await demo_campaign_list(page)
            await demo_create_campaign(page)
            campaign_id = await demo_campaign_detail(page)
            await demo_auto_approved_item(page)
            item_id = await demo_needs_review_item(page)
            await demo_chat_interface(page, item_id)
            await demo_bulk_actions(page)
            await demo_campaign_menu(page)

            print("\n" + "=" * 60)
            print("Demo Complete!")
            print("=" * 60)
            print(f"\nScreenshots saved to: {OUTPUT_DIR}")
            print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"\nError during demo: {e}")
            # Take error screenshot
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "error_screenshot.png"))
            raise

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
