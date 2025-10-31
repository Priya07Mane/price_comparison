# import asyncio
# import random
# import re
# from datetime import datetime
# from urllib.parse import quote_plus
# from dataclasses import dataclass, asdict
# from typing import List, Optional
# from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# @dataclass
# class ProductFilter:
#     """Data class for product search filters"""
#     name: str
#     brand: Optional[str] = None
#     category: Optional[str] = None
#     color: Optional[str] = None
#     size: Optional[str] = None
#     min_price: Optional[float] = None
#     max_price: Optional[float] = None
#     gender: Optional[str] = None

# @dataclass
# class ProductResult:
#     """Data class for scraped product information"""
#     title: str
#     price: float
#     original_price: Optional[float]
#     discount_percentage: Optional[int]
#     rating: Optional[float]
#     review_count: Optional[int]
#     image_url: Optional[str]
#     product_url: str
#     store_name: str
#     brand: Optional[str]
#     availability: bool
#     shipping_info: Optional[str]
#     store_color: str

# class FashionPriceScraper:
#     """Main scraper class for fashion price comparison"""
    
#     def __init__(self):
#         self.browser: Optional[Browser] = None
#         self.playwright = None
#         self.stores = {
#             'myntra': {
#                 'base_url': 'https://www.myntra.com',
#                 'color': 'bg-pink-500'
#             },
#             'amazon': {
#                 'base_url': 'https://www.amazon.in',
#                 'color': 'bg-orange-500'
#             },
#             'flipkart': {
#                 'base_url': 'https://www.flipkart.com',
#                 'color': 'bg-blue-500'
#             }
#         }

#     async def initialize_browser(self):
#         """Initialize Playwright browser with anti-detection settings"""
#         if self.playwright is None:
#             self.playwright = await async_playwright().start()
        
#         if self.browser is None:
#             self.browser = await self.playwright.chromium.launch(
#                 headless=True,
#                 args=[
#                     '--no-sandbox',
#                     '--disable-setuid-sandbox',
#                     '--disable-dev-shm-usage',
#                     '--disable-blink-features=AutomationControlled',
#                     '--disable-web-security',
#                     '--disable-features=IsolateOrigins,site-per-process'
#                 ]
#             )
#             logger.info("Browser initialized successfully")

#     async def create_page(self, extra_wait: bool = False) -> Page:
#         """Create a new page with realistic settings"""
#         context = await self.browser.new_context(
#             viewport={'width': 1920, 'height': 1080},
#             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
#             locale='en-IN',
#             timezone_id='Asia/Kolkata',
#             java_script_enabled=True
#         )
        
#         page = await context.new_page()
        
#         await page.set_extra_http_headers({
#             'Accept-Language': 'en-IN,en-US;q=0.9,en;q=0.8',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#             'Sec-Fetch-Dest': 'document',
#             'Sec-Fetch-Mode': 'navigate',
#             'Sec-Fetch-Site': 'none',
#             'Sec-Fetch-User': '?1',
#             'Cache-Control': 'max-age=0'
#         })
        
#         # Enhanced stealth
#         await page.add_init_script("""
#             Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
#             Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
#             Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
#             window.chrome = { runtime: {} };
#         """)
        
#         return page

#     async def random_delay(self, min_seconds=1, max_seconds=2):
#         """Add random delay to mimic human behavior"""
#         delay = random.uniform(min_seconds, max_seconds)
#         await asyncio.sleep(delay)

#     def extract_price(self, price_text: str) -> Optional[float]:
#         """Extract numeric price from text"""
#         if not price_text:
#             return None
        
#         cleaned = re.sub(r'[^\d,.]', '', price_text)
#         cleaned = cleaned.replace(',', '')
        
#         match = re.search(r'\d+\.?\d*', cleaned)
#         if match:
#             try:
#                 price = float(match.group())
#                 if 50 <= price <= 1000000:
#                     return price
#             except ValueError:
#                 pass
#         return None

#     async def scrape_myntra(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Myntra for products"""
#         results = []
#         page = None
        
#         try:
#             page = await self.create_page(extra_wait=True)
            
#             query_parts = [filters.name]
#             if filters.color:
#                 query_parts.append(filters.color)
#             query = " ".join(query_parts)
            
#             category_map = {
#                 'dresses': 'dresses',
#                 'tops': 'tops',
#                 'jeans': 'jeans',
#                 'shoes': 'casual-shoes',
#                 'kurtas': 'kurtas',
#                 'shirts': 'shirts',
#                 'sarees': 'sarees'
#             }
#             category = category_map.get(filters.category, 'clothing')
            
#             # Use simpler URL format
#             url = f"https://www.myntra.com/{category}?q={quote_plus(query)}"
#             logger.info(f"Scraping Myntra: {url}")
            
#             # Try with longer timeout and domcontentloaded instead of networkidle
#             try:
#                 await page.goto(url, wait_until='domcontentloaded', timeout=45000)
#             except Exception as e:
#                 logger.warning(f"Myntra navigation issue: {e}")
#                 # Try alternative approach
#                 url = f"https://www.myntra.com/search?q={quote_plus(query)}"
#                 logger.info(f"Trying alternative Myntra URL: {url}")
#                 await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            
#             await self.random_delay(3, 5)
            
#             # Wait for products
#             try:
#                 await page.wait_for_selector('li.product-base, .results-base', timeout=15000)
#             except PlaywrightTimeout:
#                 logger.warning("Myntra: Products not loaded, trying to proceed anyway")
            
#             # Scroll to load more
#             await page.evaluate('window.scrollTo(0, 800)')
#             await asyncio.sleep(2)
#             await page.evaluate('window.scrollTo(0, 1600)')
#             await asyncio.sleep(1)
            
#             products = await page.query_selector_all('li.product-base')
#             logger.info(f"Found {len(products)} Myntra product containers")
            
#             for i, product in enumerate(products[:24]):  # Increased to 24
#                 try:
#                     title = None
#                     title_selectors = [
#                         'h3.product-brand',
#                         'h4.product-product',
#                         '.product-brand',
#                         '.product-product'
#                     ]
                    
#                     for selector in title_selectors:
#                         elem = await product.query_selector(selector)
#                         if elem:
#                             text = await elem.inner_text()
#                             if text and text.strip():
#                                 if not title:
#                                     title = text.strip()
#                                 else:
#                                     title = f"{title} {text.strip()}"
                    
#                     if not title or len(title) < 3:
#                         continue
                    
#                     # Price
#                     price = None
#                     price_selectors = [
#                         'span.product-discountedPrice',
#                         '.product-discountedPrice',
#                         'span[class*="discounted"]'
#                     ]
                    
#                     for selector in price_selectors:
#                         elem = await product.query_selector(selector)
#                         if elem:
#                             price_text = await elem.inner_text()
#                             price = self.extract_price(price_text)
#                             if price:
#                                 break
                    
#                     if not price:
#                         continue
                    
#                     # Original price
#                     original_price = None
#                     original_elem = await product.query_selector('span.product-strike, .product-strike')
#                     if original_elem:
#                         original_text = await original_elem.inner_text()
#                         original_price = self.extract_price(original_text)
                    
#                     # Discount
#                     discount_percentage = None
#                     if original_price and original_price > price:
#                         discount_percentage = int((original_price - price) / original_price * 100)
                    
#                     # Rating
#                     rating = None
#                     rating_elem = await product.query_selector('.product-ratingsContainer')
#                     if rating_elem:
#                         rating_text = await rating_elem.inner_text()
#                         match = re.search(r'(\d+\.?\d*)', rating_text)
#                         if match:
#                             rating = float(match.group(1))
                    
#                     # URL
#                     product_url = ""
#                     link_elem = await product.query_selector('a')
#                     if link_elem:
#                         href = await link_elem.get_attribute('href')
#                         if href:
#                             product_url = f"https://www.myntra.com{href}" if not href.startswith('http') else href
                    
#                     # Image
#                     image_url = None
#                     img_elem = await product.query_selector('img')
#                     if img_elem:
#                         image_url = await img_elem.get_attribute('src')
                    
#                     logger.info(f"Myntra: {title[:40]}... - ₹{price}")
                    
#                     results.append(ProductResult(
#                         title=title,
#                         price=price,
#                         original_price=original_price,
#                         discount_percentage=discount_percentage,
#                         rating=rating,
#                         review_count=None,
#                         image_url=image_url,
#                         product_url=product_url,
#                         store_name="Myntra",
#                         brand=None,
#                         availability=True,
#                         shipping_info="Free Shipping",
#                         store_color="bg-pink-500"
#                     ))
                    
#                 except Exception as e:
#                     logger.debug(f"Error extracting Myntra product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Myntra: {e}")
#         finally:
#             if page:
#                 await page.close()
            
#         logger.info(f"Myntra: Returning {len(results)} products")
#         return results

#     async def scrape_amazon(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Amazon for products"""
#         results = []
#         page = None
        
#         try:
#             page = await self.create_page(extra_wait=True)
            
#             query_parts = [filters.name]
#             if filters.brand:
#                 query_parts.append(filters.brand)
#             if filters.color:
#                 query_parts.append(filters.color)
#             query = " ".join(query_parts)
            
#             url = f"https://www.amazon.in/s?k={quote_plus(query)}&i=apparel"
#             logger.info(f"Scraping Amazon: {url}")
            
#             # Use domcontentloaded and longer timeout
#             await page.goto(url, wait_until='domcontentloaded', timeout=45000)
#             await self.random_delay(3, 5)
            
#             # Scroll to trigger lazy loading
#             await page.evaluate('window.scrollTo(0, 800)')
#             await asyncio.sleep(2)
#             await page.evaluate('window.scrollTo(0, 1600)')
#             await asyncio.sleep(1)
            
#             try:
#                 await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=10000)
#             except PlaywrightTimeout:
#                 logger.warning("Amazon: Products not loaded, trying to proceed")
            
#             products = await page.query_selector_all('[data-component-type="s-search-result"]')
#             logger.info(f"Found {len(products)} Amazon product containers")
            
#             for i, product in enumerate(products[:24]):  # Increased to 24
#                 try:
#                     # Title
#                     title = None
#                     title_elem = await product.query_selector('h2 span')
#                     if title_elem:
#                         title = await title_elem.inner_text()
                    
#                     if not title or len(title.strip()) < 3:
#                         h2_elem = await product.query_selector('h2')
#                         if h2_elem:
#                             title = await h2_elem.inner_text()
                    
#                     if title:
#                         title = title.strip()
                    
#                     if not title or len(title) < 3:
#                         continue
                    
#                     # Price
#                     price = None
#                     price_elem = await product.query_selector('.a-price .a-offscreen')
#                     if price_elem:
#                         price_text = await price_elem.inner_text()
#                         price = self.extract_price(price_text)
                    
#                     if not price:
#                         price_elem = await product.query_selector('.a-price-whole')
#                         if price_elem:
#                             price_text = await price_elem.inner_text()
#                             price = self.extract_price(price_text)
                    
#                     if not price:
#                         continue
                    
#                     # Rating
#                     rating = None
#                     rating_elem = await product.query_selector('.a-icon-alt')
#                     if rating_elem:
#                         rating_text = await rating_elem.inner_text()
#                         match = re.search(r'(\d+\.?\d*)', rating_text)
#                         if match:
#                             rating = float(match.group(1))
                    
#                     # URL
#                     product_url = ""
#                     link_elem = await product.query_selector('h2 a, a.a-link-normal')
#                     if link_elem:
#                         href = await link_elem.get_attribute('href')
#                         if href:
#                             product_url = f"https://www.amazon.in{href}" if not href.startswith('http') else href
                    
#                     # Image
#                     image_url = None
#                     img_elem = await product.query_selector('img')
#                     if img_elem:
#                         image_url = await img_elem.get_attribute('src')
                    
#                     logger.info(f"Amazon: {title[:40]}... - ₹{price}")
                    
#                     results.append(ProductResult(
#                         title=title,
#                         price=price,
#                         original_price=None,
#                         discount_percentage=None,
#                         rating=rating,
#                         review_count=None,
#                         image_url=image_url,
#                         product_url=product_url,
#                         store_name="Amazon",
#                         brand=None,
#                         availability=True,
#                         shipping_info="Check Delivery",
#                         store_color="bg-orange-500"
#                     ))
                    
#                 except Exception as e:
#                     logger.debug(f"Error extracting Amazon product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Amazon: {e}")
#         finally:
#             if page:
#                 await page.close()
        
#         logger.info(f"Amazon: Returning {len(results)} products")
#         return results

#     async def scrape_flipkart(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Flipkart for products"""
#         results = []
#         page = None
        
#         try:
#             page = await self.create_page()
            
#             query_parts = [filters.name]
#             if filters.color:
#                 query_parts.append(filters.color)
#             query = " ".join(query_parts)
            
#             url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
#             logger.info(f"Scraping Flipkart: {url}")
            
#             await page.goto(url, wait_until='domcontentloaded', timeout=45000)
#             await self.random_delay(2, 3)
            
#             # Close login popup
#             try:
#                 close_btn = await page.query_selector('button._2KpZ6l, button._2AkmmA')
#                 if close_btn:
#                     await close_btn.click()
#                     await asyncio.sleep(1)
#             except:
#                 pass
            
#             # Scroll to load more products
#             await page.evaluate('window.scrollTo(0, 800)')
#             await asyncio.sleep(1)
#             await page.evaluate('window.scrollTo(0, 1600)')
#             await asyncio.sleep(1)
#             await page.evaluate('window.scrollTo(0, 2400)')
#             await asyncio.sleep(1)
            
#             # Try multiple selectors
#             products = []
#             selectors = ['div[data-id]', '._1AtVbE', '._13oc-S', 'div[class*="slAVV4"]', 'div[class*="tUxRFH"]']
            
#             for selector in selectors:
#                 products = await page.query_selector_all(selector)
#                 if products and len(products) > 5:
#                     logger.info(f"Flipkart: Using selector '{selector}', found {len(products)} containers")
#                     break
            
#             if not products:
#                 logger.warning("Flipkart: No product containers found")
#                 return results
            
#             for i, product in enumerate(products[:30]):  # Increased to 30
#                 try:
#                     # Title
#                     title = None
#                     title_selectors = [
#                         'a[class*="IRpwTa"]',
#                         'a[class*="wjcEIp"]',
#                         '._4rR01T',
#                         '.s1Q9rs',
#                         'a[title]',
#                         'div[class*="KzDlHZ"]'
#                     ]
                    
#                     for selector in title_selectors:
#                         elem = await product.query_selector(selector)
#                         if elem:
#                             if 'title' in selector and '[title]' in selector:
#                                 title = await elem.get_attribute('title')
#                             else:
#                                 title = await elem.inner_text()
                            
#                             if title and title.strip() and len(title.strip()) > 3:
#                                 title = title.strip()
#                                 break
                    
#                     if not title or len(title) < 3:
#                         continue
                    
#                     # Price
#                     price = None
#                     price_selectors = [
#                         'div[class*="Nx9bqj"]',
#                         'div[class*="_30jeq3"]',
#                         '._30jeq3',
#                         '._1_WHN1',
#                         'div[class*="_25b18c"]'
#                     ]
                    
#                     for selector in price_selectors:
#                         elem = await product.query_selector(selector)
#                         if elem:
#                             price_text = await elem.inner_text()
#                             price = self.extract_price(price_text)
#                             if price:
#                                 break
                    
#                     if not price:
#                         continue
                    
#                     # URL
#                     product_url = ""
#                     link_elem = await product.query_selector('a')
#                     if link_elem:
#                         href = await link_elem.get_attribute('href')
#                         if href:
#                             product_url = f"https://www.flipkart.com{href}" if not href.startswith('http') else href
                    
#                     # Image
#                     image_url = None
#                     img_elem = await product.query_selector('img')
#                     if img_elem:
#                         image_url = await img_elem.get_attribute('src')
                    
#                     logger.info(f"Flipkart: {title[:40]}... - ₹{price}")
                    
#                     results.append(ProductResult(
#                         title=title,
#                         price=price,
#                         original_price=None,
#                         discount_percentage=None,
#                         rating=None,
#                         review_count=None,
#                         image_url=image_url,
#                         product_url=product_url,
#                         store_name="Flipkart",
#                         brand=None,
#                         availability=True,
#                         shipping_info="Free Delivery",
#                         store_color="bg-blue-500"
#                     ))
                    
#                 except Exception as e:
#                     logger.debug(f"Error extracting Flipkart product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Flipkart: {e}")
#         finally:
#             if page:
#                 await page.close()
        
#         logger.info(f"Flipkart: Returning {len(results)} products")
#         return results

#     async def scrape_all_stores(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape all stores concurrently"""
#         await self.initialize_browser()
        
#         tasks = [
#             self.scrape_myntra(filters),
#             self.scrape_amazon(filters),
#             self.scrape_flipkart(filters),
#         ]
        
#         results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
#         all_results = []
#         store_names = ['Myntra', 'Amazon', 'Flipkart']
#         for i, results in enumerate(results_list):
#             if isinstance(results, list):
#                 logger.info(f"{store_names[i]}: Got {len(results)} valid products")
#                 all_results.extend(results)
#             else:
#                 logger.error(f"{store_names[i]}: Error - {results}")
        
#         if filters.max_price:
#             all_results = [r for r in all_results if r.price <= filters.max_price]
        
#         all_results.sort(key=lambda x: x.price)
        
#         logger.info(f"TOTAL products found across all stores: {len(all_results)}")
#         return all_results

#     async def close(self):
#         """Close the browser"""
#         if self.browser:
#             await self.browser.close()
#             self.browser = None
#         if self.playwright:
#             await self.playwright.stop()
#             self.playwright = None

# # FastAPI setup
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# app = FastAPI(title="Fashion Price Comparison API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class SearchFilters(BaseModel):
#     name: str
#     brand: Optional[str] = None
#     category: Optional[str] = None
#     color: Optional[str] = None
#     gender: Optional[str] = None
#     max_price: Optional[float] = None

# @app.post("/api/search")
# async def search_products(filters: SearchFilters):
#     try:
#         logger.info(f"Search request: {filters}")
#         scraper = FashionPriceScraper()
        
#         product_filter = ProductFilter(
#             name=filters.name,
#             brand=filters.brand,
#             category=filters.category,
#             color=filters.color,
#             gender=filters.gender,
#             max_price=filters.max_price
#         )
        
#         results = await scraper.scrape_all_stores(product_filter)
#         serializable_results = [asdict(result) for result in results]
        
#         await scraper.close()
        
#         logger.info(f"API: Returning {len(serializable_results)} results to client")
#         return serializable_results
        
#     except Exception as e:
#         logger.error(f"API Error: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/")
# async def root():
#     return {
#         "message": "Fashion Price Comparison API",
#         "version": "2.1",
#         "status": "active",
#         "stores": ["Myntra", "Amazon", "Flipkart"]
#     }

# @app.get("/health")
# async def health():
#     return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

import asyncio
import random
import re
from datetime import datetime
from urllib.parse import quote_plus
from dataclasses import dataclass, asdict
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
import logging

# Import AI module
from ai_model import get_analyzer, ImageAnalysisResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProductFilter:
    """Data class for product search filters"""
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    gender: Optional[str] = None

@dataclass
class ProductResult:
    """Data class for scraped product information"""
    title: str
    price: float
    original_price: Optional[float]
    discount_percentage: Optional[int]
    rating: Optional[float]
    review_count: Optional[int]
    image_url: Optional[str]
    product_url: str
    store_name: str
    brand: Optional[str]
    availability: bool
    shipping_info: Optional[str]
    store_color: str

class FashionPriceScraper:
    """Main scraper class for fashion price comparison"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.stores = {
            'myntra': {
                'base_url': 'https://www.myntra.com',
                'color': 'bg-pink-500'
            },
            'amazon': {
                'base_url': 'https://www.amazon.in',
                'color': 'bg-orange-500'
            },
            'flipkart': {
                'base_url': 'https://www.flipkart.com',
                'color': 'bg-blue-500'
            }
        }

    async def initialize_browser(self):
        """Initialize Playwright browser with anti-detection settings"""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
        
        if self.browser is None:
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            logger.info("Browser initialized successfully")

    async def create_page(self, extra_wait: bool = False) -> Page:
        """Create a new page with realistic settings"""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='en-IN',
            timezone_id='Asia/Kolkata',
            java_script_enabled=True
        )
        
        page = await context.new_page()
        
        await page.set_extra_http_headers({
            'Accept-Language': 'en-IN,en-US;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)
        
        return page

    async def random_delay(self, min_seconds=1, max_seconds=2):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        cleaned = re.sub(r'[^\d,.]', '', price_text)
        cleaned = cleaned.replace(',', '')
        
        match = re.search(r'\d+\.?\d*', cleaned)
        if match:
            try:
                price = float(match.group())
                if 50 <= price <= 1000000:
                    return price
            except ValueError:
                pass
        return None

    async def scrape_myntra(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Myntra for products"""
        results = []
        page = None
        
        try:
            page = await self.create_page(extra_wait=True)
            
            query_parts = [filters.name]
            if filters.color:
                query_parts.append(filters.color)
            query = " ".join(query_parts)
            
            category_map = {
                'dresses': 'dresses',
                'tops': 'tops',
                'jeans': 'jeans',
                'shoes': 'casual-shoes',
                'kurtas': 'kurtas',
                'shirts': 'shirts',
                'sarees': 'sarees'
            }
            category = category_map.get(filters.category, 'clothing')
            
            url = f"https://www.myntra.com/{category}?q={quote_plus(query)}"
            logger.info(f"Scraping Myntra: {url}")
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            except Exception as e:
                logger.warning(f"Myntra navigation issue: {e}")
                url = f"https://www.myntra.com/search?q={quote_plus(query)}"
                logger.info(f"Trying alternative Myntra URL: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            
            await self.random_delay(3, 5)
            
            try:
                await page.wait_for_selector('li.product-base, .results-base', timeout=15000)
            except PlaywrightTimeout:
                logger.warning("Myntra: Products not loaded, trying to proceed anyway")
            
            await page.evaluate('window.scrollTo(0, 800)')
            await asyncio.sleep(2)
            await page.evaluate('window.scrollTo(0, 1600)')
            await asyncio.sleep(1)
            
            products = await page.query_selector_all('li.product-base')
            logger.info(f"Found {len(products)} Myntra product containers")
            
            for i, product in enumerate(products[:24]):
                try:
                    title = None
                    title_selectors = ['h3.product-brand', 'h4.product-product', '.product-brand', '.product-product']
                    
                    for selector in title_selectors:
                        elem = await product.query_selector(selector)
                        if elem:
                            text = await elem.inner_text()
                            if text and text.strip():
                                if not title:
                                    title = text.strip()
                                else:
                                    title = f"{title} {text.strip()}"
                    
                    if not title or len(title) < 3:
                        continue
                    
                    price = None
                    price_selectors = ['span.product-discountedPrice', '.product-discountedPrice', 'span[class*="discounted"]']
                    
                    for selector in price_selectors:
                        elem = await product.query_selector(selector)
                        if elem:
                            price_text = await elem.inner_text()
                            price = self.extract_price(price_text)
                            if price:
                                break
                    
                    if not price:
                        continue
                    
                    original_price = None
                    original_elem = await product.query_selector('span.product-strike, .product-strike')
                    if original_elem:
                        original_text = await original_elem.inner_text()
                        original_price = self.extract_price(original_text)
                    
                    discount_percentage = None
                    if original_price and original_price > price:
                        discount_percentage = int((original_price - price) / original_price * 100)
                    
                    rating = None
                    rating_elem = await product.query_selector('.product-ratingsContainer')
                    if rating_elem:
                        rating_text = await rating_elem.inner_text()
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            rating = float(match.group(1))
                    
                    product_url = ""
                    link_elem = await product.query_selector('a')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.myntra.com{href}" if not href.startswith('http') else href
                    
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
                    logger.info(f"Myntra: {title[:40]}... - ₹{price}")
                    
                    results.append(ProductResult(
                        title=title,
                        price=price,
                        original_price=original_price,
                        discount_percentage=discount_percentage,
                        rating=rating,
                        review_count=None,
                        image_url=image_url,
                        product_url=product_url,
                        store_name="Myntra",
                        brand=None,
                        availability=True,
                        shipping_info="Free Shipping",
                        store_color="bg-pink-500"
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error extracting Myntra product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Myntra: {e}")
        finally:
            if page:
                await page.close()
            
        logger.info(f"Myntra: Returning {len(results)} products")
        return results

    async def scrape_amazon(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Amazon for products"""
        results = []
        page = None
        
        try:
            page = await self.create_page(extra_wait=True)
            
            query_parts = [filters.name]
            if filters.brand:
                query_parts.append(filters.brand)
            if filters.color:
                query_parts.append(filters.color)
            query = " ".join(query_parts)
            
            url = f"https://www.amazon.in/s?k={quote_plus(query)}&i=apparel"
            logger.info(f"Scraping Amazon: {url}")
            
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            await self.random_delay(3, 5)
            
            await page.evaluate('window.scrollTo(0, 800)')
            await asyncio.sleep(2)
            await page.evaluate('window.scrollTo(0, 1600)')
            await asyncio.sleep(1)
            
            try:
                await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=10000)
            except PlaywrightTimeout:
                logger.warning("Amazon: Products not loaded, trying to proceed")
            
            products = await page.query_selector_all('[data-component-type="s-search-result"]')
            logger.info(f"Found {len(products)} Amazon product containers")
            
            for i, product in enumerate(products[:24]):
                try:
                    title = None
                    title_elem = await product.query_selector('h2 span')
                    if title_elem:
                        title = await title_elem.inner_text()
                    
                    if not title or len(title.strip()) < 3:
                        h2_elem = await product.query_selector('h2')
                        if h2_elem:
                            title = await h2_elem.inner_text()
                    
                    if title:
                        title = title.strip()
                    
                    if not title or len(title) < 3:
                        continue
                    
                    price = None
                    price_elem = await product.query_selector('.a-price .a-offscreen')
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        price = self.extract_price(price_text)
                    
                    if not price:
                        price_elem = await product.query_selector('.a-price-whole')
                        if price_elem:
                            price_text = await price_elem.inner_text()
                            price = self.extract_price(price_text)
                    
                    if not price:
                        continue
                    
                    rating = None
                    rating_elem = await product.query_selector('.a-icon-alt')
                    if rating_elem:
                        rating_text = await rating_elem.inner_text()
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            rating = float(match.group(1))
                    
                    product_url = ""
                    link_elem = await product.query_selector('h2 a, a.a-link-normal')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.amazon.in{href}" if not href.startswith('http') else href
                    
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
                    logger.info(f"Amazon: {title[:40]}... - ₹{price}")
                    
                    results.append(ProductResult(
                        title=title,
                        price=price,
                        original_price=None,
                        discount_percentage=None,
                        rating=rating,
                        review_count=None,
                        image_url=image_url,
                        product_url=product_url,
                        store_name="Amazon",
                        brand=None,
                        availability=True,
                        shipping_info="Check Delivery",
                        store_color="bg-orange-500"
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error extracting Amazon product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Amazon: {e}")
        finally:
            if page:
                await page.close()
        
        logger.info(f"Amazon: Returning {len(results)} products")
        return results

    async def scrape_flipkart(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Flipkart for products"""
        results = []
        page = None
        
        try:
            page = await self.create_page()
            
            query_parts = [filters.name]
            if filters.color:
                query_parts.append(filters.color)
            query = " ".join(query_parts)
            
            url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
            logger.info(f"Scraping Flipkart: {url}")
            
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            await self.random_delay(2, 3)
            
            try:
                close_btn = await page.query_selector('button._2KpZ6l, button._2AkmmA')
                if close_btn:
                    await close_btn.click()
                    await asyncio.sleep(1)
            except:
                pass
            
            await page.evaluate('window.scrollTo(0, 800)')
            await asyncio.sleep(1)
            await page.evaluate('window.scrollTo(0, 1600)')
            await asyncio.sleep(1)
            await page.evaluate('window.scrollTo(0, 2400)')
            await asyncio.sleep(1)
            
            products = []
            selectors = ['div[data-id]', '._1AtVbE', '._13oc-S', 'div[class*="slAVV4"]', 'div[class*="tUxRFH"]']
            
            for selector in selectors:
                products = await page.query_selector_all(selector)
                if products and len(products) > 5:
                    logger.info(f"Flipkart: Using selector '{selector}', found {len(products)} containers")
                    break
            
            if not products:
                logger.warning("Flipkart: No product containers found")
                return results
            
            for i, product in enumerate(products[:30]):
                try:
                    title = None
                    title_selectors = ['a[class*="IRpwTa"]', 'a[class*="wjcEIp"]', '._4rR01T', '.s1Q9rs', 'a[title]', 'div[class*="KzDlHZ"]']
                    
                    for selector in title_selectors:
                        elem = await product.query_selector(selector)
                        if elem:
                            if 'title' in selector and '[title]' in selector:
                                title = await elem.get_attribute('title')
                            else:
                                title = await elem.inner_text()
                            
                            if title and title.strip() and len(title.strip()) > 3:
                                title = title.strip()
                                break
                    
                    if not title or len(title) < 3:
                        continue
                    
                    price = None
                    price_selectors = ['div[class*="Nx9bqj"]', 'div[class*="_30jeq3"]', '._30jeq3', '._1_WHN1', 'div[class*="_25b18c"]']
                    
                    for selector in price_selectors:
                        elem = await product.query_selector(selector)
                        if elem:
                            price_text = await elem.inner_text()
                            price = self.extract_price(price_text)
                            if price:
                                break
                    
                    if not price:
                        continue
                    
                    product_url = ""
                    link_elem = await product.query_selector('a')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.flipkart.com{href}" if not href.startswith('http') else href
                    
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
                    logger.info(f"Flipkart: {title[:40]}... - ₹{price}")
                    
                    results.append(ProductResult(
                        title=title,
                        price=price,
                        original_price=None,
                        discount_percentage=None,
                        rating=None,
                        review_count=None,
                        image_url=image_url,
                        product_url=product_url,
                        store_name="Flipkart",
                        brand=None,
                        availability=True,
                        shipping_info="Free Delivery",
                        store_color="bg-blue-500"
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error extracting Flipkart product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Flipkart: {e}")
        finally:
            if page:
                await page.close()
        
        logger.info(f"Flipkart: Returning {len(results)} products")
        return results

    async def scrape_all_stores(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape all stores concurrently"""
        await self.initialize_browser()
        
        tasks = [
            self.scrape_myntra(filters),
            self.scrape_amazon(filters),
            self.scrape_flipkart(filters),
        ]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        store_names = ['Myntra', 'Amazon', 'Flipkart']
        for i, results in enumerate(results_list):
            if isinstance(results, list):
                logger.info(f"{store_names[i]}: Got {len(results)} valid products")
                all_results.extend(results)
            else:
                logger.error(f"{store_names[i]}: Error - {results}")
        
        if filters.max_price:
            all_results = [r for r in all_results if r.price <= filters.max_price]
        
        all_results.sort(key=lambda x: x.price)
        
        logger.info(f"TOTAL products found across all stores: {len(all_results)}")
        return all_results

    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

# FastAPI setup
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Fashion Price Comparison API with AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchFilters(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    max_price: Optional[float] = None

@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze uploaded fashion image using AI"""
    try:
        logger.info(f"Received image: {file.filename}")
        
        # Read image bytes
        image_bytes = await file.read()
        
        # Get analyzer instance
        analyzer = get_analyzer()
        
        # Analyze image
        result = analyzer.analyze_image(image_bytes)
        
        logger.info(f"Analysis result: {result.description}")
        
        return {
            "success": True,
            "analysis": {
                "category": result.category,
                "color": result.color_name,
                "dominant_colors": result.dominant_colors,
                "pattern": result.pattern,
                "style": result.style,
                "confidence": result.confidence,
                "description": result.description
            }
        }
        
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@app.post("/api/search-by-image")
async def search_by_image(
    file: UploadFile = File(...),
    brand: Optional[str] = Form(None),
    max_price: Optional[float] = Form(None)
):
    """Analyze image and search for similar products"""
    try:
        logger.info(f"Image search request: {file.filename}")
        
        # Read and analyze image
        image_bytes = await file.read()
        analyzer = get_analyzer()
        analysis = analyzer.analyze_image(image_bytes)
        
        logger.info(f"AI Analysis: {analysis.description}")
        
        # Create search filter from AI analysis
        product_filter = ProductFilter(
            name=analysis.description,
            brand=brand,
            category=analysis.category,
            color=analysis.color_name,
            max_price=max_price,
            gender='women'  # Default, could be enhanced with AI
        )
        
        # Search across stores
        scraper = FashionPriceScraper()
        results = await scraper.scrape_all_stores(product_filter)
        serializable_results = [asdict(result) for result in results]
        
        await scraper.close()
        
        logger.info(f"Found {len(serializable_results)} products")
        
        return {
            "success": True,
            "ai_analysis": {
                "category": analysis.category,
                "color": analysis.color_name,
                "pattern": analysis.pattern,
                "description": analysis.description,
                "confidence": analysis.confidence
            },
            "products": serializable_results
        }
        
    except Exception as e:
        logger.error(f"Image search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

@app.post("/api/search")
async def search_products(filters: SearchFilters):
    """Traditional text-based search"""
    try:
        logger.info(f"Search request: {filters}")
        scraper = FashionPriceScraper()
        
        product_filter = ProductFilter(
            name=filters.name,
            brand=filters.brand,
            category=filters.category,
            color=filters.color,
            gender=filters.gender,
            max_price=filters.max_price
        )
        
        results = await scraper.scrape_all_stores(product_filter)
        serializable_results = [asdict(result) for result in results]
        
        await scraper.close()
        
        logger.info(f"API: Returning {len(serializable_results)} results to client")
        return serializable_results
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Fashion Price Comparison API with AI",
        "version": "3.0",
        "status": "active",
        "features": ["AI Image Analysis", "Price Comparison", "Multi-store Scraping"],
        "stores": ["Myntra", "Amazon", "Flipkart"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    