# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import time
import shutil
from scrapy import signals
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)

# Try to import webdriver-manager; make it None if unavailable so usage is guarded

try:
    from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
except Exception:
    ChromeDriverManager = None
    
class CustomSeleniumMiddleware:
    """
    Selenium middleware compatible with Selenium 4+ (uses Service()).
    
        Supports an optional request.meta['click'] instruction:
        request.meta['click'] = {
        'selector': 'button.load-more',   # CSS selector to click
        'max_clicks': 10,                 # max times to click (stop early if no button)
        'wait_after_click': 1.0,          # seconds to wait after each click
        'wait_until_selector': 'a[href*="/products/"]'  # optional CSS to wait for newly loaded

    Behavior:
    - If SELENIUM_DRIVER_EXECUTABLE_PATH setting is provided and points to an executable, that will be used.
    - Else, if webdriver-manager is installed, it will download and use a matching chromedriver.
    - Else, it will try to find 'chromedriver' on PATH.
    - If none of the above are available, raises a RuntimeError with instructions.
    """

    def __init__(self, driver_name='chrome', driver_path=None, driver_args=None, default_wait=10):
        self.driver_name = driver_name.lower()
        self.driver_path = driver_path
        self.driver_args = driver_args or ['--headless=new', '--no-sandbox', '--disable-dev-shm-usage']
        self.default_wait = default_wait
        self.driver = None
        self.driver = self._create_driver()
        
    @classmethod
    def from_crawler(cls, crawler):
        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME', 'chrome')
        driver_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH', None)
        driver_args = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS', None)
        default_wait = crawler.settings.get('SELENIUM_DEFAULT_WAIT_TIME', crawler.settings.get('SELENIUM_MAX_WAIT_TIME', 10))
        mw = cls(driver_name=driver_name, driver_path=driver_path, driver_args=driver_args, default_wait=default_wait)
        crawler.signals.connect(mw.spider_closed, signal=signals.spider_closed)
        return mw

    def _locate_chromedriver_on_path(self):
        for name in ('chromedriver', 'chromedriver.exe'):
            path = shutil.which(name)
            if path:
                return path
        return None

    def _create_driver(self):
        if self.driver_name != 'chrome':
            raise NotImplementedError("Only 'chrome' is implemented in this middleware.")

        options = Options()
        for arg in self.driver_args:
            try:
                options.add_argument(arg)
            except Exception:
                logger.debug("Failed adding chrome option: %s", arg)

        # Prefer explicit driver_path setting
        if self.driver_path:
            service = Service(self.driver_path)
            logger.info("Using chromedriver from SELENIUM_DRIVER_EXECUTABLE_PATH: %s", self.driver_path)
        else:
            # Use webdriver-manager if available
            if ChromeDriverManager is not None:
                try:
                    driver_binary = ChromeDriverManager().install()
                    service = Service(driver_binary)
                    logger.info("Downloaded chromedriver with webdriver-manager: %s", driver_binary)
                except Exception as e:
                    logger.warning("webdriver-manager failed to install a driver: %s", e)
                    found = self._locate_chromedriver_on_path()
                    if found:
                        service = Service(found)
                        logger.info("Found chromedriver on PATH: %s", found)
                    else:
                        raise RuntimeError(
                            "webdriver-manager failed and no chromedriver found on PATH. "
                            "Set SELENIUM_DRIVER_EXECUTABLE_PATH or install webdriver-manager (pip install webdriver-manager)."
                        )
            else:
                found = self._locate_chromedriver_on_path()
                if found:
                    service = Service(found)
                    logger.info("Found chromedriver on PATH: %s", found)
                else:
                    raise RuntimeError(
                        "webdriver-manager is not installed and SELENIUM_DRIVER_EXECUTABLE_PATH is not set, "
                        "and chromedriver was not found on PATH. "
                        "Install webdriver-manager (pip install webdriver-manager) or set SELENIUM_DRIVER_EXECUTABLE_PATH."
                    )

        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)
        return driver
    # New line added
    def _perform_clicks_if_requested(self, request_meta):
        """
        Read click instruction from request_meta and perform clicks on the page via self.driver.
        Returns True if any clicks were attempted (even if none found).
        """
        click_cfg = request_meta.get('click')
        if not click_cfg:
            return False

        selector = click_cfg.get('selector')
        if not selector:
            return False

        max_clicks = int(click_cfg.get('max_clicks', 10))
        wait_after_click = float(click_cfg.get('wait_after_click', 0.8))
        wait_until_sel = click_cfg.get('wait_until_selector')

        for i in range(max_clicks):
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                elements = []

            if not elements:
                logger.debug("Click loop: no elements found for selector '%s' (iteration %d)", selector, i + 1)
                break

            clicked_any = False
            for el in elements:
                try:
                    # scroll into view then click
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    el.click()
                    clicked_any = True
                except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                    logger.debug("Click attempt failed on selector '%s': %s", selector, e)
                    continue
                except Exception as e:
                    logger.debug("Unexpected click error for selector '%s': %s", selector, e)
                    continue

            if not clicked_any:
                # nothing clickable: break
                break

            # Wait for any async load; prefer explicit selector wait if provided
            if wait_until_sel:
                try:
                    WebDriverWait(self.driver, wait_after_click).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, wait_until_sel)) > 0
                    )
                except Exception:
                    # fallback to sleep if wait fails
                    time.sleep(wait_after_click)
            else:
                time.sleep(wait_after_click)

        return True
    

    def process_request(self, request, spider):
        # Only render pages that explicitly request selenium (SeleniumRequest sets meta['selenium'] = True).
        if not request.meta.get('selenium'):
            return None

        wait_time = request.meta.get('wait_time', self.default_wait)
        wait_until = request.meta.get('wait_until', None)

        try:
            self.driver.get(request.url)
            if wait_until:
                WebDriverWait(self.driver, wait_time).until(wait_until)
            else:
                time.sleep(min(2, wait_time))
                
        except TimeoutException:
            logger.warning("Timeout loading page %s", request.url)
            
        # Optional: perform clicks (load more) if requested via meta
        try:
            self._perform_clicks_if_requested(request.meta)
        except Exception as e:
            logger.debug("Error during click actions: %s", e)
            
            
        body = str.encode(self.driver.page_source)
        return HtmlResponse(url=self.driver.current_url, body=body, encoding='utf-8', request=request)

    def spider_closed(self, spider):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            logger.exception("Error quitting selenium driver")
            