import scrapy
import json

class ClimberSpider(scrapy.Spider):
    name = 'climbers'
    start_urls = ['https://bettybeta.com/bouldering/fontainebleau/']

    seen_climbers = set()
    
    def __init__(self):
        super().__init__()
        self.seen_climbers = set()
        
        # Load the mapping
        with open('../data/raw/ascents/betty_2_bleau_mapping.json', 'r') as f:
            self.betty_2_bleau = json.load(f)
        self.logger.info(f"📂 Loaded {len(self.betty_2_bleau)} boulder mappings!")

    def parse(self, response):
        for sector_link in response.css('li[data-count] a::attr(href)').getall():
            yield response.follow(sector_link, callback=self.parse_sector)
    
    def parse_sector(self, response):
        for boulder_link in response.css('h5.mt-0 a::attr(href)').getall():
            yield response.follow(boulder_link, callback=self.parse_boulder)
    
    def parse_boulder(self, response):
        # Extract all climber links from this boulder
        for climber_link in response.css('a[href*="/bouldering/climber"]::attr(href)').getall():
            # only take matches that match to 'bouldering/climber' pattern
            climber_url = response.urljoin(climber_link)
            # Deduplicate - only scrape each climber once
            if climber_url not in self.seen_climbers:
                self.seen_climbers.add(climber_url)
                yield response.follow(climber_url, callback=self.parse_climber)
    
    def parse_climber(self, response):
        # Extract user info
        name = response.css('h1::text').get().strip()
        climber_url = response.url
        self.logger.info(f"Scraping climber: {name} from {climber_url}")
        
        height_span = response.css('table tr td b:contains("cm")::text').getall()
        height = height_span[0] if len(height_span) > 0 else None
        span = height_span[1] if len(height_span) > 1 else None

        # convert both to integers
        if height is not None:
            height = int(height.replace("cm", "").strip())
        if span is not None:
            span = int(span.replace("cm", "").strip())

        if span is not None and abs(span) < 100: # assume this is the ape calculated by difference
            span = height + span  # convert to cm

        repetitions = []
        for rep in response.css('#ascents div.media-body'):
            try:
                ascent = rep.css('span.data-name::text').get().strip()
                betty_url = rep.css('h5.mt-0 a::attr(href)').get()
                # join with base url if relative
                if betty_url and not betty_url.startswith('http'):
                    betty_url = response.urljoin(betty_url)
                grade = rep.css('span.data-grade::text').get().strip()
                date_raw = rep.xpath('./h6/text()[last()]').get()
                date = ' '.join(date_raw.split()).strip().lstrip(',').strip()
                bleau_link = self.betty_2_bleau.get(betty_url, None) # set None if it doesn't exist on bleau.info

                repetitions.append({
                    'ascent': ascent,
                    'grade': grade,
                    'date': date,
                    'betty_url': betty_url,
                    'bleau_link': bleau_link
                })
            
            except AttributeError as e:
                self.logger.error(f"❌ Error extracting repetition: {e}")
                self.logger.error(f"HTML: {rep.get()}")  # Shows the full HTML of this rep
                self.logger.error(f"Ascent: {rep.css('span.data-name::text').get()}")
                self.logger.error(f"Grade: {rep.css('span.data-grade::text').get()}")
                self.logger.error(f"Date raw: {rep.xpath('./h6/text()[last()]').get()}")
                continue  # Skip this one and continue with next

        # Store temporary climber data
        yield {
            'name': name,
            'url': climber_url,
            'height': height,
            'span': span,
            'repetitions': repetitions
        }
