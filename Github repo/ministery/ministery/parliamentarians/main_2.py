import json
from scraper import GeneralizedParliamentScraper
from config import ANNUARY_URL

def main():
    # Create scraper instance
    scraper = GeneralizedParliamentScraper(ANNUARY_URL)

    try:
        # Start scraping parliamentarians
        results = scraper.scrape()
        print(f"Scraped {len(results)} parliamentarians successfully")
        
        # Save results to a JSON file
        with open("parliamentarians.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print("Results saved to parliamentarians.json")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        # Cleanup resources, like closing the browser
        scraper.cleanup()

if __name__ == "__main__":
    main()
