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
                'search_url': 'https://www.amazon.in/s?k={query}&rh=n%3A1571271031',
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
                '--window-size=1920,1080',
                '--disable-blink-features=AutomationControlled'
            ]
        )

    async def create_page(self) -> Page:
        """Create a new page with realistic settings"""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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
        query_parts = [filters.name]
        if filters.brand:
            query_parts.append(filters.brand)
        if filters.color:
            query_parts.append(filters.color)
        
        query = quote_plus(" ".join(query_parts))
        
        if store == 'myntra':
            category = filters.category or 'clothing'
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
        
        # Clean the price text and extract numbers
        cleaned_text = re.sub(r'[^\d,.]', '', price_text)
        price_match = re.search(r'[\d,]+\.?\d*', cleaned_text.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                return None
        return None

    async def scrape_myntra(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Myntra for products"""
        results = []
        page = await self.create_page()
        
        try:
            url = self.build_search_url('myntra', filters)
            logger.info(f"Scraping Myntra: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await self.random_delay(3, 5)
            
            # Updated selectors for Myntra
            try:
                await page.wait_for_selector('li.product-base', timeout=15000)
            except:
                logger.warning("Myntra products not found with primary selector")
                return results
            
            products = await page.query_selector_all('li.product-base')
            logger.info(f"Found {len(products)} Myntra products")
            
            for i, product in enumerate(products[:8]):
                try:
                    # Title extraction - multiple selectors
                    title = "Unknown Product"
                    title_selectors = [
                        '.product-brand, .product-product',
                        'h4.product-product',
                        '.product-productMetaInfo h4'
                    ]
                    
                    for selector in title_selectors:
                        title_elem = await product.query_selector(selector)
                        if title_elem:
                            title_text = await title_elem.inner_text()
                            if title_text.strip():
                                title = title_text.strip()
                                break
                    
                    # Price extraction
                    price = None
                    price_selectors = [
                        '.product-discountedPrice',
                        'span.product-discountedPrice',
                        '.product-price .product-discountedPrice'
                    ]
                    
                    for selector in price_selectors:
                        price_elem = await product.query_selector(selector)
                        if price_elem:
                            price_text = await price_elem.inner_text()
                            price = self.extract_price(price_text)
                            if price:
                                break
                    
                    # Skip if no price found
                    if not price:
                        continue
                    
                    # Original price
                    original_price = None
                    original_price_elem = await product.query_selector('.product-strike, span.product-strike')
                    if original_price_elem:
                        original_price_text = await original_price_elem.inner_text()
                        original_price = self.extract_price(original_price_text)
                    
                    # Rating
                    rating = None
                    rating_elem = await product.query_selector('.product-ratingsContainer')
                    if rating_elem:
                        rating_text = await rating_elem.inner_text()
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    
                    # Product URL
                    product_url = ""
                    link_elem = await product.query_selector('a')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.myntra.com{href}" if not href.startswith('http') else href
                    
                    # Image URL
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
                    # Calculate discount
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
            
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await self.random_delay(3, 5)
            
            # Updated selectors for Amazon
            try:
                await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=15000)
            except:
                logger.warning("Amazon products not found")
                return results
            
            products = await page.query_selector_all('[data-component-type="s-search-result"]')
            logger.info(f"Found {len(products)} Amazon products")
            
            for i, product in enumerate(products[:8]):
                try:
                    # Title extraction with multiple selectors
                    title = "Unknown Product"
                    title_selectors = [
                        'h2 a span, h2 span',
                        '.a-size-mini .a-color-base',
                        '.a-size-base-plus',
                        'h2 .a-color-base'
                    ]
                    
                    for selector in title_selectors:
                        title_elem = await product.query_selector(selector)
                        if title_elem:
                            title_text = await title_elem.inner_text()
                            if title_text.strip() and len(title_text.strip()) > 3:
                                title = title_text.strip()
                                break
                    
                    # Price extraction with multiple selectors
                    price = None
                    price_selectors = [
                        '.a-price-whole',
                        '.a-price .a-offscreen',
                        '.a-price-range .a-price .a-offscreen'
                    ]
                    
                    for selector in price_selectors:
                        price_elem = await product.query_selector(selector)
                        if price_elem:
                            price_text = await price_elem.inner_text()
                            price = self.extract_price(price_text)
                            if price:
                                break
                    
                    # Skip if no valid price
                    if not price or price < 50:  # Filter out very low prices which might be wrong
                        continue
                    
                    # Rating
                    rating = None
                    rating_elem = await product.query_selector('.a-icon-alt')
                    if rating_elem:
                        rating_text = await rating_elem.inner_text()
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    
                    # Product URL
                    product_url = ""
                    link_elem = await product.query_selector('h2 a')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.amazon.in{href}" if not href.startswith('http') else href
                    
                    # Image URL
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
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
            
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await self.random_delay(3, 5)
            
            # Updated selectors for Flipkart
            try:
                await page.wait_for_selector('div[data-id], ._1AtVbE, ._2kHMtA', timeout=15000)
            except:
                logger.warning("Flipkart products not found")
                return results
            
            # Try multiple selectors for products
            products = []
            product_selectors = ['div[data-id]', '._1AtVbE', '._2kHMtA', '._13oc-S']
            for selector in product_selectors:
                products = await page.query_selector_all(selector)
                if products:
                    break
            
            logger.info(f"Found {len(products)} Flipkart products")
            
            for i, product in enumerate(products[:8]):
                try:
                    # Title extraction
                    title = "Unknown Product"
                    title_selectors = [
                        '._4rR01T',
                        'a[title]',
                        '.s1Q9rs',
                        '._2WkVRV'
                    ]
                    
                    for selector in title_selectors:
                        title_elem = await product.query_selector(selector)
                        if title_elem:
                            if selector == 'a[title]':
                                title_text = await title_elem.get_attribute('title')
                            else:
                                title_text = await title_elem.inner_text()
                            if title_text and title_text.strip():
                                title = title_text.strip()
                                break
                    
                    # Price extraction
                    price = None
                    price_selectors = [
                        '._30jeq3',
                        '._1_WHN1',
                        '.Nx9bqj',
                        '._30jeq3._16Jk6d'
                    ]
                    
                    for selector in price_selectors:
                        price_elem = await product.query_selector(selector)
                        if price_elem:
                            price_text = await price_elem.inner_text()
                            price = self.extract_price(price_text)
                            if price:
                                break
                    
                    # Skip if no price
                    if not price:
                        continue
                    
                    # Product URL
                    product_url = ""
                    link_elem = await product.query_selector('a')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.flipkart.com{href}" if not href.startswith('http') else href
                    
                    # Image URL
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
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
            
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await self.random_delay(3, 5)
            
            # Updated selectors for Ajio
            try:
                await page.wait_for_selector('.item, .rilrtl-products-list__item', timeout=15000)
            except:
                logger.warning("Ajio products not found")
                return results
            
            products = await page.query_selector_all('.item, .rilrtl-products-list__item')
            logger.info(f"Found {len(products)} Ajio products")
            
            for i, product in enumerate(products[:8]):
                try:
                    # Title extraction
                    title = "Unknown Product"
                    title_selectors = [
                        '.nameCls',
                        '.brand',
                        '.rilrtl-products-list__item-name'
                    ]
                    
                    for selector in title_selectors:
                        title_elem = await product.query_selector(selector)
                        if title_elem:
                            title_text = await title_elem.inner_text()
                            if title_text.strip():
                                title = title_text.strip()
                                break
                    
                    # Price extraction
                    price = None
                    price_selectors = [
                        '.price',
                        '.rilrtl-products-list__item-price',
                        '.price-new'
                    ]
                    
                    for selector in price_selectors:
                        price_elem = await product.query_selector(selector)
                        if price_elem:
                            price_text = await price_elem.inner_text()
                            price = self.extract_price(price_text)
                            if price:
                                break
                    
                    # Skip if no price
                    if not price:
                        continue
                    
                    # Product URL
                    product_url = ""
                    link_elem = await product.query_selector('a')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.ajio.com{href}" if not href.startswith('http') else href
                    
                    # Image URL
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
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
        for i, results in enumerate(results_list):
            store_names = ['Myntra', 'Amazon', 'Flipkart', 'Ajio']
            if isinstance(results, list):
                logger.info(f"Got {len(results)} results from {store_names[i]}")
                all_results.extend(results)
            else:
                logger.error(f"Scraping error for {store_names[i]}: {results}")
        
        # Filter by max price if specified
        if filters.max_price:
            all_results = [r for r in all_results if r.price <= filters.max_price]
        
        # Sort by price (ascending)
        all_results.sort(key=lambda x: x.price)
        
        logger.info(f"Total products found: {len(all_results)}")
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
        logger.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Fashion Price Comparison API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)