import asyncio, saveload
from datetime import timedelta
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

ids = []

async def get_text(ctx, selector):
    loc = ctx.page.locator(f'.modal.show {selector}')
    try:
        await loc.wait_for(state='visible', timeout=2000)
        return (await loc.inner_text()).strip() if await loc.count() else ''
    except PlaywrightTimeoutError:
        print(f"⚠️ Couldn't find '{selector}' or it's not visible on screen. Moving on! ")
        return ''
    except Exception as e:
        print(f"❌ Ran into a snag trying to get text from '{selector}': {e}. ")
        return ''

async def handle(ctx: PlaywrightCrawlingContext):
    print(f"🌐 We've landed on: {ctx.page.url}")

    cookie_modal_selector = '#cookieConsent.modal.show'
    accept_button_selector = '#cookieConsent .accept-policy'

    try:
        await ctx.page.wait_for_selector(cookie_modal_selector, timeout=10000)
        print('🍪 A cookie consent pop-up just appeared! ')

        accept_button = ctx.page.locator(accept_button_selector)
        await accept_button.click()
        print('✅ We clicked to accept the cookies. ')

        await ctx.page.wait_for_selector(cookie_modal_selector, state='hidden', timeout=5000)
        print('👍 Cookie consent pop-up is now out of sight, out of mind! ')

    except PlaywrightTimeoutError:
        print('😌 No cookie consent pop-up found, or it vanished super fast. All clear! ')
    except Exception as e:
        print(f'🚨 Something unexpected happened with the cookie consent pop-up: {e}. ')

    print('🚀 Kicking off the scraping process now... ')
    await ctx.page.wait_for_selector('a[data-bs-toggle="modal"]')

    links = await ctx.page.locator('a[data-bs-toggle="modal"]').all()
    print(f'🔍 Found {len(links)} items on the page to explore! ')

    for i, link in enumerate(links):
        
        item_id = await link.get_attribute("data-id")
        if not item_id:
            print(f"⚠️ Item {i+1} seems to be missing its ID. Skipping this one for now. ")
            continue

        if item_id in ids:
            print(f"⏩ Already processed item {i + 1} ({item_id}). Skipping to the next! ")
            await ctx.page.wait_for_timeout(700)
            continue

        ids.append(item_id) 
        
        print(f'✨ Diving into item {i + 1}/{len(links)} ({item_id})... ')

        try:
            await link.scroll_into_view_if_needed()
            await link.wait_for(state='visible', timeout=5000)
            await link.click()
            print('👉 Link clicked successfully! ')
        except PlaywrightTimeoutError:
            print(f"⏰ Timeout trying to click item {i+1} ({item_id}). It just wouldn't show up! ")
            continue
        except Exception as e:
            print(f"💥 Encountered an error clicking item {i+1} ({item_id}): {e}. ")
            continue

        try:
            await ctx.page.wait_for_selector(".modal.show", timeout=10000)
            print(f"✔️ The modal for item {i+1} ({item_id}) has appeared. ")

            website_href = ""
            website_locator = ctx.page.locator('.modal.show #website a')
            try:
                await website_locator.wait_for(state='attached', timeout=3000) 
                website_href = await website_locator.get_attribute("href") or ""
            except PlaywrightTimeoutError:
                print(f"🔗 Couldn't find the website link for item '{item_id}' or it took too long to load. No worries! ")
            except Exception as e:
                print(f"❌ Something unexpected happened while grabbing the website for item {i+1} ({item_id}): {e}. ")

            data = {
                "ID": item_id, 
                "Brand": await get_text(ctx, "#brandName"),
                "Product": await get_text(ctx, "#productName"),
                "Producer": await get_text(ctx, "#producerName"),
                "Country": await get_text(ctx, "#countryName"),
                "ABV": str(await get_text(ctx, "#abv")).replace("ABV ", ""),
                "Note": str(await get_text(ctx, "#note")).replace("JUDGES' TASTING NOTE\n", ""),
                "Categories": await get_text(ctx, "#categories"),
                "Energy": str(await get_text(ctx, "#energy")).replace("Energy: ", ""), 
                "Carbs": str(await get_text(ctx, "#carbs")).replace("Carbohydrates: ", ""),
                "Sugars": str(await get_text(ctx, "#sugars")).replace("Sugars: ", ""),
                "Website": website_href
            }

            saveload.append(data)
            print(f"💾 Data for item {i+1} ({item_id}) saved! ")

        except Exception as e:
            print(f"🐛 Ran into an issue while extracting data for item {i+1} ({item_id}): {e}. ")

        finally:
            try:
                close_button = ctx.page.locator(".modal.show .btn-close").first
                await close_button.wait_for(state='visible', timeout=2000)
                await close_button.click()
                await ctx.page.wait_for_selector(".modal.show", state='hidden', timeout=5000)
                print(f"✖️ Modal for item {i+1} ({item_id}) closed successfully! ")
            except PlaywrightTimeoutError:
                print(f"🤷‍♀️ Couldn't find the close button or the modal for item {i+1} ({item_id}) just wouldn't close. Trying 'Escape'! ")
                await ctx.page.keyboard.press('Escape')
                await ctx.page.wait_for_timeout(500)
            except Exception as e:
                print(f"🚫 Unexpected problem closing the modal for item {i+1} ({item_id}): {e}. ")

            await ctx.page.wait_for_timeout(1000)


async def run():
    global ids
    ids = saveload.init()
    print('📂 Loaded existing IDs. Ready to roll! ')

    crawler = PlaywrightCrawler(
        headless=True,
        request_handler_timeout=timedelta(seconds=900)
    )
    crawler.router.default_handler(handle)
    await crawler.add_requests(['https://worldafawards.com/results/2025'])
    await crawler.run()
    print('🎉 All done!')

if __name__ == '__main__':
    asyncio.run(run())
