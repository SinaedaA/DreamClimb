import scrapy
import re
import time
from scrapy_playwright.page import PageMethod
from utils import extract_bleau_repetitions, extract_bleau_climber_basics

class ClimberSpider(scrapy.Spider):
    name = 'bleau_ascents'

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
        basic_info = extract_bleau_climber_basics(response) # returns: name, n_ascents, profile_url, height, span, nationality
        repetitions = extract_bleau_repetitions(response) # modified_date param only for scraping existing users (defaults to None)

        n_ascents_displayed = len(repetitions)
        
        if n_ascents_displayed < basic_info['n_ascents']:
            self.logger.warning(f"⚠️ Displayed ascents ({n_ascents_displayed}) less than total ascents ({basic_info['n_ascents']}) for {response.url}.")
            yield scrapy.Request(
                url = response.url, 
                callback=self.parse_bleau_climber_full, 
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'a.load-more-profile-last-repetitions'),  # Wait for button to appear
                        PageMethod('click', 'a.load-more-profile-last-repetitions'),  # Click it
                        PageMethod('wait_for_selector', 'div.last_repetitions.spinner', state='hidden'),  # Wait for spinner to disappear
                    ],
                    'name': basic_info['name'],
                    'height': basic_info['height'],
                    'span': basic_info['span'],
                    'nationality': basic_info['nationality'], 
                    'n_ascents': basic_info['n_ascents']
                }, 
                headers = {
                'Referer': response.url,
                'X-Requested-With': 'XMLHttpRequest'
                },
                errback=self.errback_climber_full,
                dont_filter=True
            )
        else:
            self.logger.info(f"Total ascents fetched for {basic_info['name']}: {len(repetitions)}/{basic_info['n_ascents']}")
            yield {
                'name': basic_info['name'],
                'profile_url': response.url,
                'height': basic_info['height'],
                'span': basic_info['span'],
                'nationality': basic_info['nationality'],
                'repetitions': repetitions,
            }
    def parse_climber_full(self, response):
        # Get info from meta
        name = response.meta['name']
        span = response.meta['span']
        height = response.meta['height']
        nationality = response.meta['nationality']
        repetitions = extract_bleau_repetitions(response) # modified_date param only for scraping existing users (defaults to None)
        n_ascents_scraped = len(repetitions)
        self.logger.info(f"✅ PLAYWRIGHT: Scraped ascents for {name}: {n_ascents_scraped} / {response.meta['n_ascents']}")
        yield {
            'name': name,
            'profile_url': response.url,
            'height': height,
            'span': span,
            'nationality': nationality,
            'repetitions': repetitions,
        }
    def errback_climber_full(self, failure):
        self.logger.error(f"Failed to fetch full ascents: {failure.value}")
        self.logger.error(f"Request URL: {failure.request.url}")
