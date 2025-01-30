import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# Base URL - Change this to the website you want to scrape
BASE_URL = "Add your base URL here"  # Example: "https://example.com"

# Headers - Modify if needed
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# Modify selectors based on your target website
CATEGORY_SELECTOR = "a[href*='/category']"  # Adjust this selector to match category links
PRODUCT_CONTAINER_SELECTOR = ".product-box, .product-item"  # Modify to match product containers
PRODUCT_NAME_SELECTOR = ".product-name, .title, h2, h3, h4, h5"  # Adjust for product name
PRODUCT_PRICE_SELECTOR = ".price, [class*='price']"  # Adjust for price element
NEXT_PAGE_SELECTOR = "a.next, .pagination-next"  # Modify for next page button


def get_categories():
    """Extract category URLs dynamically."""
    try:
        print("Fetching main page...")
        response = requests.get(BASE_URL, headers=HEADERS)  # Modify if categories are on a different page
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        categories = []
        category_links = soup.select(CATEGORY_SELECTOR)
        
        print(f"Found {len(category_links)} category links")
        
        for link in category_links:
            href = link.get("href")
            text = link.text.strip()
            
            if href and text:
                full_url = href if href.startswith('http') else BASE_URL + href
                categories.append({"name": text, "url": full_url})
        
        return categories
        
    except requests.RequestException as e:
        print(f"Error fetching categories: {e}")
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
            product_containers = soup.select(PRODUCT_CONTAINER_SELECTOR)
            
            if not product_containers:
                print(f"No more products found in {category_name}")
                break
            
            print(f"Found {len(product_containers)} products on page {page}")
            
            for container in product_containers:
                try:
                    # Extract product name
                    name_elem = container.select_one(PRODUCT_NAME_SELECTOR)
                    name = name_elem.text.strip() if name_elem else "N/A"
                    
                    # Extract price
                    price_elem = container.select_one(PRODUCT_PRICE_SELECTOR)
                    price = re.sub(r"[^\d,]", "", price_elem.text.strip()) if price_elem else "N/A"
                    
                    # Extract product URL
                    link = container.select_one("a")
                    product_url = (link.get("href") if link else "N/A")
                    if product_url != "N/A" and not product_url.startswith('http'):
                        product_url = BASE_URL + product_url
                    
                    products.append({"name": name, "price": price, "category": category_name, "product_link": product_url})
                    
                except Exception as e:
                    print(f"Error processing product: {e}")
                    continue
            
            next_button = soup.select_one(NEXT_PAGE_SELECTOR)
            if not next_button:
                print(f"No more pages for {category_name}")
                break
                
            page += 1
            time.sleep(1)
            
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
            
    return products


def scrape_all_products():
    """Scrape products from all categories."""
    print("\nStarting scraping process...")
    all_products = []
    categories = get_categories()
    
    if not categories:
        print("No categories found. Please check the website structure.")
        return []
    
    for category in categories:
        print(f"\nProcessing category: {category['name']}")
        products = scrape_products_from_category(category['url'], category['name'])
        all_products.extend(products)
    
    return all_products


def save_to_csv(products, filename="products.csv"):  # Change filename if needed
    """Save scraped data to CSV."""
    if not products:
        print("No products to save!")
        return
        
    fieldnames = ["name", "price", "category", "product_link"]  # Modify headers as needed
    
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)
    print(f"\n✅ Saved {len(products)} products to {filename}")


if __name__ == "__main__":
    print("🚀 Starting the scraping process...")
    products = scrape_all_products()
    
    if products:
        save_to_csv(products, "scraped_data.csv")  # Change filename if needed
        print(f"🎉 Successfully scraped {len(products)} products!")
    else:
        print("🚫 No products were scraped. Check the debug output above for details.")
