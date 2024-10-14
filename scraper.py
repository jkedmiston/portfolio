from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager


class Scraper(object):
    def __init__(self, url):
        self.url = url
        fp = webdriver.FirefoxProfile()
        # Avoid startup screen
        fp.set_preference("browser.startup.homepage_override.mstone", "ignore")
        fp.set_preference(
            "startup.homepage_welcome_url.additional",  "about:blank")
        from selenium.webdriver.firefox.options import Options
        args = Options()
        args.headless = True
        self.driver = webdriver.Firefox(firefox_profile=fp,
                                        options=args,
                                        executable_path=GeckoDriverManager().install())
        self.driver.set_window_size(1120, 550)

    def scrape_profile(self):
        self.driver.get(self.url)
        print(self.driver.title)
        self.driver.close()

    def scrape(self):
        self.scrape_profile()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()
