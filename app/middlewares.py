import os, random

class ProxyRotationMiddleware:
    """
    Randomly assigns a proxy from PROXY_POOL env var.
    Example:
      PROXY_POOL=http://user:pass@1.2.3.4:8000,http://user:pass@5.6.7.8:8000
    """

    def __init__(self):
        raw = os.getenv("PROXY_POOL", "")
        self.proxies = [p.strip() for p in raw.split(",") if p.strip()]
        if self.proxies:
            print(f"[ProxyRotationMiddleware] Loaded {len(self.proxies)} proxies.")
        else:
            print("[ProxyRotationMiddleware] No proxies configured; direct connection will be used.")

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        if not self.proxies:
            return
        proxy = random.choice(self.proxies)
        request.meta["proxy"] = proxy
        spider.logger.debug(f"Using proxy: {proxy}")


# ----- Proxy Rotation Middleware -----
DOWNLOADER_MIDDLEWARES.update({
    "app.middlewares.ProxyRotationMiddleware": 410,
})

# Retry and timeout tuning for unstable proxies
RETRY_ENABLED = True
RETRY_TIMES = 3
DOWNLOAD_TIMEOUT = 20
