"""
Standalone integration testing
"""
from selenium.webdriver.common.by import By
from loguru import logger
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from scraper import Scraper
import sys

logger.add("healthcheckerror.log", rotation="1 MB")  # Log file with rotation
url = "https://www.johnedmiston.com/pubsub_depth_cam"
with Scraper(url) as a:
    try:
        a.driver.get(url)
        wait = WebDriverWait(a.driver, 10)
        button = wait.until(EC.element_to_be_clickable(
            (By.ID, 'btn')))

        # trigger photo
        links = a.driver.find_elements(By.CLASS_NAME, "btn")
        out = links[0].click()

        new_element = WebDriverWait(a.driver, 20).until(
            EC.presence_of_element_located((By.ID, "plotly-chart")))

        figure = a.driver.find_element(By.TAG_NAME, 'figure')
        fig = figure.get_attribute('outerHTML')
        logger.info("storage.googleapis found")
        assert "storage.googleapis" in fig
    except:
        logger.exception("Error")
        sys.exit(1)
