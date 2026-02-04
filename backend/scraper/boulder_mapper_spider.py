import scrapy
import json

class BoulderMapperSpider(scrapy.Spider):
    name = 'boulder_mapper'
    start_urls = ['https://bettybeta.com/bouldering/fontainebleau/']
    
    def __init__(self):
        super().__init__()
        self.betty_2_bleau = {}
    
    def parse(self, response):
        # Get all sectors
        for sector_link in response.css('li[data-count] a::attr(href)').getall():
            yield response.follow(sector_link, callback=self.parse_sector)
    
    def parse_sector(self, response):
        # Get all boulders
        for boulder_link in response.css('h5.mt-0 a::attr(href)').getall():
            yield response.follow(boulder_link, callback=self.parse_boulder)
    
    def parse_boulder(self, response):
        betty_url = response.url
        bleau_link = response.css('ul li a[href*="bleau.info"]::attr(href)').get()
        
        self.betty_2_bleau[betty_url] = bleau_link
        self.logger.info(f"Mapped: {betty_url} → {bleau_link}")
    
    def closed(self, reason):
        # Save on completion
        with open('../data/raw/ascents/betty_2_bleau_mapping.json', 'w') as f:
            json.dump(self.betty_2_bleau, f, indent=2)
        self.logger.info(f"✅ Saved {len(self.betty_2_bleau)} mappings!")