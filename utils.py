from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import logging

logger = logging.getLogger(__name__)


def wait_for_element(driver, by, value, timeout=20):
    """Wait for an element to be present"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except Exception as e:
        logger.error(f"Error waiting for element {by}={value}: {str(e)}")
        raise


def find_elements(driver, by, value):
    """Find elements by a given locator"""
    try:
        return driver.find_elements(by, value)
    except Exception as e:
        logger.error(f"Error finding elements {by}={value}: {str(e)}")
        raise


def click_element(driver, by, value):
    """Click an element by a given locator"""
    try:
        element = driver.find_element(by, value)
        element.click()
    except Exception as e:
        logger.error(f"Error clicking element {by}={value}: {str(e)}")
        raise
