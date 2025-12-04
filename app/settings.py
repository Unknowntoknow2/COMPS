BOT_NAME = "craigslist_scraper"
SPIDER_MODULES = ["app.spiders"]
NEWSPIDER_MODULE = "app.spiders"
ROBOTSTXT_OBEY = False

# Playwright handler if needed later
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1.0
CONCURRENT_REQUESTS_PER_DOMAIN = 4
LOG_LEVEL = "INFO"

ITEM_PIPELINES = {
    "app.pipelines.supabase_pipeline.SupabasePipeline": 500,
}
