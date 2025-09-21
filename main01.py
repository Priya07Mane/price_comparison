import asyncio
import random
import time
from datetime import datetime
from urllib.parse import quote_plus
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page
import logging

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
        self.stores = {
            'myntra': {
                'base_url': 'https://www.myntra.com',
                'search_url': 'https://www.myntra.com/{category}?f=Gender%3A{gender}&q={query}',
                'color': 'bg-pink-500'
            },
            'amazon': {
                'base_url': 'https://www.amazon.in',
                'search_url': 'https://www.amazon.in/s?k={query}&rh=n%3A1571271031',  # Fashion category
                'color': 'bg-orange-500'
            },
            'flipkart': {
                'base_url': 'https://www.flipkart.com',
                'search_url': 'https://www.flipkart.com/search?q={query}&otracker=search&marketplace=FLIPKART',
                'color': 'bg-blue-500'
            },
            'ajio': {
                'base_url': 'https://www.ajio.com',
                'search_url': 'https://www.ajio.com/search/?text={query}',
                'color': 'bg-indigo-500'
            }
        }

    async def initialize_browser(self):
        """Initialize Playwright browser with anti-detection settings"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )

    async def create_page(self) -> Page:
        """Create a new page with realistic settings"""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Add extra headers
        await page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return page

    async def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    def build_search_url(self, store: str, filters: ProductFilter) -> str:
        """Build search URL based on store and filters"""
        store_config = self.stores[store]
        query = quote_plus(f"{filters.name} {filters.brand or ''} {filters.color or ''}".strip())
        
        if store == 'myntra':
            category = filters.category or 'dresses'
            gender = filters.gender or 'women'
            return store_config['search_url'].format(
                category=category, 
                gender=gender, 
                query=query
            )
        else:
            return store_config['search_url'].format(query=query)

    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract numbers
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            return float(price_match.group())
        return None

    async def scrape_myntra(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Myntra for products"""
        results = []
        page = await self.create_page()
        
        try:
            url = self.build_search_url('myntra', filters)
            logger.info(f"Scraping Myntra: {url}")
            
            await page.goto(url, wait_until='networkidle')
            await self.random_delay(2, 4)
            
            # Wait for products to load
            await page.wait_for_selector('.product-base', timeout=10000)
            
            # Extract product information
            products = await page.query_selector_all('.product-base')
            
            for i, product in enumerate(products[:6]):  # Limit to first 6 products
                try:
                    title_elem = await product.query_selector('.product-product')
                    title = await title_elem.inner_text() if title_elem else "Unknown Product"
                    
                    price_elem = await product.query_selector('.product-discountedPrice')
                    price_text = await price_elem.inner_text() if price_elem else ""
                    price = self.extract_price(price_text)
                    
                    original_price_elem = await product.query_selector('.product-strike')
                    original_price_text = await original_price_elem.inner_text() if original_price_elem else ""
                    original_price = self.extract_price(original_price_text)
                    
                    rating_elem = await product.query_selector('.product-ratingsContainer')
                    rating_text = await rating_elem.inner_text() if rating_elem else ""
                    rating = float(rating_text.split()[0]) if rating_text and rating_text.split() else None
                    
                    link_elem = await product.query_selector('a')
                    product_url = await link_elem.get_attribute('href') if link_elem else ""
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.myntra.com{product_url}"
                    
                    image_elem = await product.query_selector('img')
                    image_url = await image_elem.get_attribute('src') if image_elem else None
                    
                    if price:
                        discount_percentage = None
                        if original_price and original_price > price:
                            discount_percentage = int((original_price - price) / original_price * 100)
                        
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
                    logger.error(f"Error extracting Myntra product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Myntra: {e}")
        finally:
            await page.close()
            
        return results

    async def scrape_amazon(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Amazon for products"""
        results = []
        page = await self.create_page()
        
        try:
            url = self.build_search_url('amazon', filters)
            logger.info(f"Scraping Amazon: {url}")
            
            await page.goto(url, wait_until='networkidle')
            await self.random_delay(2, 4)
            
            # Wait for products to load
            await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=10000)
            
            products = await page.query_selector_all('[data-component-type="s-search-result"]')
            
            for i, product in enumerate(products[:6]):
                try:
                    title_elem = await product.query_selector('h2 a span')
                    title = await title_elem.inner_text() if title_elem else "Unknown Product"
                    
                    price_elem = await product.query_selector('.a-price-whole')
                    price_text = await price_elem.inner_text() if price_elem else ""
                    price = self.extract_price(price_text)
                    
                    rating_elem = await product.query_selector('.a-icon-alt')
                    rating_text = await rating_elem.inner_text() if rating_elem else ""
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    rating = float(rating_match.group(1)) if rating_match else None
                    
                    link_elem = await product.query_selector('h2 a')
                    product_url = await link_elem.get_attribute('href') if link_elem else ""
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.amazon.in{product_url}"
                    
                    image_elem = await product.query_selector('img')
                    image_url = await image_elem.get_attribute('src') if image_elem else None
                    
                    if price:
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
                            shipping_info="Free Shipping",
                            store_color="bg-orange-500"
                        ))
                        
                except Exception as e:
                    logger.error(f"Error extracting Amazon product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Amazon: {e}")
        finally:
            await page.close()
            
        return results

    async def scrape_flipkart(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Flipkart for products"""
        results = []
        page = await self.create_page()
        
        try:
            url = self.build_search_url('flipkart', filters)
            logger.info(f"Scraping Flipkart: {url}")
            
            await page.goto(url, wait_until='networkidle')
            await self.random_delay(2, 4)
            
            # Wait for products to load
            await page.wait_for_selector('[data-id]', timeout=10000)
            
            products = await page.query_selector_all('[data-id]')
            
            for i, product in enumerate(products[:6]):
                try:
                    title_elem = await product.query_selector('a[title]')
                    title = await title_elem.get_attribute('title') if title_elem else "Unknown Product"
                    
                    price_elem = await product.query_selector('div[class*="price"]')
                    price_text = await price_elem.inner_text() if price_elem else ""
                    price = self.extract_price(price_text)
                    
                    link_elem = await product.query_selector('a')
                    product_url = await link_elem.get_attribute('href') if link_elem else ""
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.flipkart.com{product_url}"
                    
                    image_elem = await product.query_selector('img')
                    image_url = await image_elem.get_attribute('src') if image_elem else None
                    
                    if price:
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
                            shipping_info="Free Shipping",
                            store_color="bg-blue-500"
                        ))
                        
                except Exception as e:
                    logger.error(f"Error extracting Flipkart product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Flipkart: {e}")
        finally:
            await page.close()
            
        return results

    async def scrape_ajio(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Ajio for products"""
        results = []
        page = await self.create_page()
        
        try:
            url = self.build_search_url('ajio', filters)
            logger.info(f"Scraping Ajio: {url}")
            
            await page.goto(url, wait_until='networkidle')
            await self.random_delay(2, 4)
            
            # Wait for products to load
            await page.wait_for_selector('.item', timeout=10000)
            
            products = await page.query_selector_all('.item')
            
            for i, product in enumerate(products[:6]):
                try:
                    title_elem = await product.query_selector('.nameCls')
                    title = await title_elem.inner_text() if title_elem else "Unknown Product"
                    
                    price_elem = await product.query_selector('.price')
                    price_text = await price_elem.inner_text() if price_elem else ""
                    price = self.extract_price(price_text)
                    
                    link_elem = await product.query_selector('a')
                    product_url = await link_elem.get_attribute('href') if link_elem else ""
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.ajio.com{product_url}"
                    
                    image_elem = await product.query_selector('img')
                    image_url = await image_elem.get_attribute('src') if image_elem else None
                    
                    if price:
                        results.append(ProductResult(
                            title=title,
                            price=price,
                            original_price=None,
                            discount_percentage=None,
                            rating=None,
                            review_count=None,
                            image_url=image_url,
                            product_url=product_url,
                            store_name="Ajio",
                            brand=None,
                            availability=True,
                            shipping_info="Free Shipping",
                            store_color="bg-indigo-500"
                        ))
                        
                except Exception as e:
                    logger.error(f"Error extracting Ajio product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Ajio: {e}")
        finally:
            await page.close()
            
        return results

    async def scrape_all_stores(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape all stores concurrently"""
        if not self.browser:
            await self.initialize_browser()
        
        # Create tasks for concurrent scraping
        tasks = [
            self.scrape_myntra(filters),
            self.scrape_amazon(filters),
            self.scrape_flipkart(filters),
            self.scrape_ajio(filters)
        ]
        
        # Run all scrapers concurrently
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all results
        all_results = []
        for results in results_list:
            if isinstance(results, list):
                all_results.extend(results)
            else:
                logger.error(f"Scraping error: {results}")
        
        # Sort by price (ascending)
        all_results.sort(key=lambda x: x.price)
        
        return all_results

    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()

# FastAPI setup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Fashion Price Comparison API")

# Add CORS middleware to allow frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
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

@app.post("/api/search")
async def search_products(filters: SearchFilters):
    try:
        scraper = FashionPriceScraper()
        
        # Convert Pydantic model to ProductFilter
        product_filter = ProductFilter(
            name=filters.name,
            brand=filters.brand,
            category=filters.category,
            color=filters.color,
            gender=filters.gender,
            max_price=filters.max_price
        )
        
        # Scrape all stores
        results = await scraper.scrape_all_stores(product_filter)
        
        # Convert results to JSON-serializable format
        serializable_results = []
        for result in results:
            result_dict = {
                "title": result.title,
                "price": result.price,
                "original_price": result.original_price,
                "discount_percentage": result.discount_percentage,
                "rating": result.rating,
                "review_count": result.review_count,
                "image_url": result.image_url,
                "product_url": result.product_url,
                "store_name": result.store_name,
                "brand": result.brand,
                "availability": result.availability,
                "shipping_info": result.shipping_info,
                "store_color": result.store_color
            }
            serializable_results.append(result_dict)
        
        await scraper.close()
        return serializable_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Fashion Price Comparison API is running"}

# Example usage
async def example_usage():
    scraper = FashionPriceScraper()
    
    try:
        # Create search filters
        filters = ProductFilter(
            name="floral dress",
            brand="Zara",
            color="blue",
            gender="women",
            category="dresses"
        )
        
        # Scrape all stores
        results = await scraper.scrape_all_stores(filters)
        
        # Print results
        print(f"\nFound {len(results)} products:")
        for i, product in enumerate(results, 1):
            print(f"\n{i}. {product.title}")
            print(f"   Store: {product.store_name}")
            print(f"   Price: ₹{product.price}")
            print(f"   URL: {product.product_url}")
            
    finally:
        await scraper.close()

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



# import asyncio
# import random
# import time
# from datetime import datetime
# from urllib.parse import quote_plus
# import re
# from dataclasses import dataclass
# from typing import List, Optional, Dict, Any
# from playwright.async_api import async_playwright, Browser, Page
# import logging

# from fastapi import HTTPException

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
#         self.stores = {
#             'myntra': {
#                 'base_url': 'https://www.myntra.com',
#                 'search_url': 'https://www.myntra.com/{category}?f=Gender%3A{gender}&q={query}',
#                 'color': 'bg-pink-500'
#             },
#             'amazon': {
#                 'base_url': 'https://www.amazon.in',
#                 'search_url': 'https://www.amazon.in/s?k={query}&rh=n%3A1571271031',  # Fashion category
#                 'color': 'bg-orange-500'
#             },
#             'flipkart': {
#                 'base_url': 'https://www.flipkart.com',
#                 'search_url': 'https://www.flipkart.com/search?q={query}&otracker=search&marketplace=FLIPKART',
#                 'color': 'bg-blue-500'
#             },
#             'ajio': {
#                 'base_url': 'https://www.ajio.com',
#                 'search_url': 'https://www.ajio.com/search/?text={query}',
#                 'color': 'bg-indigo-500'
#             }
#         }

#     async def initialize_browser(self):
#         """Initialize Playwright browser with anti-detection settings"""
#         playwright = await async_playwright().start()
        
#         self.browser = await playwright.chromium.launch(
#             headless=True,
#             args=[
#                 '--no-sandbox',
#                 '--disable-setuid-sandbox',
#                 '--disable-dev-shm-usage',
#                 '--disable-accelerated-2d-canvas',
#                 '--disable-gpu',
#                 '--window-size=1920,1080'
#             ]
#         )

#     async def create_page(self) -> Page:
#         """Create a new page with realistic settings"""
#         context = await self.browser.new_context(
#             viewport={'width': 1920, 'height': 1080},
#             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         )
        
#         page = await context.new_page()
        
#         # Add extra headers
#         await page.set_extra_http_headers({
#             'Accept-Language': 'en-US,en;q=0.9',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#         })
        
#         return page

#     async def random_delay(self, min_seconds=1, max_seconds=3):
#         """Add random delay to mimic human behavior"""
#         delay = random.uniform(min_seconds, max_seconds)
#         await asyncio.sleep(delay)

#     def build_search_url(self, store: str, filters: ProductFilter) -> str:
#         """Build search URL based on store and filters"""
#         store_config = self.stores[store]
#         query = quote_plus(f"{filters.name} {filters.brand or ''} {filters.color or ''}".strip())
        
#         if store == 'myntra':
#             category = filters.category or 'dresses'
#             gender = filters.gender or 'women'
#             return store_config['search_url'].format(
#                 category=category, 
#                 gender=gender, 
#                 query=query
#             )
#         else:
#             return store_config['search_url'].format(query=query)

#     def extract_price(self, price_text: str) -> Optional[float]:
#         """Extract numeric price from text"""
#         if not price_text:
#             return None
        
#         # Remove currency symbols and extract numbers
#         price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
#         if price_match:
#             return float(price_match.group())
#         return None

#     async def scrape_myntra(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Myntra for products"""
#         results = []
#         page = await self.create_page()
        
#         try:
#             url = self.build_search_url('myntra', filters)
#             logger.info(f"Scraping Myntra: {url}")
            
#             await page.goto(url, wait_until='networkidle')
#             await self.random_delay(2, 4)
            
#             # Wait for products to load
#             await page.wait_for_selector('.product-base', timeout=10000)
            
#             # Extract product information
#             products = await page.query_selector_all('.product-base')
            
#             for i, product in enumerate(products[:6]):  # Limit to first 6 products
#                 try:
#                     title_elem = await product.query_selector('.product-product')
#                     title = await title_elem.inner_text() if title_elem else "Unknown Product"
                    
#                     price_elem = await product.query_selector('.product-discountedPrice')
#                     price_text = await price_elem.inner_text() if price_elem else ""
#                     price = self.extract_price(price_text)
                    
#                     original_price_elem = await product.query_selector('.product-strike')
#                     original_price_text = await original_price_elem.inner_text() if original_price_elem else ""
#                     original_price = self.extract_price(original_price_text)
                    
#                     rating_elem = await product.query_selector('.product-ratingsContainer')
#                     rating_text = await rating_elem.inner_text() if rating_elem else ""
#                     rating = float(rating_text.split()[0]) if rating_text and rating_text.split() else None
                    
#                     link_elem = await product.query_selector('a')
#                     product_url = await link_elem.get_attribute('href') if link_elem else ""
#                     if product_url and not product_url.startswith('http'):
#                         product_url = f"https://www.myntra.com{product_url}"
                    
#                     image_elem = await product.query_selector('img')
#                     image_url = await image_elem.get_attribute('src') if image_elem else None
                    
#                     if price:
#                         discount_percentage = None
#                         if original_price and original_price > price:
#                             discount_percentage = int((original_price - price) / original_price * 100)
                        
#                         results.append(ProductResult(
#                             title=title,
#                             price=price,
#                             original_price=original_price,
#                             discount_percentage=discount_percentage,
#                             rating=rating,
#                             review_count=None,
#                             image_url=image_url,
#                             product_url=product_url,
#                             store_name="Myntra",
#                             brand=None,
#                             availability=True,
#                             shipping_info="Free Shipping",
#                             store_color="bg-pink-500"
#                         ))
                        
#                 except Exception as e:
#                     logger.error(f"Error extracting Myntra product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Myntra: {e}")
#         finally:
#             await page.close()
            
#         return results

#     async def scrape_amazon(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Amazon for products"""
#         results = []
#         page = await self.create_page()
        
#         try:
#             url = self.build_search_url('amazon', filters)
#             logger.info(f"Scraping Amazon: {url}")
            
#             await page.goto(url, wait_until='networkidle')
#             await self.random_delay(2, 4)
            
#             # Wait for products to load
#             await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=10000)
            
#             products = await page.query_selector_all('[data-component-type="s-search-result"]')
            
#             for i, product in enumerate(products[:6]):
#                 try:
#                     title_elem = await product.query_selector('h2 a span')
#                     title = await title_elem.inner_text() if title_elem else "Unknown Product"
                    
#                     price_elem = await product.query_selector('.a-price-whole')
#                     price_text = await price_elem.inner_text() if price_elem else ""
#                     price = self.extract_price(price_text)
                    
#                     rating_elem = await product.query_selector('.a-icon-alt')
#                     rating_text = await rating_elem.inner_text() if rating_elem else ""
#                     rating_match = re.search(r'(\d+\.?\d*)', rating_text)
#                     rating = float(rating_match.group(1)) if rating_match else None
                    
#                     link_elem = await product.query_selector('h2 a')
#                     product_url = await link_elem.get_attribute('href') if link_elem else ""
#                     if product_url and not product_url.startswith('http'):
#                         product_url = f"https://www.amazon.in{product_url}"
                    
#                     image_elem = await product.query_selector('img')
#                     image_url = await image_elem.get_attribute('src') if image_elem else None
                    
#                     if price:
#                         results.append(ProductResult(
#                             title=title,
#                             price=price,
#                             original_price=None,
#                             discount_percentage=None,
#                             rating=rating,
#                             review_count=None,
#                             image_url=image_url,
#                             product_url=product_url,
#                             store_name="Amazon",
#                             brand=None,
#                             availability=True,
#                             shipping_info="Free Shipping",
#                             store_color="bg-orange-500"
#                         ))
                        
#                 except Exception as e:
#                     logger.error(f"Error extracting Amazon product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Amazon: {e}")
#         finally:
#             await page.close()
            
#         return results

#     async def scrape_flipkart(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Flipkart for products"""
#         results = []
#         page = await self.create_page()
        
#         try:
#             url = self.build_search_url('flipkart', filters)
#             logger.info(f"Scraping Flipkart: {url}")
            
#             await page.goto(url, wait_until='networkidle')
#             await self.random_delay(2, 4)
            
#             # Wait for products to load
#             await page.wait_for_selector('[data-id]', timeout=10000)
            
#             products = await page.query_selector_all('[data-id]')
            
#             for i, product in enumerate(products[:6]):
#                 try:
#                     title_elem = await product.query_selector('a[title]')
#                     title = await title_elem.get_attribute('title') if title_elem else "Unknown Product"
                    
#                     price_elem = await product.query_selector('div[class*="price"]')
#                     price_text = await price_elem.inner_text() if price_elem else ""
#                     price = self.extract_price(price_text)
                    
#                     link_elem = await product.query_selector('a')
#                     product_url = await link_elem.get_attribute('href') if link_elem else ""
#                     if product_url and not product_url.startswith('http'):
#                         product_url = f"https://www.flipkart.com{product_url}"
                    
#                     image_elem = await product.query_selector('img')
#                     image_url = await image_elem.get_attribute('src') if image_elem else None
                    
#                     if price:
#                         results.append(ProductResult(
#                             title=title,
#                             price=price,
#                             original_price=None,
#                             discount_percentage=None,
#                             rating=None,
#                             review_count=None,
#                             image_url=image_url,
#                             product_url=product_url,
#                             store_name="Flipkart",
#                             brand=None,
#                             availability=True,
#                             shipping_info="Free Shipping",
#                             store_color="bg-blue-500"
#                         ))
                        
#                 except Exception as e:
#                     logger.error(f"Error extracting Flipkart product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Flipkart: {e}")
#         finally:
#             await page.close()
            
#         return results

#     async def scrape_ajio(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Ajio for products"""
#         results = []
#         page = await self.create_page()
        
#         try:
#             url = self.build_search_url('ajio', filters)
#             logger.info(f"Scraping Ajio: {url}")
            
#             await page.goto(url, wait_until='networkidle')
#             await self.random_delay(2, 4)
            
#             # Wait for products to load
#             await page.wait_for_selector('.item', timeout=10000)
            
#             products = await page.query_selector_all('.item')
            
#             for i, product in enumerate(products[:6]):
#                 try:
#                     title_elem = await product.query_selector('.nameCls')
#                     title = await title_elem.inner_text() if title_elem else "Unknown Product"
                    
#                     price_elem = await product.query_selector('.price')
#                     price_text = await price_elem.inner_text() if price_elem else ""
#                     price = self.extract_price(price_text)
                    
#                     link_elem = await product.query_selector('a')
#                     product_url = await link_elem.get_attribute('href') if link_elem else ""
#                     if product_url and not product_url.startswith('http'):
#                         product_url = f"https://www.ajio.com{product_url}"
                    
#                     image_elem = await product.query_selector('img')
#                     image_url = await image_elem.get_attribute('src') if image_elem else None
                    
#                     if price:
#                         results.append(ProductResult(
#                             title=title,
#                             price=price,
#                             original_price=None,
#                             discount_percentage=None,
#                             rating=None,
#                             review_count=None,
#                             image_url=image_url,
#                             product_url=product_url,
#                             store_name="Ajio",
#                             brand=None,
#                             availability=True,
#                             shipping_info="Free Shipping",
#                             store_color="bg-indigo-500"
#                         ))
                        
#                 except Exception as e:
#                     logger.error(f"Error extracting Ajio product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Ajio: {e}")
#         finally:
#             await page.close()
            
#         return results

#     async def scrape_all_stores(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape all stores concurrently"""
#         if not self.browser:
#             await self.initialize_browser()
        
#         # Create tasks for concurrent scraping
#         tasks = [
#             self.scrape_myntra(filters),
#             self.scrape_amazon(filters),
#             self.scrape_flipkart(filters),
#             self.scrape_ajio(filters)
#         ]
        
#         # Run all scrapers concurrently
#         results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
#         # Combine all results
#         all_results = []
#         for results in results_list:
#             if isinstance(results, list):
#                 all_results.extend(results)
#             else:
#                 logger.error(f"Scraping error: {results}")
        
#         # Sort by price (ascending)
#         all_results.sort(key=lambda x: x.price)
        
#         return all_results

#     async def close(self):
#         """Close the browser"""
#         if self.browser:
#             await self.browser.close()

# # ... (all your existing imports and classes remain the same)

# # Example usage
# async def example_usage():
#     scraper = FashionPriceScraper()
    
#     try:
#         # Create search filters
#         filters = ProductFilter(
#             name="floral dress",
#             brand="Zara",
#             color="blue",
#             gender="women",
#             category="dresses"
#         )
        
#         # Scrape all stores
#         results = await scraper.scrape_all_stores(filters)
        
#         # Print results
#         print(f"\nFound {len(results)} products:")
#         for i, product in enumerate(results, 1):
#             print(f"\n{i}. {product.title}")
#             print(f"   Store: {product.store_name}")
#             print(f"   Price: ₹{product.price}")
#             print(f"   URL: {product.product_url}")
            
#     finally:
#         await scraper.close()

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# app = FastAPI(title="Fashion Price Comparison API")

# # Add CORS middleware to allow frontend-backend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Added both localhost variants
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
#         scraper = FashionPriceScraper()
        
#         # Convert Pydantic model to ProductFilter
#         product_filter = ProductFilter(
#             name=filters.name,
#             brand=filters.brand,
#             category=filters.category,
#             color=filters.color,
#             gender=filters.gender,
#             max_price=filters.max_price
#         )
        
#         # Scrape all stores
#         results = await scraper.scrape_all_stores(product_filter)
        
#         # Convert results to JSON-serializable format
#         serializable_results = []
#         for result in results:
#             result_dict = {
#                 "title": result.title,
#                 "price": result.price,
#                 "original_price": result.original_price,
#                 "discount_percentage": result.discount_percentage,
#                 "rating": result.rating,
#                 "review_count": result.review_count,
#                 "image_url": result.image_url,
#                 "product_url": result.product_url,
#                 "store_name": result.store_name,
#                 "brand": result.brand,
#                 "availability": result.availability,
#                 "shipping_info": result.shipping_info,
#                 "store_color": result.store_color
#             }
#             serializable_results.append(result_dict)
        
#         await scraper.close()
#         return serializable_results
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/")
# async def root():
#     return {"message": "Fashion Price Comparison API is running"}

# # Main entry point
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

