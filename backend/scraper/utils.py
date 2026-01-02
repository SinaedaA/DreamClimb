# utils.py
import requests
from bs4 import BeautifulSoup
import json

def fetch_page(url):
    """Fetch HTML from a URL and return BeautifulSoup object"""
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.content, 'html.parser')

def save_json(data, filepath):
    """Save data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)