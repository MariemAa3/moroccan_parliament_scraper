from scraper import GenericScraper
from config import QUESTION_URL


def main():
    # Create scraper instance
    scraper = GenericScraper(QUESTION_URL)

    try:
        # Start scraping
        results = scraper.scrape_question()
        print(f"Scraped {len(results)} laws successfully")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()
