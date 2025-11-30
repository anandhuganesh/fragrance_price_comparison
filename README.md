```markdown
# Fragrance Scraper (Scrapy + Selenium) - Starter

## Project overview

- Scrape fragrance product pages from multiple websites (here 2 websites are used - brandedperfume and samawa).
- Clean & normalize product fields.
- Store locally (SQLite) or push to BigQuery.
- Later: deduplicate / match products across sites and highlight cheapest seller.

This Scrapy project collects product information (at minimum):
- raw_name
- raw_price
- image_url
- url

Key files to know:
- `fragrance_project/items.py` — item fields
- `fragrance_project/settings.py` — main Scrapy settings
- `fragrance_project/middlewares.py` — Custom Selenium middleware 
- `fragrance_project/pipelines.py` — validation & cleaning (price parsing)
- `fragrance_project/spiders/brandedperfume_spider.py` — brandedperfume spider
- `fragrance_project/spiders/samawa_spider.py` — samawa spider
- `fragrance_project/cleaning.py` — helper for parsing numeric prices


Quick start (conda terminal)
1. Create and activate env:

   >>> conda create -n fragrance_env
   >>> conda activate fragrance_env

2. Install dependencies:
   >>> pip install -r requirements.txt

3. Chromedriver:
   - Use webdriver-manager (recommended). In spiders you can initialize via webdriver-manager.
   - Or download chromedriver that matches your Chrome version and set PATH.


4. Create spider project structure:

   Ensure you are in the parent directory: cd fragrance-price-engine
	Create the Scrapy project using the Scrapy command:
   >>> scrapy startproject fragrance_project
   This command automatically creates the following standard structure:


5. Run Spider:	

   From the project root (where `scrapy.cfg` is located):

- Crawl brandedperfume:
 
   >>> scrapy crawl branded_perfume -o brandedperfume.jsonl
  ```

- Crawl samawa:
  
   >>> scrapy crawl samawa -o samawa_raw_data.jsonl


6. Convert json to csv
    Created a python file 'fragrance_project/raw_data/convert_json_to_csv.py' - To convert json file to csv


Important notes
- Respect robots.txt and site terms of service.
- Add appropriate download delays and rotate user agents / proxies for heavy scraping.
- Use Selenium only when necessary; pure Scrapy requests are faster.
- If sites block you, consider residential proxies or throttling.
```