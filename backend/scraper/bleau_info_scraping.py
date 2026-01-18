import scrapy
import re
import time
from scrapy_playwright.page import PageMethod

class ClimberSpider(scrapy.Spider):
    name = 'climbers'

    custom_settings = {
        # 'DOWNLOAD_DELAY': 1,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
    }

    start_urls = ['https://bleau.info/areas_by_region']

    seen_climbers = set()
    
    def parse(self, response):
        for sector_href in response.css('div.area_by_regions a::attr(href)').getall():
            if "toggle" in sector_href:
                continue
            sector_link = response.urljoin(sector_href)
            yield response.follow(sector_link, callback=self.parse_sector)
    
    def parse_sector(self, response):
        for boulder_href in response.css('div.vsr a::attr(href)').getall():
            boulder_link = response.urljoin(boulder_href)
            yield response.follow(boulder_link, callback=self.parse_boulder)
    
    def parse_boulder(self, response):
        # Extract all climber links from this boulder
        for climber_href in response.css('div.repetition a[href*="/profiles"]::attr(href)').getall():
            climber_link = response.urljoin(climber_href)
            # Deduplicate - only scrape each climber once
            if climber_link not in self.seen_climbers:
                self.seen_climbers.add(climber_link)
                yield response.follow(climber_link, callback=self.parse_climber)
    
    def parse_climber(self, response):
        # Extract user info
        name = response.css('h3::text').get().strip()
        self.logger.info(f"Scraping climber: {name} from {response.url}")
        ## Get total ascents count from h4 and extract number
        n_ascents_text = response.css('h4::text').get()
        n_ascents_text = re.search(r'\((\d+)\)', n_ascents_text).group(1) if n_ascents_text else '0'
        n_ascents = int(n_ascents_text) if n_ascents_text else 0
        
        # Get ascents and dates
        repetitions = []
        for rep in response.css('#tab_by_date > div.repetition'):
            date = rep.xpath('./text()[1]').get().strip()
            
            ascent = rep.css('a::text').get().strip()
            grade = rep.xpath('./text()[normalize-space()][last()]').get().strip()  # Last non-empty text
            
            repetitions.append({
                'date': date,
                'ascent': ascent,
                'grade': grade
            })
        n_ascents_displayed = len(repetitions)

        # Extract climber characteristics and split by strong tags
        full_text = response.css('p').get()
        height = re.search(r'<strong>Height:</strong>\s*([0-9.]+)m', full_text)
        span = re.search(r'<strong>Span:</strong>\s*([0-9.]+)m', full_text)
        nationality = re.search(r'<strong>Nationality:</strong>\s*(\w+)', full_text)

        # Convert height and span to cm, and nationality from group
        height = float(height.group(1).replace(',', '.'))*100 if height else None
        span = float(span.group(1).replace(',', '.'))*100 if span else None
        nationality = nationality.group(1) if nationality else None
        
        if n_ascents > n_ascents_displayed:

            yield scrapy.Request(
                url = response.url, 
                callback=self.parse_climber_full, 
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'a.load-more-profile-last-repetitions'),  # Wait for button to appear
                        PageMethod('click', 'a.load-more-profile-last-repetitions'),  # Click it
                        PageMethod('wait_for_selector', 'div.last_repetitions.spinner', state='hidden'),  # Wait for spinner to disappear
                    ],
                    'name': name,
                    'height': height,
                    'span': span,
                    'nationality': nationality, 
                    'n_ascents': n_ascents
                }, 
                headers = {
                'Referer': response.url,
                'X-Requested-With': 'XMLHttpRequest'
                },
                errback=self.errback_climber_full,
                dont_filter=True
            )
        else:
            self.logger.info(f"Total ascents fetched for {name}: {len(repetitions)}/{n_ascents}")
            yield {
                'name': name,
                'url': response.url,
                'height': height,
                'span': span,
                'nationality': nationality,
                'ascents': repetitions,
            }
    def parse_climber_full(self, response):
        # Get info from meta
        name = response.meta['name']
        span = response.meta['span']
        height = response.meta['height']
        nationality = response.meta['nationality']

        # Get ascents and dates
        repetitions = []
        for rep in response.css('#tab_by_date > div.repetition'):
            date = rep.xpath('./text()[1]').get().strip()
            ascent = rep.css('a::text').get().strip()
            grade = rep.xpath('./text()[normalize-space()][last()]').get().strip()  # Last non-empty text
            
            repetitions.append({
                'date': date,
                'ascent': ascent,
                'grade': grade
            })
        n_ascents_scraped = len(repetitions)
        self.logger.info(f"✅ PLAYWRIGHT: Scraped ascents for {name}: {n_ascents_scraped} / {response.meta['n_ascents']}")
        yield {
            'name': name,
            'url': response.url,
            'height': height,
            'span': span,
            'nationality': nationality,
            'repetitions': repetitions
        }
    def errback_climber_full(self, failure):
        self.logger.error(f"Failed to fetch full ascents: {failure.value}")
        self.logger.error(f"Request URL: {failure.request.url}")
