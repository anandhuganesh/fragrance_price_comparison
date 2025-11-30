# Scrapy settings for fragrance_project project
import os

BOT_NAME = 'fragrance_project'

SPIDER_MODULES = ['fragrance_project.spiders']
NEWSPIDER_MODULE = 'fragrance_project.spiders'

# Obey robots.txt rules (Set to False for Scrapy-Selenium to work in some cases)
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy
CONCURRENT_REQUESTS = 4

# Increase request timeout for dynamic pages
DOWNLOAD_TIMEOUT = 60

# Retry & logging
RETRY_ENABLED = True
RETRY_TIMES = 3

# --- Custom Output Pipeline ---
FEEDS = {
    'raw_data/all_fragrances_raw.jsonl': {
        'format': 'jsonlines',
        'encoding': 'utf8',
        'overwrite': False, # Append data for multiple spiders
    }
}

ITEM_PIPELINES = {
    'fragrance_project.pipelines.FragranceProjectPipeline': 300,
}

# --- Selenium Middleware Configuration ---
"""
DOWNLOADER_MIDDLEWARES = {
    'scrapy_selenium.SeleniumMiddleware': 800,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}
"""
DOWNLOADER_MIDDLEWARES = {
    'fragrance_project.middlewares.CustomSeleniumMiddleware': 800,
}
# 2. Configure the Selenium Driver (MUST match your driver location/type)
# We assume the chromedriver.exe is in the project root path.

SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = None 

SELENIUM_DRIVER_ARGUMENTS = ['--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--window-size=1920,1080']  # '--headless' if using headless mode

# Optionally use Selenium Grid
# SELENIUM_DRIVER_URL = 'http://127.0.0.1:4444/wd/hub'

# Delay (seconds) before Scrapy starts processing the page after loading (crucial for JavaScript loading)
SELENIUM_MAX_WAIT_TIME = 15

# Use a common user agent to prevent being blocked
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

LOG_LEVEL = 'INFO'  # Set to 'DEBUG' for more verbose output