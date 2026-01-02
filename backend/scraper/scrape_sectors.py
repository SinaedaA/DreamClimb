# scrape_sectors.py

import requests
import time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from utils import fetch_page, save_json

## CONSTANT
CORE_URL = "https://bleau.info"

## HANDLE DIRECTORIES
SCRIPT_DIR = Path(__file__).parent # bleau-recommender/backend/scraper
BACKEND_ROOT = SCRIPT_DIR.parent  # bleau-recommender/backend/

def main():
    """Main function to scrape sectors and save data"""
    ## Ensure output directory exists
    boulders_dir = BACKEND_ROOT / 'data' / 'raw' / 'boulders'
    circuits_dir = BACKEND_ROOT / 'data' / 'raw' / 'circuits'

    boulders_dir.mkdir(parents=True, exist_ok=True)
    circuits_dir.mkdir(parents=True, exist_ok=True)

    ## Get the sector_slug dictionary {name: slug}
    slug_dict = scrape_sector_slugs()
    print(f"Found {len(slug_dict)} sectors to scrape")

    ## Scrape each sector independently
    for name, slug in slug_dict.items():
        print(f"Scraping {name} - {slug}...")
        boulder_path = boulders_dir / f'{slug}.json'
        circuit_path = circuits_dir / f'{slug}.json'
    
        # Check what needs scraping
        needs_boulders = not (boulder_path.exists() and boulder_path.stat().st_size > 0)
        needs_circuits = not (circuit_path.exists() and circuit_path.stat().st_size > 0)
    
        # Skip if both are already done
        if not needs_boulders and not needs_circuits:
            print(f"✓ Both files exist for {slug}, skipping...")
            continue
        
        try:
            data = scrape_sector(name, slug)

            if needs_boulders:
                save_json(data['boulders'], boulder_path)
                print(f"  ✓ Saved boulders")
            
            if needs_circuits:
                if is_valid_circuit_data(data['circuits']):
                    save_json(data['circuits'], circuit_path)
                    print(f"  ✓ Saved circuits")
                elif not data['circuits']['circuits']:
                    print(f"  ✓ No circuits found for {slug}, skipping save.")
                else:
                    print(f"  ✗ Invalid circuit data for {slug}, skipping save.")

            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Failed to scrape {name}: {e}")
            continue
    
    print("Done!")

def parse_problems(soup):
    """Extract problems from the page"""
    problems = []
    for div in soup.select('div.vsr'):
        # Extract name and URL
        link = div.find('a')
        name = link.text.strip() if link else None
        url = urljoin(CORE_URL, link['href']) if link else None
        
        # Extract grade (first text node after the link, before any span)
        grade = None
        for text in div.stripped_strings:
            if text not in [name] and not text.startswith('('):
                # Check if it looks like a grade (starts with number)
                if text[0].isdigit():
                    grade = text
                    break
        # Extract rating of the boulder
        rating = div.find('span', class_='vr')
        # count number of stars if rating exists
        if rating:
            full_stars = len(rating.find_all(class_='glyphicon glyphicon-star'))
            half_stars = len(rating.find_all(class_='glyphicon glyphicon-star half'))
            rating = full_stars + 0.5 * half_stars
        else:
            rating = None

        # Extract first ascensionist
        fa_tag = div.find('em')
        first_ascensionist = fa_tag.text.strip() if fa_tag else None
        
        # Extract styles
        style_tag = div.find('span', class_='btype')
        styles = style_tag.text.strip().split(', ') if style_tag else []
        
        # Check for alternative grade (span.ag)
        alt_grade_tag = div.find('span', class_='ag')
        alt_grade = alt_grade_tag.text.strip() if alt_grade_tag else None
        
        problems.append({
            'name': name,
            'url': url,
            'grade': grade,
            'alt_grade': alt_grade,  # Some problems have this
            'first_ascensionist': first_ascensionist,
            'styles': styles,
            'rating': rating
        })
    return problems

def parse_circuits(soup):
    """Extract circuits from the page"""
    circuit_links = [
        urljoin(CORE_URL, a['href'])
        for a in soup.select('ul.list-inline a')
            if 'circuit' in a['href'] and a['href'].endswith('.html')
    ]
    circuits = []
    if len(circuit_links) == 0:
        return None
    for crct_url in circuit_links:
        print(f"  - Fetching circuit: {crct_url}")
        crct_soup = fetch_page(crct_url)
        ## Name of circuit
        name_tag = crct_soup.find('h3')
        name = name_tag.find(string=True, recursive=False).strip() if name_tag else 'Unknown Circuit'
        
        ## All boulders inside circuit (1 boulder = class_ = 'row lvar')
        problems = []
        for problem in crct_soup.select('div.row.lvar'):
            prob_id = problem.find('div', class_='lvnr col-xs-1').text.strip()
            prob_link = problem.find('a')
            prob_url = urljoin(CORE_URL, prob_link['href']) if prob_link else None
            problems.append({
                'id': prob_id,
                'url': prob_url
            })
        ## Only append this circuit to circuits if it has problems
        if len(problems) > 0:
            ## Append problems to circuit data
            circuits.append({
                'name': name,
                'url': crct_url,
                'problems': problems
            })
        else:
            print(f"    ✗ No problems found in circuit {name}, skipping.")
    return circuits

def scrape_sector(sector_name, sector_slug):
    """Scrape both boulders and circuits from a sector"""
    url = urljoin(CORE_URL, sector_slug)
    soup = fetch_page(url)
    
    problems = parse_problems(soup)
    circuits = parse_circuits(soup)
    
    return {
        'boulders': {'sector': sector_name, 'problems': problems},
        'circuits': {'sector': sector_name, 'circuits': circuits}
    }

def scrape_sector_slugs():
    area_url = urljoin(CORE_URL, "areas_by_region")
    response = requests.get(area_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    names_to_slugs = {
        a.text.strip(): a['href'].split('/')[-1]
        for a in soup.select('div.row-same-height.area_by_regions a') # div with BOTH classes row-same-height AND area_by_regions, and take all <a> tags inside
    }
    return names_to_slugs

def is_valid_circuit_data(data):
    """Check if circuit data has required fields"""
    if not data.get('sector'):
        return False
    if not data.get('circuits'):
        return False
    # Check each circuit has required fields
    for circuit in data['circuits']:
        if not circuit.get('name') or not circuit.get('url'):
            return False
        if not circuit.get('problems'):
            return False
        # Check each problem is complete
        for problem in circuit['problems']:
            if problem.get('id') is None or not problem.get('url'):
                return False
    return True

if __name__ == "__main__":
    main()