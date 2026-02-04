import sys
sys.path.insert(0, '/opt/airflow')

import scrapy
import json
from app.database import SessionLocal
from app.models import UserResponse
from scrapy_playwright.page import PageMethod
import datetime
from utils import parse_betty_climber_logic, extract_bleau_climber_basics, extract_bleau_repetitions

## Get existing user profile links from DB
def get_existing_users():
    db = SessionLocal()
    users = db.query(UserResponse).all() #filter(UserResponse.profile_url.like('https://bleau%')).all()
    user_links = [user.profile_url for user in users]
    # Get most recent 'modified_at' in the entire table user_response (= date of most recent scrape)
    modified_date = db.query(UserResponse).order_by(UserResponse.modified_at.desc()).first().modified_at
    print(f"🗂️ Found {len(user_links)} existing users to scrape. Most recent scrape was on {modified_date}.")
    
    db.close()
    user_links_unique = set(user_links)
    return list(user_links_unique), modified_date

class ExistingClimberSpider(scrapy.Spider):
    name = 'existing_climbers'
    start_urls = []  # to be populated with existing user profile links
    modified_date = None

    seen_climbers = set()
    
    custom_settings = {
        # 'DOWNLOAD_DELAY': 1,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
    }

    def __init__(self, betty2bleau = '../data/raw/ascents/betty_2_bleau_mapping.json', days_back = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_climbers = set()
        self.days_back = int(days_back)
        
        # Load the mapping
        with open(betty2bleau, 'r') as f:
            self.betty_2_bleau = json.load(f)
        self.logger.info(f"📂 Loaded {len(self.betty_2_bleau)} boulder mappings!")

        # Populate start_urls with existing user profile links from DB
        self.start_urls, self.modified_date = get_existing_users()
        # for testing purposes, you can set days_back to check only ascents x days before the last modified_date
        self.modified_date = self.modified_date - datetime.timedelta(days=self.days_back)
        self.logger.info(f"🚀 Starting to scrape new ascents from {len(self.start_urls)} existing climbers from DB. Keep only ascents later than {self.modified_date}.")

    def parse(self, response):
        # Determine if the URL is from bettybeta or bleau.info
        if "bettybeta.com" in response.url:
            #self.logger.info(f"✅✅✅ Detected BettyBeta profile page: {response.url}")
            # Follow to the climber profile page
            yield response.follow(response.url, callback=self.parse_betty_climber)
        elif "bleau.info" in response.url:
            #self.logger.info(f"✅✅✅ Detected Bleau.info profile page: {response.url}")
            # Directly parse the climber profile page
            yield response.follow(response.url, callback=self.parse_bleau_climber)
    
    def parse_betty_climber(self, response):
        result = parse_betty_climber_logic(response, self.betty_2_bleau, self.logger, self.modified_date)
        
        # Only yield if there are new ascents
        if len(result['repetitions']) > 0:
            self.logger.info(f"Newest ascents for {result['name']} fetched: {len(result['repetitions'])} ascents.")
            yield result
        else:
            self.logger.info(f"No new ascents for {result['name']} since {self.modified_date}")
    
    def parse_bleau_climber(self, response):
        basic_info = extract_bleau_climber_basics(response) # returns: name, n_ascents, profile_url, height, span, nationality
        repetitions = extract_bleau_repetitions(response)
        
        # get most recent and oldest date from repeitions
        dates = [datetime.datetime.strptime(rep['date'], "%d-%m-%Y").date()  for rep in repetitions]
        oldest_date = min(dates) if dates else None
        #self.logger.info(f"🗓️ Oldest date displayed on this page: {oldest_date}")

        # filter repetitions to only include those after modified_date
        repetitions = [rep for rep in repetitions if datetime.datetime.strptime(rep['date'], "%d-%m-%Y").date()  > self.modified_date.date()]
        
        # If the oldest date is AFTER the modified_date, we need to fetch more ascents via playwright
        if len(repetitions) > 0:
            if oldest_date > self.modified_date.date():
                self.logger.warning(f"⚠️ Displayed ascents might not cover additional ascents since {self.modified_date} - {response.url}.")
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
                        'n_ascents': basic_info['n_ascents'],
                        'source': 'bleau_info'
                    }, 
                    headers = {
                    'Referer': response.url,
                    'X-Requested-With': 'XMLHttpRequest'
                    },
                    errback=self.errback_climber_full,
                    dont_filter=True
                )
            else:
                self.logger.info(f"Newest ascents for {basic_info['name']} fetched: {len(repetitions)} ascents fetched.")
                yield {
                    'name': basic_info['name'],
                    'profile_url': response.url,
                    'height': basic_info['height'],
                    'span': basic_info['span'],
                    'nationality': basic_info['nationality'],
                    'repetitions': repetitions,
                    'source': 'bleau_info'
                }

    def parse_bleau_climber_full(self, response):
        # Get info from meta
        name = response.meta['name']
        span = response.meta['span']
        height = response.meta['height']
        nationality = response.meta['nationality']
        repetitions = extract_bleau_repetitions(response, self.modified_date)
        n_ascents_scraped = len(repetitions)
        self.logger.info(f"✅ PLAYWRIGHT: Scraped ascents for {name}: {n_ascents_scraped} / {response.meta['n_ascents']}")
        yield {
            'name': name,
            'profile_url': response.url,
            'height': height,
            'span': span,
            'nationality': nationality,
            'repetitions': repetitions,
            'source': 'bleau_info'
        }
    def errback_climber_full(self, failure):
        self.logger.error(f"Failed to fetch full ascents: {failure.value}")
        self.logger.error(f"Request URL: {failure.request.url}")
