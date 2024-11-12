import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import time
import random
from fake_useragent import UserAgent
import logging
import atexit
import json
from urllib.parse import unquote
import os
from utils import wait_for_element, find_elements, click_element

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class GenericScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.driver = None
        self.logger = logging.getLogger(__name__)
        atexit.register(self.cleanup)

    def cleanup(self):
        """Safely cleanup driver resources"""
        try:
            if hasattr(self, "driver") and self.driver is not None:
                self.logger.info("Cleaning up driver resources...")
                try:
                    self.driver.close()
                except Exception:
                    pass
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def get_driver(self):
        """Initialize and return an undetected Chrome driver"""
        try:
            options = uc.ChromeOptions()

            ua = UserAgent()
            user_agent = ua.random

            options.add_argument(f"user-agent={user_agent}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--enable-javascript")

            window_sizes = [(1366, 768), (1920, 1080), (1536, 864)]
            random_size = random.choice(window_sizes)
            options.add_argument(f"--window-size={random_size[0]},{random_size[1]}")

            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(random.randint(30, 40))

            return driver

        except Exception as e:
            self.logger.error(f"Failed to initialize driver: {str(e)}")
            raise

    def wait_for_page_load(self):
        """Wait for page to load with random delays"""
        try:
            time.sleep(random.uniform(2, 4))
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            self.logger.error(f"Error while waiting for page load: {str(e)}")
            raise

    def get_legislation_links(self):
        """Get links for different types of legislation"""
        try:
            wait_for_element(self.driver, By.CSS_SELECTOR, "p a")

            self.legislation_links = {
                "projets": None,
                "propositions": None,
                "adopted": None,
                "last_page": None,
            }

            links = find_elements(self.driver, By.CSS_SELECTOR, "p a")

            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip().lower()

                    if "projets de loi" in text:
                        self.legislation_links["projets"] = href
                        self.logger.info(f"Found projets link: {href}")
                    elif "propositions de loi" in text:
                        self.legislation_links["propositions"] = href
                        self.logger.info(f"Found propositions link: {href}")
                    elif "textes de loi" in text:
                        self.legislation_links["adopted"] = href
                        self.logger.info(f"Found adopted texts link: {href}")

                except Exception as e:
                    self.logger.error(f"Error processing link: {str(e)}")
                    continue

            try:
                last_page_link = self.driver.find_element(
                    By.CSS_SELECTOR, ".pagination-container .last-item a"
                )
                self.legislation_links["last_page"] = last_page_link.get_attribute(
                    "href"
                )
                self.logger.info(
                    f"Found last page link: {self.legislation_links['last_page']}"
                )
            except NoSuchElementException:
                self.logger.info("No last page link found.")

            return self.legislation_links

        except Exception as e:
            self.logger.error(f"Error in get_legislation_links: {str(e)}")
            return {}

    def extract_law_info(self):
        laws = []
        current_page = 1
        last_page = None

        while True:
            self.logger.info(f"Scraping page {current_page}")

            # Wait for the law items to be present
            wait_for_element(self.driver, By.CSS_SELECTOR, ".col-md-6.col-lg-4.mb-4")

            # Find all law items
            law_items = find_elements(
                self.driver, By.CSS_SELECTOR, ".col-md-6.col-lg-4.mb-4"
            )

            for item in law_items:
                try:
                    # Find the link and title within each item
                    link_element = item.find_element(
                        By.CSS_SELECTOR, "h3.questionss_group a"
                    )
                    href = link_element.get_attribute("href")
                    title = link_element.text.strip()

                    # Decode URL-encoded title from href if title is empty
                    if not title and href:
                        try:
                            encoded_title = href.split("/")[-1]
                            title = unquote(encoded_title)
                        except:
                            title = "Unknown Title"

                    if href and title:
                        laws.append({"title": title, "url": href})

                except Exception as e:
                    self.logger.error(f"Error extracting law info: {str(e)}")
                    continue

            try:
                next_page_link = self.driver.find_element(
                    By.XPATH, "//a[@class='page-link' and contains(text(), 'Suivant')]"
                )
                if last_page is None:
                    current_page_link = self.driver.find_element(
                        By.CSS_SELECTOR, ".pagination-container .active a"
                    )
                    last_page = current_page_link.get_attribute("href")
                next_page_link.click()
                current_page += 1
                self.wait_for_page_load()
            except NoSuchElementException:
                self.logger.info("No more pages to navigate.")
                break
            except Exception as e:
                self.logger.error(f"Error navigating to the next page: {str(e)}")
                break

        return laws

    def extract_adopted_law_info(self, adopted_laws_link):
        laws = []
        legislature_links = self.get_legislature_links(adopted_laws_link)

        for legislature_id, legislature_link in legislature_links.items():
            self.logger.info(f"Scraping adopted laws for legislature {legislature_id}")
            self.driver.get(legislature_link)
            self.wait_for_page_load()

            current_page = 1
            last_page = None
            last_date = None

            while True:
                self.logger.info(f"Scraping page {current_page}")

                # Wait for the law items to be present
                wait_for_element(
                    self.driver, By.CSS_SELECTOR, ".col-md-6.col-lg-4.mb-4"
                )

                # Find all date headers
                date_elements = find_elements(
                    self.driver, By.CSS_SELECTOR, "h2.sorting_date"
                )

                if date_elements:
                    last_date = date_elements[-1].text.strip()

                # Find all law items
                law_items = find_elements(
                    self.driver, By.CSS_SELECTOR, ".col-md-6.col-lg-4.mb-4"
                )

                for item in law_items:
                    try:
                        # Find the link and title within each item
                        link_element = item.find_element(
                            By.CSS_SELECTOR, "h3.questionss_group a"
                        )
                        href = link_element.get_attribute("href")
                        title = link_element.text.strip()

                        # Decode URL-encoded title from href if title is empty
                        if not title and href:
                            try:
                                encoded_title = href.split("/")[-1]
                                title = unquote(encoded_title)
                            except:
                                title = "Unknown Title"

                        if href and title:
                            laws.append(
                                {
                                    "title": title,
                                    "url": href,
                                    "date": last_date,
                                    "legislature_id": legislature_id,
                                }
                            )

                    except Exception as e:
                        self.logger.error(
                            f"Error extracting adopted law info: {str(e)}"
                        )
                        continue

                try:
                    next_page_link = self.driver.find_element(
                        By.XPATH,
                        "//a[@class='page-link' and contains(text(), 'Suivant')]",
                    )
                    if last_page is None:
                        current_page_link = self.driver.find_element(
                            By.CSS_SELECTOR, ".pagination-container .active a"
                        )
                        last_page = current_page_link.get_attribute("href")
                    next_page_link.click()
                    current_page += 1
                    self.wait_for_page_load()
                except NoSuchElementException:
                    self.logger.info("No more pages to navigate.")
                    break
                except Exception as e:
                    self.logger.error(f"Error navigating to the next page: {str(e)}")
                    break

        return laws

    def get_legislature_links(self, adopted_laws_link):
        """Get links for different legislative periods"""
        try:
            legislature_links = {}

            # Find the legislature selection dropdown
            wait_for_element(
                self.driver,
                By.CSS_SELECTOR,
                "select[name='field_legislature_target_id_1']",
            )
            legislature_dropdown = self.driver.find_element(
                By.CSS_SELECTOR, "select[name='field_legislature_target_id_1']"
            )
            legislature_select = Select(legislature_dropdown)

            # Iterate through the dropdown options and generate the links
            for option in legislature_select.options:
                option_text = option.text.strip()
                option_value = option.get_attribute("value")
                if option_value:
                    year = int(option_text.split("-")[0])
                    if year >= 2011:
                        # Generate the URL for the current legislative period
                        current_url = f"{adopted_laws_link}?body_value=&field_legislature_target_id_1={option_value}&field_annee_legislative_target_id=All&field_nature_loi_target_id=All"
                        legislature_links[option_value] = current_url

            return legislature_links

        except Exception as e:
            self.logger.error(f"Error getting legislature links: {str(e)}")
            return {}

    def save_to_json(self, data, filename):
        """Save the scraped data to a JSON file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Data successfully saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {str(e)}")

    def scrape_legislation(self):
        try:
            self.logger.info("Starting scraping process...")

            # Initialize driver if not already done
            if self.driver is None:
                self.driver = self.get_driver()

            # Navigate to base URL
            self.logger.info(f"Accessing URL: {self.base_url}")
            self.driver.get(self.base_url)
            self.wait_for_page_load()

            # Get legislation links
            links = self.get_legislation_links()
            self.logger.info(f"Found links: {links}")

            all_laws = {}

            # Navigate to projets de loi page
            if links.get("projets"):
                self.driver.get(links["projets"])
                self.wait_for_page_load()

                # Extract law information
                laws = self.extract_law_info()

                # Save to JSON
                if laws:
                    all_laws["projets_de_loi"] = laws
                    self.save_to_json(
                        {"projets_de_loi": laws}, "moroccan_legislation.json"
                    )

            # Navigate to propositions de loi page
            if links.get("propositions"):
                self.driver.get(links["propositions"])
                self.wait_for_page_load()

                # Extract law information
                laws = self.extract_law_info()

                # Save to JSON
                if laws:
                    all_laws["propositions_de_loi"] = laws
                    self.save_to_json(
                        {"propositions_de_loi": laws}, "moroccan_legislation.json"
                    )

            # Navigate to textes de loi page and extract for different legislatures
            if links.get("adopted"):
                self.driver.get(links["adopted"])
                self.wait_for_page_load()

                # Extract law information for each legislature
                laws = self.extract_adopted_law_info(links["adopted"])
                if laws:
                    all_laws["textes_de_loi"] = laws
                    self.save_to_json(
                        {"textes_de_loi": laws}, "moroccan_legislation.json"
                    )

            # Save all laws to a single JSON file
            if all_laws:
                self.save_to_json(all_laws, "moroccan_legislation_all.json")

            return all_laws

        except Exception as e:
            self.logger.error(f"Error in scraping process: {str(e)}")
            return []
        finally:
            self.cleanup()
