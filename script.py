import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# Base URL and Headers
BASE_URL = "https://cheers.com.np"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_liquor_categories():
    """Extract only liquor category URLs."""
    try:
        print("Fetching main page...")
        response = requests.get(f"{BASE_URL}/liquor", headers=HEADERS)
        response.raise_for_status()
        
        print(f"Liquor page status code: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the category container
        categories = []
        category_links = soup.select("a[href*='/liquor/category']")
        
        print(f"Found {len(category_links)} liquor category links")
        
        for link in category_links:
            href = link.get("href")
            text = link.text.strip()
            
            if href and text and not any(x in text.lower() for x in ['home', 'currency', 'npr']):
                print(f"Found liquor category: {text}")
                full_url = href if href.startswith('http') else BASE_URL + href
                
                categories.append({
                    "name": text,
                    "url": full_url
                })
        
        return categories
        
    except requests.RequestException as e:
        print(f"Error fetching liquor categories: {e}")
        return []

def scrape_products_from_category(category_url, category_name):
    """Scrape products from a specific category URL."""
    products = []
    page = 1
    
    while True:
        try:
            url = f"{category_url}&page={page}" if "?" in category_url else f"{category_url}?page={page}"
            print(f"\nScraping page {page} of {category_name}")
            
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find product containers
            product_containers = soup.select(".product-box, .product-item, [class*='product-list']")
            
            if not product_containers:
                print(f"No more products found in {category_name}")
                break
            
            print(f"Found {len(product_containers)} products on page {page}")
            
            for container in product_containers:
                try:
                    # Extract product name
                    name_elem = container.select_one(".product-name, .title, h2, h3, h4, h5")
                    if not name_elem:
                        continue
                    name = name_elem.text.strip()
                    
                    # Extract price
                    price_elem = container.select_one(".price, [class*='price']")
                    price = "N/A"
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # Extract only numbers and commas from price
                        price = re.sub(r"[^\d,]", "", price_text)
                    
                    # Extract product URL
                    link = container.select_one("a")
                    product_url = (link.get("href") if link else "N/A")
                    if product_url != "N/A" and not product_url.startswith('http'):
                        product_url = BASE_URL + product_url
                    
                    # Only add if we have at least a name and it's not a currency or home link
                    if name and not any(x in name.lower() for x in ['home', 'currency', 'npr']):
                        print(f"Found product: {name[:50]}...")
                        products.append({
                            "name": name,
                            "price": price,
                            "category": category_name,
                            "product_link": product_url
                        })
                    
                except Exception as e:
                    print(f"Error processing product: {e}")
                    continue
            
            # Check for next page
            next_button = soup.select_one("a.next, .pagination-next, [class*='next']")
            if not next_button:
                print(f"No more pages for {category_name}")
                break
                
            page += 1
            time.sleep(1)  # Respect the server
            
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
            
    return products

def scrape_all_liquor_products():
    """Scrape products from all liquor categories."""
    print("\nStarting to scrape liquor products...")
    all_products = []
    categories = get_liquor_categories()
    
    if not categories:
        print("No liquor categories found. Please check the website structure.")
        return []
    
    for category in categories:
        print(f"\nProcessing category: {category['name']}")
        products = scrape_products_from_category(
            category['url'],
            category['name']
        )
        all_products.extend(products)
    
    return all_products

def save_to_csv(products):
    """Save scraped data to CSV."""
    if not products:
        print("No products to save!")
        return
        
    fieldnames = ["name", "price", "category", "product_link"]
    
    with open("liquor_products1.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)
    print(f"\n✅ Saved {len(products)} products to liquor_products.csv")

if __name__ == "__main__":
    print("🚀 Starting the liquor product scraping process...")
    products = scrape_all_liquor_products()
    
    if products:
        save_to_csv(products)
        print(f"🎉 Successfully scraped {len(products)} liquor products!")
    else:
        print("🚫 No products were scraped. Check the debug output above for details.")