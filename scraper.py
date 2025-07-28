import asyncio, logging
from saveload  import *
from datetime import timedelta
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

ids = []
logging.getLogger('crawlee').setLevel(logging.ERROR) # Supress request statistics

async def get_text(ctx, selector):
    loc = ctx.page.locator(f'.modal.show {selector}')
    try:
        await loc.wait_for(state='visible', timeout=2000)
        return (await loc.inner_text()).strip() if await loc.count() else ''
    except PlaywrightTimeoutError:
        log(f"⚠️ '{selector}' not visible.")
        return ''
    except Exception as e:
        log(f"❌ Error scraping '{selector}': {e}")
        return ''

async def handle(ctx: PlaywrightCrawlingContext):
    log(f"🌐 Page loaded: '{ctx.page.url}'")

    cookie_modal_selector = '#cookieConsent.modal.show'
    accept_button_selector = '#cookieConsent .accept-policy'

    try:
        await ctx.page.wait_for_selector(cookie_modal_selector, timeout=10000)
        log('🍪 Cookie prompt detected.')

        accept_button = ctx.page.locator(accept_button_selector)
        await accept_button.click()
        log('✅ Cookies accepted.')

        await ctx.page.wait_for_selector(cookie_modal_selector, state='hidden', timeout=5000)
        log('👍 Cookie prompt closed.')
    except PlaywrightTimeoutError:
        log('😌 No cookie prompt found.')
    except Exception as e:
        log(f'🚨 Cookie prompt error: {e}')

    log('🚀 Starting scraping.')
    await ctx.page.wait_for_selector('a[data-bs-toggle="modal"]')

    links = await ctx.page.locator('a[data-bs-toggle="modal"]').all()
    log(f'🔍 Found {len(links)} items.')

    for i, link in enumerate(links):
        item_id = await link.get_attribute("data-id")
        if not item_id:
            log(f"⚠️ Skipped: No ID.")
            continue

        if item_id in ids:
            log(f"⏩ Skipped: Already processed.")
            await ctx.page.wait_for_timeout(700)
            continue

        ids.append(item_id)
        log(f'✨ Item {i + 1}/{len(links)} ({item_id})')

        try:
            await link.scroll_into_view_if_needed()
            await link.wait_for(state='visible', timeout=5000)
            await link.click()
            log('👉 Clicked.')
        except PlaywrightTimeoutError:
            log(f"⏰ Click failed: Timeout.")
            continue
        except Exception as e:
            log(f"💥 Click error: {e}")
            continue

        try:
            await ctx.page.wait_for_selector(".modal.show", timeout=10000)
            log(f"✔️ Modal opened.")

            website_href = ""
            website_locator = ctx.page.locator('.modal.show #website a')
            try:
                await website_locator.wait_for(state='attached', timeout=3000)
                website_href = await website_locator.get_attribute("href") or ""
            except PlaywrightTimeoutError:
                log(f"🔗 Website not found.")
            except Exception as e:
                log(f"❌ Website error: {e}")

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

            append(data)
            log(f"💾 Saved.")
        except Exception as e:
            log(f"🐛 Data extraction error: {e}")
        finally:
            try:
                close_button = ctx.page.locator(".modal.show .btn-close").first
                await close_button.wait_for(state='visible', timeout=2000)
                await close_button.click()
                await ctx.page.wait_for_selector(".modal.show", state='hidden', timeout=5000)
                log(f"✖️ Modal closed.")
            except PlaywrightTimeoutError:
                log(f"🤷‍♀️ Close failed. Using Escape.")
                await ctx.page.keyboard.press('Escape')
                await ctx.page.wait_for_timeout(500)
            except Exception as e:
                log(f"🚫 Close error: {e}")

            await ctx.page.wait_for_timeout(1000)

async def run():
    global ids
    ids = init()
    log('📂 IDs loaded.')

    crawler = PlaywrightCrawler(
        headless=True,
        request_handler_timeout=timedelta(seconds=900)
    )
    crawler.router.default_handler(handle)
    await crawler.add_requests(['https://worldafawards.com/results/2025'])
    await crawler.run()
    log('🎉 Finished.')

if __name__ == '__main__':
    asyncio.run(run())
