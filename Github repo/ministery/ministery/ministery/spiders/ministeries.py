import scrapy
import re


class MinisteriesSpider(scrapy.Spider):
    name = "ministeries"
    allowed_domains = ["fr.wikipedia.org"]
    start_urls = ["https://fr.wikipedia.org/wiki/Gouvernement_Akhannouch_II"]
    
    def parse(self, response):
        yield from self.parse_precedent_minister(response)
    
    def parse_precedent_minister(self, response):
        yield from self.parse_minister_2(response)
        link = response.xpath("/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[1]/div[1]/p[2]/span[1]/a/@href").getall()
        link_2 = response.xpath("/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[1]/div[9]/table[1]/tbody/tr[4]/td/div/ul/li/a/@href").getall()
        for href in link_2:
            yield {
                "from": self.get_id(response.url),
                "to": self.get_id(href)
            }
            yield response.follow(href, callback=self.parse_minister_2)

    def get_id(self, url):
        return re.sub(".*\?id=", "", url)
    
    def parse_minister(self, response):
        for row in response.xpath('//table[contains(@class, "wikitable")][3]//tr[position()>1]'):
            yield {
                'name': row.xpath('.//td[@width="27%"]//text()').get(),
                'title': row.xpath('.//td[@width="60%"]//text()').get(),
                'party': row.xpath('.//td[@width="7%"]//text()').get()
            }

    def parse_minister_2(self, response):
        threshold = 10  # Set your threshold here
        government_name = self.extract_government_name(response.url)

        tables = response.xpath('//table')
        
        for table in tables:
            # Extract the headers
            headers = table.xpath('.//th/text()').getall()
            headers = [header.strip() for header in headers]

            # Check if 'nom' is in headers
            if "Ministre de rattachement" in headers:
                # Extract all rows of the table
                for row in table.xpath('.//tr')[1:]:  # Skip the header row
                    k_title = headers.index('Ministre de rattachement') +1 
                    k_name = headers.index('Nom')+2
                    k_party = headers.index("Parti")+2
                    ministre_de_rattachement = row.xpath(f'td[{k_title}]//text()').get().strip()
                    name = row.xpath(f'td[{k_name}]//text()').get().strip()
                    party = row.xpath(f'td[{k_party}]//text()').get().strip()
                    yield {
                        "name": name,
                        "ministre_de_rattachement":ministre_de_rattachement,
                        "party":party,
                        "government":government_name
                    }
            elif "Nom" in headers and "Ministre de rattachement" not in headers:
                for row in table.xpath('.//tr')[1:]:  # Skip the header row
                    title = row.xpath('td[2]//text()').get('').strip()
                    name = row.xpath('td[4]//a/text()').get('').strip()
                    party = row.xpath('td[5]//a/text()').get('').strip()
                    yield {
                        "name": name,
                        "title":title,
                        "party":party,
                        "government":government_name
                    }

    def extract_government_name(self, url):
        """Extract the government name from the URL"""
        match = re.search(r"/wiki/Gouvernement_(.+)", url)
        if match:
            government = match.group(1).replace("_", " ")
            return government.strip()
        return None


