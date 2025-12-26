import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

BASE_URL = "https://www.careers360.com"
MAX_THREADS = 10

def fetch_soup(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"[fetch_soup] Error fetching {url}: {e}")
        return None

def fetch_location_from_detail_page(url):
    try:
        time.sleep(random.uniform(0.5, 1.0))
        soup = fetch_soup(url)
        if not soup:
            return url, None

        banner_div = soup.select_one('div.bannerTags')
        if banner_div:
            a_tags = banner_div.find_all('a')
            if len(a_tags) >= 2:
                city = a_tags[0].get_text(strip=True)
                state = a_tags[1].get_text(strip=True)
                return url, f"{city}, {state}"

        return url, None
    except Exception as e:
        print(f"[Detail Page] Failed to fetch location from {url}: {e}")
        return url, None

def fetch_established_year(url):
    soup = fetch_soup(url)
    if not soup:
        return None
    highlight_section = soup.select_one('div#highlight table.table')
    if highlight_section:
        rows = highlight_section.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 2 and cols[0].get_text(strip=True).lower() == 'established':
                return cols[1].get_text(strip=True)
    return None

def fetch_courses(url):
    courses_url = url.rstrip('/') + '/courses'
    soup = fetch_soup(courses_url)
    if not soup:
        return []

    course_rows = []
    course_divs = soup.select('div.detail')
    for div in course_divs:
        course_name_tag = div.find('h4')
        if course_name_tag and course_name_tag.a:
            course_name = course_name_tag.a.get_text(strip=True)
            fees = duration = seats = None

            detail_div = div.select_one('div.course_detail')
            if detail_div:
                for fee_block in detail_div.find_all('div'):
                    label = fee_block.get_text(strip=True).lower()
                    if "total fees" in label:
                        fee_span = fee_block.find('span')
                        if fee_span:
                            fees = fee_span.get_text(strip=True)
                    elif "duration" in label:
                        duration_span = fee_block.find('span')
                        if duration_span:
                            duration = duration_span.get_text(strip=True)
                    elif "seats" in label:
                        seats_span = fee_block.find('span')
                        if seats_span:
                            seats = seats_span.get_text(strip=True)

            course_rows.append((course_name, duration, fees, seats))
    return course_rows

def extract_card_details(card):
    data = {}
    full = card.get_text(separator='|||', strip=True)
    lines = [l.strip() for l in full.split('|||') if l.strip()]
    h3 = card.find('h3')
    if h3:
        a_tag = h3.find('a', href=True)
        if a_tag:
            title = a_tag.get_text(strip=True)
            detail_url = a_tag['href']
            if not detail_url.startswith("http"):
                detail_url = BASE_URL + detail_url
            data['title'] = title
            data['detail_url'] = detail_url
    for line in lines:
        m = re.search(r'(\d+(\.\d+)?)/5', line)
        if m:
            data['rating'] = m.group(0)
            break
    ownership_tag = card.select_one('.ownership, .college-type, .institute-type, .type')
    if ownership_tag:
        data['ownership'] = ownership_tag.get_text(strip=True)
    for line in lines:
        if ',' in line and len(line.split(',')) == 2:
            if not any(lbl in line for lbl in ['Rating', 'Ownership', 'NIRF', 'Rank', 'Careers360']):
                data['location'] = line
                break
    return data

def is_valid_location(loc):
    if not loc or ',' not in loc:
        return False
    if any(bad in loc.lower() for bad in ['meritcum-means', 'scholarship', 'phd', 'research']):
        return False
    parts = [part.strip() for part in loc.split(',')]
    return len(parts) == 2

def scrape_domain_listing(list_url, card_selector, domain_label):
    print(f"\nScraping {domain_label} from {list_url}")
    soup = fetch_soup(list_url)
    if not soup:
        return []

    cards = soup.select(card_selector)
    print(f"Found {len(cards)} {domain_label} cards")
    results = []
    detail_urls = []

    for card in cards:
        det = extract_card_details(card)
        det['domain'] = domain_label
        if 'detail_url' in det:
            detail_urls.append(det['detail_url'])
        results.append(det)

    url_to_location, url_to_established, url_to_courses = {}, {}, {}

    def fetch_details(url):
        loc_url, location = fetch_location_from_detail_page(url)
        established = fetch_established_year(url)
        courses = fetch_courses(url)
        return loc_url, location, established, courses

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(fetch_details, url): url for url in detail_urls}
        for future in as_completed(futures):
            try:
                url, location, established, courses = future.result()
                if location:
                    url_to_location[url] = location
                if established:
                    url_to_established[url] = established
                if courses:
                    url_to_courses[url] = courses
            except Exception as e:
                print(f"Error fetching details: {e}")

    final_rows = []
    for det in results:
        url = det.get('detail_url')
        location = url_to_location.get(url)
        if location and is_valid_location(location):
            det['location'] = location
            det['city'], det['state'] = [p.strip() for p in location.split(',')]
        else:
            det['location'] = det['city'] = det['state'] = None

        det['established'] = url_to_established.get(url)

        courses = url_to_courses.get(url)
        if not courses:
            det['course_name'] = det['course_duration'] = det['course_fee'] = det['course_seats'] = None
            det.pop('detail_url', None)
            final_rows.append(det)
        else:
            for course_name, duration, course_fee, seats in courses:
                new_row = det.copy()
                new_row['course_name'] = course_name
                new_row['course_duration'] = duration
                new_row['course_fee'] = course_fee
                new_row['course_seats'] = seats
                new_row.pop('detail_url', None)
                final_rows.append(new_row)

    return final_rows

def scrape_all_domains():
    all_data = []
    domains = [
        ("Engineering", "https://engineering.careers360.com/colleges/ranking", "div.card_block"),
        ("Medical", "https://medicine.careers360.com/colleges/ranking", "div.card_block"),
        ("University", "https://university.careers360.com/colleges/ranking", "div.card_block"),
        ("MBA", "https://bschool.careers360.com/colleges/ranking", "div.card_block"),
        ("Law", "https://law.careers360.com/colleges/ranking", "div.card_block"),
    ]
    for domain_label, url, selector in domains:
        data = scrape_domain_listing(url, selector, domain_label)
        all_data.extend(data)
    return pd.DataFrame(all_data)

def main():
    df = scrape_all_domains()
    if df.empty:
        print("⚠️ No data scraped.")
        return

    def clean_duration_in_years(duration):
        if not duration or not isinstance(duration, str):
            return None
        duration = duration.lower().strip()
        years = re.search(r'(\d+(\.\d+)?)\s*year', duration)
        months = re.search(r'(\d+(\.\d+)?)\s*month', duration)
        total_years = 0.0
        if years:
            total_years += float(years.group(1))
        if months:
            total_years += float(months.group(1)) / 12
        return round(total_years, 2) if total_years > 0 else None

    def clean_fee_in_inr(fee):
        if not fee or not isinstance(fee, str):
            return None
        fee = fee.lower().replace(',', '').replace('₹', '').strip()
        if re.search(r'(\d+(\.\d+)?)(\s*)?(crore|cr)', fee):
            return int(float(re.search(r'(\d+(\.\d+)?)', fee).group()) * 1e7)
        if re.search(r'(\d+(\.\d+)?)(\s*)?(lakh|lac|l)', fee):
            return int(float(re.search(r'(\d+(\.\d+)?)', fee).group()) * 1e5)
        if re.search(r'(\d+(\.\d+)?)(\s*)?k', fee):
            return int(float(re.search(r'(\d+(\.\d+)?)', fee).group()) * 1e3)
        if re.fullmatch(r'\d+(\.\d+)?', fee):
            return int(float(fee))
        return None

    df['course_duration_years'] = df['course_duration'].apply(clean_duration_in_years)
    df['course_fee_inr'] = df['course_fee'].apply(clean_fee_in_inr)

    if 'rating' in df.columns:
        df['rating_raw'] = df['rating']
        df['rating'] = pd.to_numeric(df['rating'].str.extract(r'(\d+(\.\d+)?)')[0], errors='coerce')
    else:
        df['rating_raw'] = "NaN"
        df['rating'] = 0

    if 'course_seats' in df.columns:
        df['course_seats'] = pd.to_numeric(df['course_seats'].str.replace(r'\D+', '', regex=True), errors='coerce')
    df.to_csv('careers360_colleges.csv', index=False, encoding='utf-8-sig')
    for col in df.columns:
        if df[col].dtype.kind in 'biufc':
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna('NaN')

    # Reorder columns with location after course_fee_inr
    column_order = [
        'title', 'rating', 'domain', 'city', 'state', 'established',
        'course_name', 'course_duration_years', 'course_fee_inr', 'location',
        'course_duration', 'course_fee', 'course_seats', 'rating_raw'
    ]
    df = df[[col for col in column_order if col in df.columns]]

    print(df.head(10))

    df.to_csv('cleaned_careers360_colleges.csv', index=False, encoding='utf-8-sig')
    print("✅ Data exported to careers360_colleges.csv")

if __name__ == '__main__':
    main()
