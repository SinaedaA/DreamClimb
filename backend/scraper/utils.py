# utils.py
import requests
from bs4 import BeautifulSoup
import json
import datetime
import re

def fetch_page(url):
    """Fetch HTML from a URL and return BeautifulSoup object"""
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.content, 'html.parser')

def save_json(data, filepath):
    """Save data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def parse_betty_climber_logic(response, betty_2_bleau_mapping, logger, modified_date = None):
    """Extract climber data from BettyBeta profile page"""
    
    # Extract user info
    name = response.css('h1::text').get().strip()
    climber_url = response.url
    logger.info(f"Scraping climber: {name} from {climber_url}")
    
    height_span = response.css('table tr td b:contains("cm")::text').getall()
    height = height_span[0] if len(height_span) > 0 else None
    span = height_span[1] if len(height_span) > 1 else None

    # convert both to integers
    if height is not None:
        height = int(height.replace("cm", "").strip())
    if span is not None:
        span = int(span.replace("cm", "").strip())

    if span is not None and abs(span) < 100:
        span = height + span

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
            date_climbed = datetime.datetime.strptime(date, "%m/%d/%Y").date()
            if modified_date and date_climbed <= modified_date.date():
                continue
            bleau_link = betty_2_bleau_mapping.get(betty_url, None)
            repetitions.append({
                'ascent': ascent,
                'grade': grade,
                'date': date_climbed.strftime("%d-%m-%Y"),
                'bleau_link': bleau_link
            })
        except Exception as e:
            logger.error(f"❌ Error parsing repetition for {name}: {e}")
    
    return {
        'name': name,
        'profile_url': climber_url,
        'n_ascents': len(repetitions),
        'height': height,
        'span': span,
        'source': 'betty_beta',
        'repetitions': repetitions
    }

def extract_bleau_climber_basics(response):
    """Extract basic info from bleau.info profile"""
    
    name = response.css('h3::text').get().strip()
    n_ascents_text = response.css('h4::text').get()
    n_ascents_text = re.search(r'\((\d+)\)', n_ascents_text).group(1) if n_ascents_text else '0'
    n_ascents = int(n_ascents_text) if n_ascents_text else 0
    
    full_text = response.css('p').get()
    height = re.search(r'<strong>Height:</strong>\s*([0-9.]+)m', full_text)
    span = re.search(r'<strong>Span:</strong>\s*([0-9.]+)m', full_text)
    nationality = re.search(r'<strong>Nationality:</strong>\s*(\w+)', full_text)
    
    return {
        'name': name,
        'profile_url': response.url,
        'n_ascents': n_ascents,
        'height': float(height.group(1).replace(',', '.'))*100 if height else None,
        'span': float(span.group(1).replace(',', '.'))*100 if span else None,
        'nationality': nationality.group(1) if nationality else None,
        'source': 'bleau_info'
    }

def extract_bleau_repetitions(response, modified_date = None):
    """Extract ascent list"""
    repetitions = []
    for rep in response.css('#tab_by_date > div.repetition'):
        date_raw = rep.xpath('./text()[1]').get()
        date = re.sub(r'[^0-9-]', '', date_raw)
        date_climbed = datetime.datetime.strptime(date, "%d-%m-%Y").date()
        if modified_date and date_climbed <= modified_date.date():
            continue
        ascent = rep.css('a::text').get().strip()
        grade = rep.xpath('./text()[normalize-space()][last()]').get().strip()
        repetitions.append({'date': date_climbed.strftime("%d-%m-%Y"), 'ascent': ascent, 'grade': grade})
    return repetitions