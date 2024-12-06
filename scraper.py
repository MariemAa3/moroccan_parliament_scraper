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
            wait_for_element(
                self.driver, By.CSS_SELECTOR, ".dropdown-menu.multi-column.columns-3"
            )

            self.legislation_links = {
                "projets": None,
                "propositions": None,
                "adopted": None,
                "last_page": None,
            }

            legislation_dropdown = self.driver.find_element(
                By.XPATH, "//a[contains(text(), 'التشريع')]/following-sibling::div"
            )
            links = legislation_dropdown.find_elements(
                By.CSS_SELECTOR, "ul.multi-column-dropdown li a"
            )

            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.get_attribute("innerText").strip()
                    self.logger.info(f"Found link: {text} -> {href}")

                    self.logger.info(
                        f"Expected text: مشاريع القوانين, مقترحات القوانين, النصوص المصادق عليها"
                    )
                    self.logger.info(f"Extracted text: {text}")

                    if "مشاريع القوانين" in text:
                        self.legislation_links["projets"] = href
                        self.logger.info(f"Found projets link: {href}")
                    elif "مقترحات القوانين" in text:
                        self.legislation_links["propositions"] = href
                        self.logger.info(f"Found propositions link: {href}")
                    elif "النصوص المصادق عليها" in text:
                        self.legislation_links["adopted"] = href
                        self.logger.info(f"Found adopted texts link: {href}")

                except Exception as e:
                    self.logger.error(f"Error processing link: {str(e)}")
                    continue

            # self.logger.info(f"Found links: {self.legislation_links}")
            return self.legislation_links

        except Exception as e:
            self.logger.error(f"Error in get_legislation_links: {str(e)}")
            return {}

    def extract_law_info(self, law_type):
        """Extract law information with simplified output format"""
        laws = []
        current_page = 1

        while True:
            self.logger.info(f"Scraping page {current_page} for {law_type}")

            try:
                wait_for_element(
                    self.driver, By.CSS_SELECTOR, ".col-md-6.col-lg-4.mb-4", timeout=20
                )
                current_page_url = self.driver.current_url
                law_items = find_elements(
                    self.driver, By.CSS_SELECTOR, ".col-md-6.col-lg-4.mb-4"
                )

                if not law_items:
                    self.logger.warning(f"No law items found on page {current_page}")
                    break

                page_laws = []
                for item in law_items:
                    try:
                        law_details = {"type": law_type, "readings": []}

                        link_element = item.find_element(
                            By.CSS_SELECTOR, "h3.questionss_group a"
                        )
                        law_url = link_element.get_attribute("href")
                        law_title = link_element.find_element(
                            By.CSS_SELECTOR, "p"
                        ).text.strip()

                        law_details.update({"title": law_title, "url": law_url})

                        page_laws.append(law_details)

                    except Exception as e:
                        self.logger.error(f"Error extracting basic law info: {str(e)}")
                        continue

                for law in page_laws:
                    try:
                        # self.logger.info(f"Navigating to law page: {law['url']}")
                        self.driver.get(law["url"])
                        self.wait_for_page_load()
                        time.sleep(random.uniform(2, 3))

                        reading_sections = find_elements(
                            self.driver, By.CSS_SELECTOR, ".dp-section"
                        )

                        for section in reading_sections:
                            reading_data = {}

                            try:
                                reading_title = section.find_element(
                                    By.CSS_SELECTOR, ".section-title"
                                ).text.strip()
                                reading_data["reading"] = reading_title
                            except NoSuchElementException:
                                continue

                            blocks = section.find_elements(By.CSS_SELECTOR, ".dp-block")

                            for block in blocks:
                                try:
                                    block_type = block.find_element(
                                        By.CSS_SELECTOR, ".dp-block-l span"
                                    ).text.strip()
                                    details = block.find_elements(
                                        By.CSS_SELECTOR, ".dp-block-r span"
                                    )

                                    if "مكتب مجلس النواب" in block_type:
                                        for detail in details:
                                            text = detail.text.strip()
                                            if "تاريخ إحالته على المجلس" in text:
                                                reading_data["deposit_date"] = (
                                                    text.split(
                                                        "تاريخ إحالته على المجلس:"
                                                    )[-1].strip()
                                                )

                                    elif "اللجنة" in block_type:
                                        for detail in details:
                                            text = detail.text.strip()
                                            if "تمت إحالته على لجنة" in text:
                                                commission_name = (
                                                    text.split("تمت إحالته على لجنة")[
                                                        -1
                                                    ]
                                                    .split("في")[0]
                                                    .strip()
                                                )
                                                reading_data["commission"] = (
                                                    commission_name
                                                )

                                    elif "الجلسة العامة" in block_type:
                                        for detail in details:
                                            text = detail.text.strip()
                                            if "نتيجة التصويت" in text:
                                                vote_data = {}
                                                vote_text = text.split("نتيجة التصويت")[
                                                    -1
                                                ].strip()

                                                if "الإجماع" in vote_text:
                                                    vote_data["unanimous"] = True
                                                else:
                                                    import re

                                                    yes_match = re.search(
                                                        r"الموافقون\s*[:：]\s*(\d+)",
                                                        vote_text,
                                                    )
                                                    if yes_match:
                                                        vote_data["yes"] = int(
                                                            yes_match.group(1)
                                                        )

                                                    no_match = re.search(
                                                        r"المعارضون\s*[:：]\s*(\d+)",
                                                        vote_text,
                                                    )
                                                    if no_match:
                                                        vote_data["no"] = int(
                                                            no_match.group(1)
                                                        )

                                                    abstain_match = re.search(
                                                        r"الممتنعون\s*[:：]\s*(\d+|لا أحد)",
                                                        vote_text,
                                                    )
                                                    if abstain_match:
                                                        abstain_value = (
                                                            abstain_match.group(1)
                                                        )
                                                        vote_data["abstain"] = (
                                                            0
                                                            if abstain_value == "لا أحد"
                                                            else int(abstain_value)
                                                        )

                                                    if "رفضه مجلس النواب" in vote_text:
                                                        vote_data["rejected"] = True
                                                    elif (
                                                        "صادقه مجلس النواب" in vote_text
                                                    ):
                                                        vote_data["approved"] = True

                                                if vote_data:
                                                    reading_data["vote"] = vote_data

                                except NoSuchElementException:
                                    continue

                            if reading_data.get("reading"):
                                law["readings"].append(reading_data)

                        laws.append(law)

                    except Exception as e:
                        self.logger.error(f"Error processing law details: {str(e)}")
                        laws.append(law)
                        continue

                    finally:
                        self.driver.get(current_page_url)
                        self.wait_for_page_load()
                        time.sleep(random.uniform(1, 2))

                try:
                    next_button = self.driver.find_element(
                        By.XPATH,
                        "//a[@class='page-link' and contains(text(), 'التالي')]",
                    )
                    if not next_button.is_enabled():
                        break
                    next_button.click()
                    current_page += 1
                    self.wait_for_page_load()
                    time.sleep(random.uniform(1, 2))
                except NoSuchElementException:
                    self.logger.info("No more pages to navigate.")
                    break
                except Exception as e:
                    self.logger.error(f"Error navigating to next page: {str(e)}")
                    break

            except Exception as e:
                self.logger.error(f"Error processing page {current_page}: {str(e)}")
                break

        return laws

    def extract_adopted_law_info(self, adopted_laws_link):
        laws = []
        legislature_links = self.get_legislature_links(adopted_laws_link)

        for legislature_period, legislature_link in legislature_links.items():
            self.logger.info(
                f"Scraping adopted laws for legislature period {legislature_period}"
            )
            self.driver.get(legislature_link)
            self.wait_for_page_load()

            current_page = 1
            last_date = None

            while True:
                self.logger.info(f"Scraping page {current_page}")

                wait_for_element(
                    self.driver, By.CSS_SELECTOR, ".col-md-6.col-lg-4.mb-4"
                )

                date_elements = find_elements(
                    self.driver, By.CSS_SELECTOR, "h2.sorting_date"
                )

                if date_elements:
                    last_date = date_elements[-1].text.strip()

                law_items = find_elements(
                    self.driver, By.CSS_SELECTOR, ".col-md-6.col-lg-4.mb-4"
                )

                for item in law_items:
                    try:
                        link_element = item.find_element(
                            By.CSS_SELECTOR, "h3.questionss_group a"
                        )
                        href = link_element.get_attribute("href")
                        title = link_element.text.strip()

                        if not title and href:
                            try:
                                encoded_title = href.split("/")[-1]
                                title = unquote(encoded_title)
                            except:
                                title = "Unknown Title"

                        commission_element = item.find_element(
                            By.CSS_SELECTOR, ".lw-link span"
                        )
                        commission = (
                            commission_element.text.strip()
                            if commission_element
                            else "Unknown Commission"
                        )

                        if href and title:
                            laws.append(
                                {
                                    "title": title,
                                    "url": href,
                                    "date": last_date,
                                    "legislature_period": legislature_period,
                                    "commission": commission,
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
                        "//a[@class='page-link' and contains(text(), 'التالي')]",
                    )
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
        """Get links for different legislature periods"""
        try:
            wait_for_element(
                self.driver, By.CSS_SELECTOR, ".dropdown-menu.multi-column.columns-3"
            )

            legislature_links = {}

            legislature_dropdown = self.driver.find_element(
                By.CSS_SELECTOR, "select[name='field_legislature_target_id_1']"
            )
            legislature_select = Select(legislature_dropdown)

            for option in legislature_select.options:
                option_text = option.text.strip()
                option_value = option.get_attribute("value")
                if option_value:
                    year = int(option_text.split("-")[0])
                    if year >= 2011:
                        current_url = f"{adopted_laws_link}?body_value=&field_legislature_target_id_1={option_value}&field_annee_legislative_target_id=All&field_nature_loi_target_id=All"
                        legislature_links[option_text] = current_url

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

            if self.driver is None:
                self.driver = self.get_driver()

            self.logger.info(f"Accessing URL: {self.base_url}")
            self.driver.get(self.base_url)
            self.wait_for_page_load()

            links = self.get_legislation_links()
            self.logger.info(f"Found links: {links}")

            all_laws = {}

            if links.get("projets"):
                self.driver.get(links["projets"])
                self.wait_for_page_load()

                laws = self.extract_law_info("projets")

                if laws:
                    all_laws["projets_de_loi"] = laws
                    self.save_to_json(
                        {"projets_de_loi": laws}, "moroccan_legislation.json"
                    )

            if links.get("propositions"):
                self.driver.get(links["propositions"])
                self.wait_for_page_load()

                laws = self.extract_law_info("propositions")

                if laws:
                    all_laws["propositions_de_loi"] = laws
                    self.save_to_json(
                        {"propositions_de_loi": laws}, "moroccan_legislation.json"
                    )

            if links.get("adopted"):
                self.driver.get(links["adopted"])
                self.wait_for_page_load()

                laws = self.extract_adopted_law_info(links["adopted"])
                if laws:
                    all_laws["textes_de_loi"] = laws
                    self.save_to_json(
                        {"textes_de_loi": laws}, "moroccan_legislation.json"
                    )

            if all_laws:
                self.save_to_json(all_laws, "moroccan_legislation_all.json")

            return all_laws

        except Exception as e:
            self.logger.error(f"Error in scraping process: {str(e)}")
            return []
        finally:
            self.cleanup()
