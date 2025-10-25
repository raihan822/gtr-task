# scraper.py
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin
from db import get_session, Phone

BASE_SEARCH = "https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName=Samsung"
HEADERS = {"User-Agent": "Samsung-Phone-Advisor/1.0 (+https://example.com)"}

def parse_specs_from_model_page(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {
        'display': None,
        'battery': None,
        'camera': None,
        'ram': None,
        'storage': None,
        'release_date': None
    }
    # NOTE: GSMArena uses structured spec lists. The exact selectors may change.
    spec_tables = soup.select('.specs-table')
    for table in spec_tables:
        rows = table.select('tr')
        for r in rows:
            th = r.find('th')
            td = r.find('td')
            if not th or not td:
                continue
            key = th.get_text(strip=True).lower()
            val = td.get_text(' ', strip=True)
            if 'display' in key:
                data['display'] = val
            if 'battery' in key:
                # extract mAh integer
                m = re.search(r"(\d{3,5})\s?mAh", val)
                if m:
                    data['battery'] = int(m.group(1))
                else:
                    data['battery'] = None
            if 'camera' in key:
                data['camera'] = val
            if 'ram' in key:
                data['ram'] = val
            if 'internal' in key or 'storage' in key:
                data['storage'] = val
            if 'announcement' in key or 'released' in key:
                data['release_date'] = val
    return data


def scrape_models(limit=30, delay=1.0):
    # Very simple approach: fetch search results and follow links
    resp = requests.get(BASE_SEARCH, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = []
    for a in soup.select('div.makers ul li a'):
        href = a.get('href')
        name = a.get_text(strip=True)
        if href:
            links.append((name, urljoin('https://www.gsmarena.com/', href)))
        if len(links) >= limit:
            break

    saved = 0
    session = get_session()
    for name, link in links:
        try:
            r = requests.get(link, headers=HEADERS, timeout=15)
            r.raise_for_status()
            parsed = parse_specs_from_model_page(r.text)
            phone = Phone(
                model_name=name,
                brand='Samsung',
                release_date=None, # optional: parse into date
                display=parsed['display'],
                battery=parsed['battery'],
                camera=parsed['camera'],
                ram=parsed['ram'],
                storage=parsed['storage'],
                price_usd=None,
                source_url=link,
            )
            session.add(phone)
            session.commit()
            saved += 1
            print(f"Saved: {name}")
        except Exception as e:
            print("Error fetching", link, e)
        time.sleep(delay)
    session.close()
    print(f"Done. Saved {saved} models.")

if __name__ == '__main__':
    scrape_models(25)