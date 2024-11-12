from scraper import GenericScraper
from config import LAWS_URL


def main():
    # Create scraper instance
    scraper = GenericScraper(LAWS_URL)

    try:
        # Start scraping
        results = scraper.scrape_legislation()
        print(f"Scraped {len(results)} laws successfully")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()
