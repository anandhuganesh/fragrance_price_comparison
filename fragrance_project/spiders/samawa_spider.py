import scrapy
from fragrance_project.items import FragranceItem
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import datetime
import logging

logger = logging.getLogger(__name__)


class SamawaSpider(scrapy.Spider):
    """
    Scrapes product data from Samawa.ae collection pages.
    Uses the project's CustomSeleniumMiddleware (meta['selenium']=True) and
    instructs it to click any "load more" buttons so product cards are loaded.
    """
    name = 'samawa'
    start_urls = ['https://samawa.ae/collections/perfume-spray?includeOutOfStock=true']

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
    }

    def start_requests(self):
        wait_cond = EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/products/']"))
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "selenium": True,
                    "wait_time": 12,
                    "wait_until": wait_cond,
                    "click": {
                        "selector": "button.sparq-load-more, button.load-more, button.btn-pink, div.sparq-load-more button",
                        "max_clicks": 50,
                        "wait_after_click": 1.0,
                        "wait_until_selector": "a[href*='/products/']"
                    }
                },
            )

    def parse(self, response):
        """
        Prefer to collect product links site-wide first. If none found, fall back
        to extracting link per product card.
        """
        # Trying broad link collection (Shopify-like /products/ pattern)
        links = response.css("a[href*='/products/']::attr(href)").getall()
        links = [response.urljoin(h) for h in dict.fromkeys(links) if h]

        if links:
            logger.info("[%s] Found %d product links on %s", self.name, len(links), response.url)
            for href in links:
                yield scrapy.Request(
                    url=href,
                    callback=self.parse_product,
                    meta={
                        "selenium": True,
                        "wait_time": 8,
                        "wait_until": EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .product-single__title"))
                    },
                )
            return

        # Fallback: iterate per product card and extract details from listing
        product_containers = response.css('div.sparq-card')
        if not product_containers:
            # Save rendered page for inspection (helpful if selectors still miss)
            try:
                open("debug_samawa.html", "wb").write(response.body)
                logger.warning("[%s] No product containers found; saved rendered page to debug_samawa.html", self.name)
            except Exception:
                logger.warning("[%s] No product containers found and could not save debug file", self.name)
            return

        for product in product_containers:
            item = FragranceItem()

            href = product.css("a.sparq-loop-product::attr(href), a.sparq-title::attr(href), a[href*='/products/']::attr(href)").get()
            item['url'] = response.urljoin(href) if href else None

            raw_name = product.css('a.sparq-title::text, .sparq-title::text').get()
            item['raw_name'] = raw_name.strip() if raw_name else None

            raw_price = product.css('span.money.sq-price::text, span.money.sq-price::text').get()
            item['raw_price'] = raw_price.strip() if raw_price else None

            image_url = product.css('a.sparq-loop-product img::attr(src), img.grid-view-item__image::attr(src), img::attr(src)').get()
            item['image_url'] = response.urljoin(image_url) if image_url else None

            item['website_source'] = self.name
            item['timestamp'] = datetime.datetime.utcnow().isoformat() + "Z"

            # Only yield items that have at least name and url (price optional)
            if item.get('raw_name') and item.get('url'):
                yield item
            else:
                logger.debug("[%s] Skipped product in listing (missing name or url). name=%r url=%r price=%r",
                            self.name, item.get('raw_name'), item.get('url'), item.get('raw_price'))

    def parse_product(self, response):
        """
        Parse individual product page and extract required fields.
        """
        item = FragranceItem()
        item['url'] = response.url

        title = (
            response.css("h1.product-single__title::text").get()
            or response.css("h1::text").get()
            or response.css("meta[property='og:title']::attr(content)").get()
        )
        item['raw_name'] = title.strip() if title else None

        price_meta = (
            response.css("meta[property='product:price:amount']::attr(content)").get()
            or response.css("meta[itemprop='price']::attr(content)").get()
        )
        if price_meta and price_meta.strip():
            item['raw_price'] = price_meta.strip()
        else:
            price_text = (
                response.css(".product-single__price .price::text").get()
                or response.css(".price::text").get()
                or response.css(".sparq-price .money::text").get()
            )
            item['raw_price'] = price_text.strip() if price_text else None

        image = (
            response.css("meta[property='og:image']::attr(content)").get()
            or response.css(".product-single__photo img::attr(src)").get()
            or response.css(".product-gallery img::attr(src)").get()
            or response.css("img::attr(src)").get()
        )
        item['image_url'] = response.urljoin(image) if image else None

        item['website_source'] = self.name
        item['timestamp'] = datetime.datetime.utcnow().isoformat() + "Z"

        if not item.get('raw_name') or not item.get('url'):
            logger.debug("[%s] Incomplete product scraped: name=%r url=%r price=%r",
                        self.name, item.get('raw_name'), item.get('url'), item.get('raw_price'))

        yield item