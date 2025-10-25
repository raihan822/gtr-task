# scraper.py
# START TIME: -----------
import time
start_time = time.time()
# -----------------------
#//////////////////////////////////////////////////////////////////////////////////
# scraper.py
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from urllib.parse import urljoin
from _2_db import get_session, Phone  # Your separate db file

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_SEARCH = "https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName=Samsung"

# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#     "Accept-Language": "en-US,en;q=0.9"
# }
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
    "Referer": "https://www.google.com/"
}

proxy = "102.209.18.204:8080"
proxies = {
    "http":  f"http://{proxy}",
    "https": f"http://{proxy}",
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_release_date(date_str):
    """
    Convert GSMArena date format to Python date object

    Examples:
        "2025, January 22" → datetime.date(2025, 1, 22)
        "2024, December" → datetime.date(2024, 12, 1)
        "Cancelled" → None
        "Not announced yet" → None

    Args:
        date_str: Release date string from GSMArena

    Returns:
        datetime.date object or None
    """
    if not date_str:
        return None

    # Clean the string
    date_str = date_str.strip()

    # Check for invalid dates
    invalid_keywords = ['cancelled', 'not announced', 'expected', 'rumored',
                        'discontinued', 'coming soon', 'TBA', 'Q1', 'Q2', 'Q3', 'Q4']
    if any(keyword in date_str.lower() for keyword in invalid_keywords):
        return None

    # Try to parse formats like "2025, January 22" or "2024, December"
    try:
        # Pattern: "YYYY, Month DD" or "YYYY, Month"
        match = re.search(r'(\d{4}),?\s+(\w+)(?:\s+(\d{1,2}))?', date_str)
        if match:
            year = int(match.group(1))
            month_str = match.group(2)
            day = int(match.group(3)) if match.group(3) else 1

            # Convert month name to number
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12,
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                'jun': 6, 'jul': 7, 'aug': 8,
                'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            month = month_map.get(month_str.lower())

            if month:
                return datetime(year, month, day).date()
    except (ValueError, AttributeError):
        pass

    return None


def parse_specs_from_model_page(html):
    """
    Parse phone specifications from GSMArena phone details page

    Args:
        html: HTML content of phone details page

    Returns:
        dict with parsed specs
    """
    soup = BeautifulSoup(html, "html.parser")
    data = {
        'display': None,
        'battery': None,
        'camera': None,
        'ram': None,
        'storage': None,
        'release_date': None,
        'price_usd': None
    }

    # ==================== PRICE EXTRACTION ====================
    price_td = soup.find("td", class_="nfo", attrs={"data-spec": "price"})

    if price_td:
        price_text = price_td.get_text(strip=True)
        # Extract USD price (format: $ X,XXX.XX or $ XXX.XX)
        usd_match = re.search(r'\$\s*([0-9,]+\.?\d*)', price_text)
        if usd_match:
            price_str = usd_match.group(1).replace(',', '')
            try:
                data['price_usd'] = float(price_str)
            except ValueError:
                pass

    # Alternative: Check pricing link (fallback)
    if not data['price_usd']:
        price_link = soup.find("a", href=re.compile(r"-price-\d+\.php"))
        if price_link:
            price_text = price_link.get_text(strip=True)
            usd_match = re.search(r'\$\s*([0-9,]+\.?\d*)', price_text)
            if usd_match:
                price_str = usd_match.group(1).replace(',', '')
                try:
                    data['price_usd'] = float(price_str)
                except ValueError:
                    pass

    # ==================== OTHER SPECS ====================
    specs_div = soup.find("div", id="specs-list")
    if not specs_div:
        return data

    for table in specs_div.find_all("table", cellspacing="0"):
        for row in table.find_all("tr"):
            ttl = row.find("td", class_="ttl")
            nfo = row.find("td", class_="nfo")

            if not ttl or not nfo:
                continue

            key = ttl.get_text(strip=True).lower()
            val = nfo.get_text(" ", strip=True)

            # Display size
            if "size" in key and not data['display']:
                data['display'] = val

            # Battery (look for mAh)
            elif not data['battery']:
                m = re.search(r"(\d{3,5})\s?mAh", val.replace(",", ""))
                if m:
                    data['battery'] = int(m.group(1))

            # Camera (main/rear camera)
            elif ("quad" in key or "triple" in key or "dual" in key or
                  "single" in key or "main camera" in key.lower()) and not data['camera']:
                data['camera'] = val

            # Internal storage (contains both RAM and storage)
            elif "internal" in key:
                if not data['storage']:
                    data['storage'] = val
                if not data['ram']:
                    # Extract RAM (e.g., "12GB RAM")
                    ram_match = re.search(r"(\d+GB)\s+RAM", val)
                    if ram_match:
                        data['ram'] = ram_match.group(1)

            # Release date (parse to date object)
            elif ("announced" in key or "status" in key) and not data['release_date']:
                data['release_date'] = parse_release_date(val)

    return data


# ============================================================================
# MAIN SCRAPING FUNCTION
# ============================================================================

def scrape_models(limit=30, delay=1.0):
    """
    Scrape Samsung phone models from GSMArena search results

    Args:
        limit: Maximum number of phones to scrape
        delay: Delay in seconds between requests (be respectful)
    """
    print(f"{'=' * 60}")
    print(f"Starting GSMArena Scraper for Samsung Phones")
    print(f"{'=' * 60}\n")

    # Fetch search results page
    try:
        print(f">> Fetching search results...")
        resp = requests.get(BASE_SEARCH, headers=HEADERS, proxies=proxies, timeout=15)
        resp.raise_for_status()
        print(f"✓ Search page loaded successfully\n")
    except Exception as e:
        print(f"Error fetching search page: {e}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Extract phone links
    links = []
    makers_div = soup.find("div", class_="makers")

    if not makers_div:
        print("Could not find 'makers' div. Page structure may have changed.")
        return

    for li in makers_div.find_all("li"):
        a_tag = li.find("a")
        if a_tag:
            href = a_tag.get('href')
            # Get phone name from <strong> or <span> tag
            name_tag = a_tag.find("strong") or a_tag.find("span")
            if name_tag:
                name = name_tag.get_text(strip=True)
            else:
                # Fallback: get all text
                name = a_tag.get_text(strip=True)
                name = re.sub(r'\s+', ' ', name)

            if href and name:
                full_url = urljoin("https://www.gsmarena.com/", href)
                links.append((name, full_url))

            if len(links) >= limit:
                break

    if not links:
        print("No phone links found. Check page structure.")
        return

    print(f"✓ Found {len(links)} models to scrape\n")
    print(f"{'=' * 60}\n")

    # Scrape each phone's details
    saved = 0
    session = get_session()

    for idx, (name, link) in enumerate(links, 1):
        try:
            print(f"[{idx}/{len(links)}] >> {name}...", end=" ")
            r = requests.get(link, headers=HEADERS, proxies=proxies, timeout=15)
            r.raise_for_status()

            parsed = parse_specs_from_model_page(r.text)

            # Create Phone object
            phone = Phone(
                model_name=name,
                brand='Samsung',
                release_date=parsed['release_date'],  # Now a date object or None
                display=parsed['display'],
                battery=parsed['battery'],
                camera=parsed['camera'],
                ram=parsed['ram'],
                storage=parsed['storage'],
                price_usd=parsed['price_usd'],
                source_url=link
            )

            session.add(phone)
            session.commit()
            saved += 1

            # Show extracted info
            price_str = f"${parsed['price_usd']:.2f}" if parsed['price_usd'] else "no price"
            date_str = parsed['release_date'].strftime("%Y-%m-%d") if parsed['release_date'] else "no date"
            print(f"✓ ({price_str} | {date_str})")

        except Exception as e:
            print(f"✗ Error: {e}")
            session.rollback()

        # Be respectful to the server
        time.sleep(delay)

    session.close()

    print(f"\n{'=' * 60}")
    print(f"✓ Scraping Complete!")
    print(f"{'=' * 60}")
    print(f"Successfully saved: {saved}/{len(links)} models")
    print(f"{'=' * 60}\n")


# ============================================================================
# TESTER
# ============================================================================
def test_search_parsing():
    """Test if we can parse search results correctly"""
    resp = requests.get(BASE_SEARCH, headers=HEADERS, proxies=proxies, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')

    makers_div = soup.find("div", class_="makers")
    if not makers_div:
        print("❌ Could not find makers div")
        return

    links = []
    for li in makers_div.find_all("li")[:5]:  # Test first 5
        a_tag = li.find("a")
        if a_tag:
            name = a_tag.find("strong")
            if name:
                print(f"✓ Found: {name.get_text(strip=True)}")
                links.append((name.get_text(strip=True), a_tag.get('href')))

    print(f"\nTotal found: {len(links)}")
    return links

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == '__main__':
    # test_search_parsing()  # Uncomment to test
    scrape_models(limit=30, delay=2)


#//////////////////////////////////////////////////////////////////////////////////
## END TIME & TIME CALCULATION: ------------------------------------------------------------
end_time = time.time()
elapsed_time = end_time - start_time
minutes = int(elapsed_time // 60)
seconds = elapsed_time % 60
print("\nTotal Elapsed Time: {} minutes and {:.2f} seconds".format(minutes, seconds))
## ------------------------------------------------------------