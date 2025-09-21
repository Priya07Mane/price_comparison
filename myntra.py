import requests
from fake_useragent import UserAgent
import os
import urllib3
import time
import random
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_chrome_driver():
    """Setup Chrome driver with anti-detection options"""
    options = Options()
    
    # Basic options
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Anti-detection measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Set a realistic user agent
    ua = UserAgent()
    options.add_argument(f"--user-agent={ua.random}")
    
    # Window size
    options.add_argument("--window-size=1920,1080")
    
    # Disable images and CSS for faster loading (optional)
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    options.add_experimental_option("prefs", prefs)
    
    return options

def scrape_myntra_with_selenium():
    """Scrape Myntra using Selenium with better error handling"""
    
    options = setup_chrome_driver()
    driver = None
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Add random delay
        time.sleep(random.uniform(2, 5))
        
        url = "https://www.myntra.com/dresses?f=Gender%3Amen%20women%2Cwomen"
        print(f"Attempting to access: {url}")
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 20)
        
        # Wait for specific elements to ensure page is loaded
        try:
            # Wait for product listings or main content to load
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-base")))
            print("Page loaded successfully!")
        except:
            print("Product elements not found, but page might have loaded")
        
        # Add another small delay
        time.sleep(random.uniform(3, 6))
        
        html = driver.page_source
        
        # Save HTML content
        with open("myntra_dresses.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        print("HTML content saved to myntra_dresses.html")
        return True
        
    except Exception as e:
        print(f"Selenium scraping failed: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()

def scrape_myntra_with_requests():
    """Alternative method using requests with proxy"""
    
    session = requests.Session()
    
    # More realistic headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Referer": "https://www.google.com/",
    }
    
    token = os.getenv("PROXY_TOKEN")
    
    if token:
        proxyModeUrl = f"http://{token}:@proxy.scrape.do:8080"
        proxies = {
            "http": proxyModeUrl,
            "https": proxyModeUrl,
        }
    else:
        proxies = {}
        print("No proxy token found, proceeding without proxy")
    
    url = "https://www.myntra.com/dresses?f=Gender%3Amen%20women%2Cwomen"
    
    try:
        print(f"Attempting to access: {url}")
        
        # Add session cookies and make a request
        session.headers.update(headers)
        
        response = session.get(url, proxies=proxies, verify=False, timeout=30)
        
        if response.status_code == 200:
            with open("myntra_dresses_requests.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("HTML content saved to myntra_dresses_requests.html")
            return True
        else:
            print(f"Request failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Requests method failed: {str(e)}")
        return False

def main():
    """Main function to try both methods"""
    print("Starting Myntra scraping...")
    
    # Try Selenium first
    print("\n--- Trying Selenium method ---")
    if scrape_myntra_with_selenium():
        print("Selenium method successful!")
        return
    
    # If Selenium fails, try requests
    print("\n--- Trying Requests method ---")
    if scrape_myntra_with_requests():
        print("Requests method successful!")
        return
    
    print("\nBoth methods failed. Myntra might be blocking requests.")
    print("Consider:")
    print("1. Using residential proxies")
    print("2. Adding more delays between requests")
    print("3. Using a different approach like scrapy with rotating user agents")

if __name__ == "__main__":
    main()