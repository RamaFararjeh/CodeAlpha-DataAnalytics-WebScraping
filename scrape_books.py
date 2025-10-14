import time
import csv
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE = "http://books.toscrape.com/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CodeAlpha/1.0)"}

def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def extract_rating(tag):
    # ratings are in classes like "star-rating Three"
    classes = tag.get("class", [])
    # Map textual rating to number
    map_ = {"One":1, "Two":2, "Three":3, "Four":4, "Five":5}
    for c in classes:
        if c in map_:
            return map_[c]
    return None

def parse_book(card, category_name=None):
    title = card.h3.a.get("title", "").strip()
    rel = card.h3.a.get("href")
    product_url = urljoin(BASE, rel)
    price_text = card.select_one(".price_color").text.strip()
    # price like '£51.77' -> 51.77
    price = float(re.sub(r"[^\d.]", "", price_text))
    rating = extract_rating(card.select_one(".star-rating"))
    availability_text = card.select_one(".availability").get_text(strip=True)
    available = "In stock" in availability_text
    return {
        "title": title,
        "price_gbp": price,
        "rating": rating,
        "available": available,
        "category": category_name,
        "product_page": product_url
    }

def scrape_category(cat_url, cat_name):
    rows = []
    page_url = cat_url
    while True:
        soup = get_soup(page_url)
        for card in soup.select("article.product_pod"):
            rows.append(parse_book(card, category_name=cat_name))
        # next page?
        next_li = soup.select_one("li.next > a")
        if next_li:
            page_url = urljoin(page_url, next_li.get("href"))
            time.sleep(1)  # politeness
        else:
            break
    return rows

def get_all_categories():
    soup = get_soup(BASE)
    cats = []
    for a in soup.select("div.side_categories ul li ul li a"):
        name = a.get_text(strip=True)
        link = urljoin(BASE, a["href"])
        cats.append((name, link))
    return cats

def main():
    all_rows = []
    cats = get_all_categories()
    for i, (name, link) in enumerate(cats, start=1):
        print(f"[{i}/{len(cats)}] Scraping category: {name}")
        all_rows.extend(scrape_category(link, name))
        time.sleep(1)  # politeness
    # save CSV
    fieldnames = ["title","price_gbp","rating","available","category","product_page"]
    with open("books.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)
    print(f"Done. Saved {len(all_rows)} rows to books.csv")

if __name__ == "__main__":
    main()
