import scrapy
from bs4 import BeautifulSoup

class CraigslistCarsSpider(scrapy.Spider):
    name = "craigslist_cars"

    def __init__(self, city="sfbay", category="cta", query="", limit=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.city = city
        self.category = category
        self.query = query
        self.limit = int(limit)
        self.count = 0

    def start_requests(self):
        base_url = f"https://{self.city}.craigslist.org/search/{self.category}?query={self.query}"
        yield scrapy.Request(url=base_url, callback=self.parse_list)

    def parse_list(self, response):
        soup = BeautifulSoup(response.text, "lxml")
        for li in soup.select("li.result-row"):
            if self.count >= self.limit:
                break
            pid = li.get("data-pid")
            title_el = li.select_one(".result-title")
            url = title_el["href"] if title_el else None
            title = title_el.get_text(strip=True) if title_el else None
            price_el = li.select_one(".result-price")
            price = price_el.get_text(strip=True) if price_el else None
            date_el = li.select_one("time")
            posted = date_el["datetime"] if date_el else None

            if url:
                self.count += 1
                yield scrapy.Request(
                    url,
                    callback=self.parse_detail,
                    meta={
                        "listing": {
                            "craigslist_id": pid,
                            "title": title,
                            "price": price,
                            "posted": posted,
                            "url": url,
                        }
                    },
                )

        next_page = soup.select_one("a.button.next, a.next")
        if next_page and "href" in next_page.attrs and self.count < self.limit:
            yield response.follow(next_page["href"], callback=self.parse_list)

    def parse_detail(self, response):
        soup = BeautifulSoup(response.text, "lxml")
        listing = response.meta["listing"]
        desc = soup.select_one("#postingbody")
        description = desc.get_text(" ", strip=True) if desc else ""
        attrs = {}
        for group in soup.select("p.attrgroup span"):
            txt = group.get_text(" ", strip=True)
            if ":" in txt:
                k, v = txt.split(":", 1)
                attrs[k.strip()] = v.strip()
            else:
                attrs[txt] = True
        images = [img["src"] for img in soup.select("img") if "src" in img.attrs]
        yield {
            **listing,
            "description": description,
            "attributes": attrs,
            "images": images,
        }
