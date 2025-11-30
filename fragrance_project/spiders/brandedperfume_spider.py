import scrapy
from fragrance_project.items import FragranceItem
#Import the Selenium Request Class
from scrapy_selenium import SeleniumRequest 
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import datetime # Import datetime for a reliable timestamp
import logging
import re

logger = logging.getLogger(__name__)

class BrandedPerfumeSpider(scrapy.Spider):
    """
    Scrapes product data from BrandedPerfume.com.
    
    """
    name = 'branded_perfume'
    
    # Starting URL for the main product category
    start_urls = ['https://brandedperfume.com/perfumes/']
    
    def start_requests(self):
        """
        Uses SeleniumRequest to handle dynamic JavaScript content loading.
        """
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                wait_time=15, 
                wait_until=EC.presence_of_element_located((
                    By.CSS_SELECTOR,  
                    "div.ty-grid-list__item" 
                ))
            )

    def parse(self, response):
        """
        Parses the product listing page.
        """
        logger.info(f"[{self.name}] Parsing page: {response.url}")
        # 1. Find all product containers on the page. 
        product_containers = response.css('div.ty-grid-list__item')
        logger.info(f"[{self.name}] Found {len(product_containers)} product containers")
        
        extracted_count = 0 

        for idx, product in enumerate(product_containers):
            item = FragranceItem()
            
            # Extract URL
            url_element = product.css('a.product-title::attr(href)').get()
            item['url'] = response.urljoin(url_element) if url_element else None

            # ----------  Extract Raw Name -----------
            raw_name = product.css('a.product-title::text').get()      
            item['raw_name'] = raw_name.strip() if raw_name else None
            #url = product.css('div.ypi-grid-list__item_body').get()
            
            
            
            # ----------  Extract Raw Price -----------
            
            raw_price = product.css('span.ty-price > span.ty-price-num:nth-child(2)::text').get()
            # Strip whitespace and handle missing price
            if raw_price:
                raw_price = raw_price.strip()
                if not raw_price:
                    raw_price = None
            item['raw_price'] = raw_price 
            
            
            # --- 4. Extract Image URL ---
            
            image_container = product.css('div.ty-grid-list__image')
            image_url = image_container.css('img::attr(data-src)').get()
            if not image_url:
                image_url = image_container.css('img::attr(src)').get()
            item['image_url'] = response.urljoin(image_url) if image_url else None
            
            # Add metadata
            item['website_source'] = self.name
            item['timestamp'] = datetime.datetime.now().isoformat()

            if not (item['raw_name'] and item['raw_price'] and item['url']):
                logger.debug(f"[{self.name}] Skipped product {idx}: name={item['raw_name']}, price={item['raw_price']}, url={item['url']}")
            else:
                extracted_count += 1
                yield item
        
        logger.info(f"[{self.name}] Extracted {extracted_count} valid items from this page")

        # --- FOLLOW PAGINATION LINKS ---
        next_page = response.css('a.ty-pagination__next::attr(href)').get()
        
        if next_page is not None:
            logger.info(f"[{self.name}] Following pagination: {next_page}")
            yield SeleniumRequest(
                url=response.urljoin(next_page),
                callback=self.parse,
                wait_time=15, 
                wait_until=EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "div.ty-grid-list__item"
                ))
            )
            