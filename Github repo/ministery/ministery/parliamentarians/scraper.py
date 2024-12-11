import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import json
import logging
import time
import random
from fake_useragent import UserAgent
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class GeneralizedParliamentScraperArabic:
    def __init__(self, base_url):
        self.base_url = base_url
        self.driver = None
        self.logger = logging.getLogger(__name__)
        atexit.register(self.cleanup)  # Ensure cleanup after scraping

    def cleanup(self):
        """Safely cleanup driver resources"""
        if self.driver:
            self.logger.info("Cleaning up driver resources...")
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Error during cleanup: {str(e)}")
            self.driver = None

    def get_driver(self):
        """Initialize and return an undetected Chrome driver"""
        try:
            options = uc.ChromeOptions()
            ua = UserAgent()
            user_agent = ua.random

            # Set Chrome options
            options.add_argument(f"user-agent={user_agent}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--enable-javascript")

            # Set a random window size to simulate real browsing
            window_sizes = [(1366, 768), (1920, 1080), (1536, 864)]
            random_size = random.choice(window_sizes)
            options.add_argument(f"--window-size={random_size[0]},{random_size[1]}")

            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(random.randint(30, 40))

            return driver
        except Exception as e:
            self.logger.error(f"Failed to initialize driver: {str(e)}")
            raise

    def wait_for_element(self, by, value, timeout=30):
        """Wait until the element is visible on the page."""
        WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((by, value)))

    def extract_parliamentarians_from_page(self):
        """Dynamically extracts all entries for parliamentarians on the current page (Arabic version)."""
        parliamentarians = []
        try:
            self.wait_for_element(By.CSS_SELECTOR, "div.filter-result-wrp")
            
            # Extract all parliamentarian cards on the page
            parliamentarian_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.filter-result-wrp > div.f-result-list.row > div")

            if not parliamentarian_cards:
                self.logger.warning("No parliamentarian cards found on the page.")

            # Loop through all the cards and extract details
            for card in parliamentarian_cards:
                try:
                    # Extract the name
                    name_element = card.find_element(By.CSS_SELECTOR, "span.q-name > a")
                    name = name_element.text.strip()

                    # Extract the party
                    party_element = card.find_element(By.CSS_SELECTOR, "span:nth-child(2)")
                    party = party_element.text.strip()

                    # Extract the function
                    function_element = card.find_element(By.CSS_SELECTOR, "a:nth-child(3) > span")
                    function = function_element.text.strip()

                    # Add extracted data to the list
                    parliamentarians.append({"name": name, "party": party, "function": function})

                except NoSuchElementException as e:
                    self.logger.warning(f"Missing data for a parliamentarian: {str(e)}")
                    continue  # If any data is missing, continue with the next card

        except Exception as e:
            self.logger.error(f"Error extracting parliamentarians: {str(e)}")

        return parliamentarians

    def go_to_next_page(self, current_page_number):
        """Navigate to the next page based on the current page number."""
        try:
            # Construct the next page URL based on the current page number
            next_page_number = current_page_number + 1
            if next_page_number > 33:  # Only navigate up to page 33
                self.logger.info("Reached the last page (page 33).")
                return None  # Stop if we've reached page 33

            # Generate the next page URL
            next_page_url = f"{self.base_url}?page={next_page_number}"

            self.logger.info(f"Navigating to the next page: {next_page_url}")
            self.driver.get(next_page_url)  # Navigate to the next page
            time.sleep(random.uniform(3, 5))  # Allow time for the page to load
            return next_page_number  # Return the new page number

        except Exception as e:
            self.logger.error(f"Error navigating to the next page: {str(e)}")
            return None

    def save_to_json(self, data, filename):
        """Save data to a JSON file."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Data successfully saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {str(e)}")

    def scrape(self):
        """Main scraping function that iterates through all pages (Arabic version)."""
        all_parliamentarians = []
        try:
            self.driver = self.get_driver()
            self.driver.get(self.base_url)
            time.sleep(random.uniform(3, 5))  # Allow time for the page to load

            for page_number in range(1, 34):  # Loop through pages 1 to 33
                self.logger.info(f"Extracting parliamentarian information from page {page_number}...")
                page_data = self.extract_parliamentarians_from_page()
                all_parliamentarians.extend(page_data)

                # Navigate to the next page
                next_page_number = self.go_to_next_page(page_number)
                if next_page_number is None:
                    break  # Stop if we reach the last page

            self.save_to_json(all_parliamentarians, "parliamentarians_arabic_2021_2026.json")
            self.logger.info("Scraping completed successfully.")
            return all_parliamentarians

        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            return []
        finally:
            self.cleanup()

if __name__ == "__main__":
    BASE_URL_AR = "https://www.chambredesrepresentants.ma/ar/%D8%AF%D9%84%D9%8A%D9%84-%D8%A3%D8%B9%D8%B6%D8%A7%D8%A1-%D9%85%D8%AC%D9%84%D8%B3-%D8%A7%D9%84%D9%86%D9%88%D8%A7%D8%A8/2021-2026/"
    scraper_ar = GeneralizedParliamentScraperArabic(BASE_URL_AR)
    parliamentarians_ar = scraper_ar.scrape()
    print(parliamentarians_ar)
