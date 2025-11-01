

# import asyncio
# import random
# import re
# from datetime import datetime
# from urllib.parse import quote_plus
# from dataclasses import dataclass, asdict
# from typing import List, Optional
# from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
# import logging

# # Import AI module
# from ai_model import get_analyzer, ImageAnalysisResult

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
#             },
#             'ajio': {
#                 'base_url': 'https://www.ajio.com',
#                 'color': 'bg-yellow-600'
#             },
#             'meesho': {
#                 'base_url': 'https://www.meesho.com',
#                 'color': 'bg-purple-600'
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
#                     '--disable-features=IsolateOrigins,site-per-process',
#                     '--disable-site-isolation-trials',
#                     '--disable-features=BlockInsecurePrivateNetworkRequests'
#                 ]
#             )
#             logger.info("Browser initialized successfully")

#     async def create_page(self, extra_wait: bool = False) -> Page:
#         """Create a new page with realistic settings"""
#         context = await self.browser.new_context(
#             viewport={'width': 1920, 'height': 1080},
#             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
#             locale='en-IN',
#             timezone_id='Asia/Kolkata',
#             java_script_enabled=True,
#             ignore_https_errors=True
#         )
        
#         page = await context.new_page()
        
#         await page.set_extra_http_headers({
#             'Accept-Language': 'en-IN,en-US;q=0.9,en;q=0.8',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#             'Sec-Fetch-Dest': 'document',
#             'Sec-Fetch-Mode': 'navigate',
#             'Sec-Fetch-Site': 'none',
#             'Sec-Fetch-User': '?1',
#             'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
#             'Sec-Ch-Ua-Mobile': '?0',
#             'Sec-Ch-Ua-Platform': '"Windows"',
#             'Cache-Control': 'max-age=0'
#         })
        
#         # Enhanced stealth script
#         await page.add_init_script("""
#             // Remove webdriver property
#             Object.defineProperty(navigator, 'webdriver', {
#                 get: () => undefined
#             });
            
#             // Mock plugins
#             Object.defineProperty(navigator, 'plugins', {
#                 get: () => [1, 2, 3, 4, 5]
#             });
            
#             // Mock languages
#             Object.defineProperty(navigator, 'languages', {
#                 get: () => ['en-US', 'en', 'en-IN']
#             });
            
#             // Add chrome object
#             window.chrome = {
#                 runtime: {},
#                 loadTimes: function() {},
#                 csi: function() {},
#                 app: {}
#             };
            
#             // Mock permissions
#             const originalQuery = window.navigator.permissions.query;
#             window.navigator.permissions.query = (parameters) => (
#                 parameters.name === 'notifications' ?
#                     Promise.resolve({ state: Notification.permission }) :
#                     originalQuery(parameters)
#             );
            
#             // Mock battery
#             Object.defineProperty(navigator, 'getBattery', {
#                 value: () => Promise.resolve({
#                     charging: true,
#                     chargingTime: 0,
#                     dischargingTime: Infinity,
#                     level: 1.0
#                 })
#             });
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
            
#             # Use general search URL - more reliable
#             url = f"https://www.myntra.com/{quote_plus(query)}"
#             logger.info(f"Scraping Myntra: {url}")
            
#             # Try with longer timeout and load strategy
#             try:
#                 await page.goto(url, wait_until='load', timeout=60000)
#             except Exception as e:
#                 logger.warning(f"Myntra primary URL failed: {e}, trying search")
#                 url = f"https://www.myntra.com/{quote_plus(query)}"
#                 try:
#                     await page.goto(url, timeout=60000)
#                 except:
#                     logger.error("Myntra: All URL attempts failed")
#                     return results
            
#             await self.random_delay(4, 6)
            
#             # Scroll to trigger lazy loading
#             for i in range(3):
#                 await page.evaluate(f'window.scrollTo(0, {(i+1)*800})')
#                 await asyncio.sleep(1.5)
            
#             # Wait for products
#             try:
#                 await page.wait_for_selector('li.product-base, .product-productMetaInfo', timeout=10000)
#             except PlaywrightTimeout:
#                 logger.warning("Myntra: Products not loaded")
#                 return results
            
#             products = await page.query_selector_all('li.product-base')
#             logger.info(f"Found {len(products)} Myntra product containers")
            
#             for i, product in enumerate(products[:24]):
#                 try:
#                     title = None
#                     title_selectors = ['h3.product-brand', 'h4.product-product', '.product-brand', '.product-product']
                    
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
                    
#                     price = None
#                     price_selectors = ['span.product-discountedPrice', '.product-discountedPrice', 'span[class*="discounted"]']
                    
#                     for selector in price_selectors:
#                         elem = await product.query_selector(selector)
#                         if elem:
#                             price_text = await elem.inner_text()
#                             price = self.extract_price(price_text)
#                             if price:
#                                 break
                    
#                     if not price:
#                         continue
                    
#                     original_price = None
#                     original_elem = await product.query_selector('span.product-strike, .product-strike')
#                     if original_elem:
#                         original_text = await original_elem.inner_text()
#                         original_price = self.extract_price(original_text)
                    
#                     discount_percentage = None
#                     if original_price and original_price > price:
#                         discount_percentage = int((original_price - price) / original_price * 100)
                    
#                     rating = None
#                     rating_elem = await product.query_selector('.product-ratingsContainer')
#                     if rating_elem:
#                         rating_text = await rating_elem.inner_text()
#                         match = re.search(r'(\d+\.?\d*)', rating_text)
#                         if match:
#                             rating = float(match.group(1))
                    
#                     product_url = ""
#                     link_elem = await product.query_selector('a')
#                     if link_elem:
#                         href = await link_elem.get_attribute('href')
#                         if href:
#                             product_url = f"https://www.myntra.com{href}" if not href.startswith('http') else href
                    
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
            
#             await page.goto(url, wait_until='domcontentloaded', timeout=45000)
#             await self.random_delay(3, 5)
            
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
            
#             for i, product in enumerate(products[:24]):
#                 try:
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
                    
#                     rating = None
#                     rating_elem = await product.query_selector('.a-icon-alt')
#                     if rating_elem:
#                         rating_text = await rating_elem.inner_text()
#                         match = re.search(r'(\d+\.?\d*)', rating_text)
#                         if match:
#                             rating = float(match.group(1))
                    
#                     product_url = ""
#                     link_elem = await product.query_selector('h2 a, a.a-link-normal')
#                     if link_elem:
#                         href = await link_elem.get_attribute('href')
#                         if href:
#                             product_url = f"https://www.amazon.in{href}" if not href.startswith('http') else href
                    
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
            
#             # Try multiple times with different strategies
#             loaded = False
#             for attempt in range(2):
#                 try:
#                     await page.goto(url, wait_until='load', timeout=60000)
#                     loaded = True
#                     break
#                 except Exception as e:
#                     if attempt == 0:
#                         logger.warning(f"Flipkart attempt {attempt+1} failed: {e}, retrying...")
#                         await asyncio.sleep(3)
#                     else:
#                         logger.error(f"Flipkart: All attempts failed")
#                         return results
            
#             if not loaded:
#                 return results
            
#             await self.random_delay(3, 5)
            
#             try:
#                 close_btn = await page.query_selector('button._2KpZ6l, button._2AkmmA')
#                 if close_btn:
#                     await close_btn.click()
#                     await asyncio.sleep(1)
#             except:
#                 pass
            
#             await page.evaluate('window.scrollTo(0, 800)')
#             await asyncio.sleep(1)
#             await page.evaluate('window.scrollTo(0, 1600)')
#             await asyncio.sleep(1)
#             await page.evaluate('window.scrollTo(0, 2400)')
#             await asyncio.sleep(1)
            
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
            
#             for i, product in enumerate(products[:30]):
#                 try:
#                     title = None
#                     title_selectors = ['a[class*="IRpwTa"]', 'a[class*="wjcEIp"]', '._4rR01T', '.s1Q9rs', 'a[title]', 'div[class*="KzDlHZ"]']
                    
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
                    
#                     price = None
#                     price_selectors = ['div[class*="Nx9bqj"]', 'div[class*="_30jeq3"]', '._30jeq3', '._1_WHN1', 'div[class*="_25b18c"]']
                    
#                     for selector in price_selectors:
#                         elem = await product.query_selector(selector)
#                         if elem:
#                             price_text = await elem.inner_text()
#                             price = self.extract_price(price_text)
#                             if price:
#                                 break
                    
#                     if not price:
#                         continue
                    
#                     product_url = ""
#                     link_elem = await product.query_selector('a')
#                     if link_elem:
#                         href = await link_elem.get_attribute('href')
#                         if href:
#                             product_url = f"https://www.flipkart.com{href}" if not href.startswith('http') else href
                    
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

#     async def scrape_ajio(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Ajio for products"""
#         results = []
#         page = None
        
#         try:
#             page = await self.create_page()
            
#             query_parts = [filters.name]
#             if filters.color:
#                 query_parts.append(filters.color)
#             query = " ".join(query_parts)
            
#             url = f"https://www.ajio.com/search/?text={quote_plus(query)}"
#             logger.info(f"Scraping Ajio: {url}")
            
#             # Try loading with retries
#             loaded = False
#             for attempt in range(2):
#                 try:
#                     await page.goto(url, wait_until='load', timeout=60000)
#                     loaded = True
#                     break
#                 except Exception as e:
#                     if attempt == 0:
#                         logger.warning(f"Ajio attempt {attempt+1} failed: {e}, retrying...")
#                         await asyncio.sleep(3)
#                     else:
#                         logger.error(f"Ajio: All attempts failed")
#                         return results
            
#             if not loaded:
#                 return results
            
#             await self.random_delay(3, 5)
            
#             # Scroll to load products
#             for i in range(3):
#                 await page.evaluate(f'window.scrollTo(0, {(i+1)*1000})')
#                 await asyncio.sleep(1.5)
            
#             # Ajio product selectors
#             products = []
#             selectors = ['.item', '.rilrtl-products-list__item', 'div[class*="product"]']
            
#             for selector in selectors:
#                 products = await page.query_selector_all(selector)
#                 if products and len(products) > 5:
#                     logger.info(f"Ajio: Using selector '{selector}', found {len(products)} containers")
#                     break
            
#             if not products:
#                 logger.warning("Ajio: No product containers found")
#                 return results
            
#             for i, product in enumerate(products[:24]):
#                 try:
#                     # Title
#                     title = None
#                     title_selectors = [
#                         '.nameCls',
#                         '.item-title',
#                         'div[class*="name"]',
#                         'strong'
#                     ]
                    
#                     for selector in title_selectors:
#                         elem = await product.query_selector(selector)
#                         if elem:
#                             title = await elem.inner_text()
#                             if title and title.strip() and len(title.strip()) > 3:
#                                 title = title.strip()
#                                 break
                    
#                     if not title or len(title) < 3:
#                         continue
                    
#                     # Price
#                     price = None
#                     price_selectors = [
#                         '.price',
#                         'span[class*="price"]',
#                         '.priceText',
#                         'strong[class*="price"]'
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
                    
#                     # Original price for discount
#                     original_price = None
#                     original_elem = await product.query_selector('.orgPrice, del, .price-original')
#                     if original_elem:
#                         original_text = await original_elem.inner_text()
#                         original_price = self.extract_price(original_text)
                    
#                     # Discount
#                     discount_percentage = None
#                     if original_price and original_price > price:
#                         discount_percentage = int((original_price - price) / original_price * 100)
                    
#                     # URL
#                     product_url = ""
#                     link_elem = await product.query_selector('a')
#                     if link_elem:
#                         href = await link_elem.get_attribute('href')
#                         if href:
#                             product_url = f"https://www.ajio.com{href}" if not href.startswith('http') else href
                    
#                     # Image
#                     image_url = None
#                     img_elem = await product.query_selector('img')
#                     if img_elem:
#                         image_url = await img_elem.get_attribute('src')
                    
#                     logger.info(f"Ajio: {title[:40]}... - ₹{price}")
                    
#                     results.append(ProductResult(
#                         title=title,
#                         price=price,
#                         original_price=original_price,
#                         discount_percentage=discount_percentage,
#                         rating=None,
#                         review_count=None,
#                         image_url=image_url,
#                         product_url=product_url,
#                         store_name="Ajio",
#                         brand=None,
#                         availability=True,
#                         shipping_info="Check Delivery",
#                         store_color="bg-yellow-600"
#                     ))
                    
#                 except Exception as e:
#                     logger.debug(f"Error extracting Ajio product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Ajio: {e}")
#         finally:
#             if page:
#                 await page.close()
        
#         logger.info(f"Ajio: Returning {len(results)} products")
#         return results

#     async def scrape_meesho(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape Meesho for products"""
#         results = []
#         page = None
        
#         try:
#             page = await self.create_page()
            
#             query_parts = [filters.name]
#             if filters.color:
#                 query_parts.append(filters.color)
#             query = " ".join(query_parts)
            
#             url = f"https://www.meesho.com/search?q={quote_plus(query)}"
#             logger.info(f"Scraping Meesho: {url}")
            
#             # Try loading
#             loaded = False
#             for attempt in range(2):
#                 try:
#                     await page.goto(url, wait_until='load', timeout=60000)
#                     loaded = True
#                     break
#                 except Exception as e:
#                     if attempt == 0:
#                         logger.warning(f"Meesho attempt {attempt+1} failed: {e}, retrying...")
#                         await asyncio.sleep(3)
#                     else:
#                         logger.error(f"Meesho: All attempts failed")
#                         return results
            
#             if not loaded:
#                 return results
            
#             await self.random_delay(4, 6)
            
#             # Meesho loads products dynamically - need more scrolling
#             for i in range(4):
#                 await page.evaluate(f'window.scrollTo(0, {(i+1)*1000})')
#                 await asyncio.sleep(2)
            
#             # Meesho product selectors
#             products = []
#             selectors = [
#                 'div[data-testid="product-card"]',
#                 'div[class*="ProductCard"]',
#                 'div[class*="product-"]',
#                 'a[href*="/product/"]'
#             ]
            
#             for selector in selectors:
#                 products = await page.query_selector_all(selector)
#                 if products and len(products) > 3:
#                     logger.info(f"Meesho: Using selector '{selector}', found {len(products)} containers")
#                     break
            
#             if not products:
#                 logger.warning("Meesho: No product containers found")
#                 return results
            
#             for i, product in enumerate(products[:24]):
#                 try:
#                     # Title
#                     title = None
#                     title_selectors = [
#                         'p[class*="ProductCard"]',
#                         'p[class*="title"]',
#                         'div[class*="name"]',
#                         'p'
#                     ]
                    
#                     for selector in title_selectors:
#                         elem = await product.query_selector(selector)
#                         if elem:
#                             title = await elem.inner_text()
#                             if title and title.strip() and len(title.strip()) > 5:
#                                 title = title.strip()
#                                 break
                    
#                     if not title or len(title) < 5:
#                         continue
                    
#                     # Price - Meesho shows price prominently
#                     price = None
#                     price_selectors = [
#                         'h5[class*="price"]',
#                         'span[class*="price"]',
#                         'p[class*="price"]',
#                         'h5'
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
                    
#                     # Rating
#                     rating = None
#                     rating_elem = await product.query_selector('[class*="rating"], span[class*="Rating"]')
#                     if rating_elem:
#                         rating_text = await rating_elem.inner_text()
#                         match = re.search(r'(\d+\.?\d*)', rating_text)
#                         if match:
#                             rating = float(match.group(1))
                    
#                     # URL
#                     product_url = ""
#                     link_elem = await product.query_selector('a') if await product.query_selector('a') else product
#                     if link_elem:
#                         href = await link_elem.get_attribute('href')
#                         if href:
#                             product_url = f"https://www.meesho.com{href}" if not href.startswith('http') else href
                    
#                     # Image
#                     image_url = None
#                     img_elem = await product.query_selector('img')
#                     if img_elem:
#                         image_url = await img_elem.get_attribute('src')
                    
#                     logger.info(f"Meesho: {title[:40]}... - ₹{price}")
                    
#                     results.append(ProductResult(
#                         title=title,
#                         price=price,
#                         original_price=None,
#                         discount_percentage=None,
#                         rating=rating,
#                         review_count=None,
#                         image_url=image_url,
#                         product_url=product_url,
#                         store_name="Meesho",
#                         brand=None,
#                         availability=True,
#                         shipping_info="Free Delivery",
#                         store_color="bg-purple-600"
#                     ))
                    
#                 except Exception as e:
#                     logger.debug(f"Error extracting Meesho product {i}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"Error scraping Meesho: {e}")
#         finally:
#             if page:
#                 await page.close()
        
#         logger.info(f"Meesho: Returning {len(results)} products")
#         return results

#     async def scrape_all_stores(self, filters: ProductFilter) -> List[ProductResult]:
#         """Scrape all stores concurrently"""
#         await self.initialize_browser()
        
#         tasks = [
#             self.scrape_myntra(filters),
#             self.scrape_amazon(filters),
#             self.scrape_flipkart(filters),
#             self.scrape_ajio(filters),
#             self.scrape_meesho(filters),
#         ]
        
#         results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
#         all_results = []
#         store_names = ['Myntra', 'Amazon', 'Flipkart', 'Ajio', 'Meesho']
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
# from fastapi import FastAPI, HTTPException, UploadFile, File, Form
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# app = FastAPI(title="Fashion Price Comparison API with AI")

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

# @app.post("/api/analyze-image")
# async def analyze_image(file: UploadFile = File(...)):
#     """Analyze uploaded fashion image using AI"""
#     try:
#         logger.info(f"Received image: {file.filename}")
        
#         # Read image bytes
#         image_bytes = await file.read()
        
#         # Get analyzer instance
#         analyzer = get_analyzer()
        
#         # Analyze image
#         result = analyzer.analyze_image(image_bytes)
        
#         logger.info(f"Analysis result: {result.description}")
        
#         return {
#             "success": True,
#             "analysis": {
#                 "category": result.category,
#                 "color": result.color_name,
#                 "dominant_colors": result.dominant_colors,
#                 "pattern": result.pattern,
#                 "style": result.style,
#                 "confidence": result.confidence,
#                 "description": result.description
#             }
#         }
        
#     except Exception as e:
#         logger.error(f"Image analysis error: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

# @app.post("/api/search-by-image")
# async def search_by_image(
#     file: UploadFile = File(...),
#     brand: Optional[str] = Form(None),
#     max_price: Optional[float] = Form(None)
# ):
#     """Analyze image and search for similar products"""
#     try:
#         logger.info(f"Image search request: {file.filename}")
        
#         # Read and analyze image
#         image_bytes = await file.read()
#         analyzer = get_analyzer()
#         analysis = analyzer.analyze_image(image_bytes)
        
#         logger.info(f"AI Analysis: {analysis.description}")
        
#         # Create search filter from AI analysis
#         product_filter = ProductFilter(
#             name=analysis.description,
#             brand=brand,
#             category=analysis.category,
#             color=analysis.color_name,
#             max_price=max_price,
#             gender='women'  # Default, could be enhanced with AI
#         )
        
#         # Search across stores
#         scraper = FashionPriceScraper()
#         results = await scraper.scrape_all_stores(product_filter)
#         serializable_results = [asdict(result) for result in results]
        
#         await scraper.close()
        
#         logger.info(f"Found {len(serializable_results)} products")
        
#         return {
#             "success": True,
#             "ai_analysis": {
#                 "category": analysis.category,
#                 "color": analysis.color_name,
#                 "pattern": analysis.pattern,
#                 "description": analysis.description,
#                 "confidence": analysis.confidence
#             },
#             "products": serializable_results
#         }
        
#     except Exception as e:
#         logger.error(f"Image search error: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

# @app.post("/api/search")
# async def search_products(filters: SearchFilters):
#     """Traditional text-based search"""
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
#         "message": "Fashion Price Comparison API with AI",
#         "version": "3.0",
#         "status": "active",
#         "features": ["AI Image Analysis", "Price Comparison", "Multi-store Scraping"],
#         "stores": ["Myntra", "Amazon", "Flipkart", "Ajio", "Meesho"]
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
            },
            'ajio': {
                'base_url': 'https://www.ajio.com',
                'color': 'bg-yellow-600'
            },
            'meesho': {
                'base_url': 'https://www.meesho.com',
                'color': 'bg-purple-600'
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
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-features=BlockInsecurePrivateNetworkRequests'
                ]
            )
            logger.info("Browser initialized successfully")

    async def create_page(self, extra_wait: bool = False) -> Page:
        """Create a new page with realistic settings"""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='en-IN',
            timezone_id='Asia/Kolkata',
            java_script_enabled=True,
            ignore_https_errors=True
        )
        
        page = await context.new_page()
        
        await page.set_extra_http_headers({
            'Accept-Language': 'en-IN,en-US;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'max-age=0'
        })
        
        # Enhanced stealth script
        await page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'en-IN']
            });
            
            // Add chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock battery
            Object.defineProperty(navigator, 'getBattery', {
                value: () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1.0
                })
            });
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
            
            # Use general search URL - more reliable
            url = f"https://www.myntra.com/{quote_plus(query)}"
            logger.info(f"Scraping Myntra: {url}")
            
            # Try with longer timeout and load strategy
            try:
                await page.goto(url, wait_until='load', timeout=60000)
            except Exception as e:
                logger.warning(f"Myntra primary URL failed: {e}, trying search")
                url = f"https://www.myntra.com/{quote_plus(query)}"
                try:
                    await page.goto(url, timeout=60000)
                except:
                    logger.error("Myntra: All URL attempts failed")
                    return results
            
            await self.random_delay(4, 6)
            
            # Scroll to trigger lazy loading
            for i in range(3):
                await page.evaluate(f'window.scrollTo(0, {(i+1)*800})')
                await asyncio.sleep(1.5)
            
            # Wait for products
            try:
                await page.wait_for_selector('li.product-base, .product-productMetaInfo', timeout=10000)
            except PlaywrightTimeout:
                logger.warning("Myntra: Products not loaded")
                return results
            
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
            
            # Try multiple times with different strategies
            loaded = False
            for attempt in range(2):
                try:
                    await page.goto(url, wait_until='load', timeout=60000)
                    loaded = True
                    break
                except Exception as e:
                    if attempt == 0:
                        logger.warning(f"Flipkart attempt {attempt+1} failed: {e}, retrying...")
                        await asyncio.sleep(3)
                    else:
                        logger.error(f"Flipkart: All attempts failed")
                        return results
            
            if not loaded:
                return results
            
            await self.random_delay(3, 5)
            
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

    async def scrape_ajio(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Ajio for products"""
        results = []
        page = None
        
        try:
            page = await self.create_page()
            
            query_parts = [filters.name]
            if filters.color:
                query_parts.append(filters.color)
            query = " ".join(query_parts)
            
            url = f"https://www.ajio.com/search/?text={quote_plus(query)}"
            logger.info(f"Scraping Ajio: {url}")
            
            # Try loading with retries
            loaded = False
            for attempt in range(2):
                try:
                    await page.goto(url, wait_until='load', timeout=60000)
                    loaded = True
                    break
                except Exception as e:
                    if attempt == 0:
                        logger.warning(f"Ajio attempt {attempt+1} failed: {e}, retrying...")
                        await asyncio.sleep(3)
                    else:
                        logger.error(f"Ajio: All attempts failed")
                        return results
            
            if not loaded:
                return results
            
            await self.random_delay(3, 5)
            
            # Scroll to load products
            for i in range(3):
                await page.evaluate(f'window.scrollTo(0, {(i+1)*1000})')
                await asyncio.sleep(1.5)
            
            # Ajio product selectors
            products = []
            selectors = ['.item', '.rilrtl-products-list__item', 'div[class*="product"]']
            
            for selector in selectors:
                products = await page.query_selector_all(selector)
                if products and len(products) > 5:
                    logger.info(f"Ajio: Using selector '{selector}', found {len(products)} containers")
                    break
            
            if not products:
                logger.warning("Ajio: No product containers found")
                return results
            
            for i, product in enumerate(products[:24]):
                try:
                    # Title
                    title = None
                    title_selectors = [
                        '.nameCls',
                        '.item-title',
                        'div[class*="name"]',
                        'strong'
                    ]
                    
                    for selector in title_selectors:
                        elem = await product.query_selector(selector)
                        if elem:
                            title = await elem.inner_text()
                            if title and title.strip() and len(title.strip()) > 3:
                                title = title.strip()
                                break
                    
                    if not title or len(title) < 3:
                        continue
                    
                    # Price
                    price = None
                    price_selectors = [
                        '.price',
                        'span[class*="price"]',
                        '.priceText',
                        'strong[class*="price"]'
                    ]
                    
                    for selector in price_selectors:
                        elem = await product.query_selector(selector)
                        if elem:
                            price_text = await elem.inner_text()
                            price = self.extract_price(price_text)
                            if price:
                                break
                    
                    if not price:
                        continue
                    
                    # Original price for discount
                    original_price = None
                    original_elem = await product.query_selector('.orgPrice, del, .price-original')
                    if original_elem:
                        original_text = await original_elem.inner_text()
                        original_price = self.extract_price(original_text)
                    
                    # Discount
                    discount_percentage = None
                    if original_price and original_price > price:
                        discount_percentage = int((original_price - price) / original_price * 100)
                    
                    # URL
                    product_url = ""
                    link_elem = await product.query_selector('a')
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.ajio.com{href}" if not href.startswith('http') else href
                    
                    # Image
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
                    logger.info(f"Ajio: {title[:40]}... - ₹{price}")
                    
                    results.append(ProductResult(
                        title=title,
                        price=price,
                        original_price=original_price,
                        discount_percentage=discount_percentage,
                        rating=None,
                        review_count=None,
                        image_url=image_url,
                        product_url=product_url,
                        store_name="Ajio",
                        brand=None,
                        availability=True,
                        shipping_info="Check Delivery",
                        store_color="bg-yellow-600"
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error extracting Ajio product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Ajio: {e}")
        finally:
            if page:
                await page.close()
        
        logger.info(f"Ajio: Returning {len(results)} products")
        return results

    async def scrape_meesho(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape Meesho for products"""
        results = []
        page = None
        
        try:
            page = await self.create_page()
            
            query_parts = [filters.name]
            if filters.color:
                query_parts.append(filters.color)
            query = " ".join(query_parts)
            
            url = f"https://www.meesho.com/search?q={quote_plus(query)}"
            logger.info(f"Scraping Meesho: {url}")
            
            # Try loading
            loaded = False
            for attempt in range(2):
                try:
                    await page.goto(url, wait_until='load', timeout=60000)
                    loaded = True
                    break
                except Exception as e:
                    if attempt == 0:
                        logger.warning(f"Meesho attempt {attempt+1} failed: {e}, retrying...")
                        await asyncio.sleep(3)
                    else:
                        logger.error(f"Meesho: All attempts failed")
                        return results
            
            if not loaded:
                return results
            
            await self.random_delay(4, 6)
            
            # Meesho loads products dynamically - need more scrolling
            for i in range(4):
                await page.evaluate(f'window.scrollTo(0, {(i+1)*1000})')
                await asyncio.sleep(2)
            
            # Meesho product selectors
            products = []
            selectors = [
                'div[data-testid="product-card"]',
                'div[class*="ProductCard"]',
                'div[class*="product-"]',
                'a[href*="/product/"]'
            ]
            
            for selector in selectors:
                products = await page.query_selector_all(selector)
                if products and len(products) > 3:
                    logger.info(f"Meesho: Using selector '{selector}', found {len(products)} containers")
                    break
            
            if not products:
                logger.warning("Meesho: No product containers found")
                return results
            
            for i, product in enumerate(products[:24]):
                try:
                    # Title
                    title = None
                    title_selectors = [
                        'p[class*="ProductCard"]',
                        'p[class*="title"]',
                        'div[class*="name"]',
                        'p'
                    ]
                    
                    for selector in title_selectors:
                        elem = await product.query_selector(selector)
                        if elem:
                            title = await elem.inner_text()
                            if title and title.strip() and len(title.strip()) > 5:
                                title = title.strip()
                                break
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # Price - Meesho shows price prominently
                    price = None
                    price_selectors = [
                        'h5[class*="price"]',
                        'span[class*="price"]',
                        'p[class*="price"]',
                        'h5'
                    ]
                    
                    for selector in price_selectors:
                        elem = await product.query_selector(selector)
                        if elem:
                            price_text = await elem.inner_text()
                            price = self.extract_price(price_text)
                            if price:
                                break
                    
                    if not price:
                        continue
                    
                    # Rating
                    rating = None
                    rating_elem = await product.query_selector('[class*="rating"], span[class*="Rating"]')
                    if rating_elem:
                        rating_text = await rating_elem.inner_text()
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            rating = float(match.group(1))
                    
                    # URL
                    product_url = ""
                    link_elem = await product.query_selector('a') if await product.query_selector('a') else product
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.meesho.com{href}" if not href.startswith('http') else href
                    
                    # Image
                    image_url = None
                    img_elem = await product.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
                    logger.info(f"Meesho: {title[:40]}... - ₹{price}")
                    
                    results.append(ProductResult(
                        title=title,
                        price=price,
                        original_price=None,
                        discount_percentage=None,
                        rating=rating,
                        review_count=None,
                        image_url=image_url,
                        product_url=product_url,
                        store_name="Meesho",
                        brand=None,
                        availability=True,
                        shipping_info="Free Delivery",
                        store_color="bg-purple-600"
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error extracting Meesho product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Meesho: {e}")
        finally:
            if page:
                await page.close()
        
        logger.info(f"Meesho: Returning {len(results)} products")
        return results

    async def scrape_all_stores(self, filters: ProductFilter) -> List[ProductResult]:
        """Scrape all stores concurrently"""
        await self.initialize_browser()
        
        tasks = [
            self.scrape_myntra(filters),
            self.scrape_amazon(filters),
            self.scrape_flipkart(filters),
            self.scrape_ajio(filters),
            self.scrape_meesho(filters),
        ]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        store_names = ['Myntra', 'Amazon', 'Flipkart', 'Ajio', 'Meesho']
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
        logger.info(f"Received image for analysis: {file.filename}, content_type: {file.content_type}")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes
        image_bytes = await file.read()
        logger.info(f"Image size: {len(image_bytes)} bytes")
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Get analyzer instance
        analyzer = get_analyzer()
        
        # Analyze image
        result = analyzer.analyze_image(image_bytes)
        
        logger.info(f"✅ Analysis successful: {result.description}")
        
        return {
            "success": True,
            "analysis": {
                "category": result.category,
                "color": result.color_name,
                "dominant_colors": result.dominant_colors,
                "pattern": result.pattern,
                "style": result.style,
                "confidence": round(result.confidence, 3),
                "description": result.description
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Image analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@app.post("/api/search-by-image")
async def search_by_image(
    file: UploadFile = File(...),
    brand: Optional[str] = Form(None),
    max_price: Optional[float] = Form(None)
):
    """Analyze image and search for similar products"""
    try:
        logger.info(f"=" * 70)
        logger.info(f"IMAGE SEARCH REQUEST - File: {file.filename}")
        logger.info(f"=" * 70)
        
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and analyze image
        image_bytes = await file.read()
        logger.info(f"Image size: {len(image_bytes)} bytes")
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        analyzer = get_analyzer()
        analysis = analyzer.analyze_image(image_bytes)
        
        logger.info(f"✅ AI Analysis complete: {analysis.description}")
        logger.info(f"   Category: {analysis.category}, Color: {analysis.color_name}, Pattern: {analysis.pattern}")
        
        # Create search filter from AI analysis
        # Use simpler search terms for better results
        search_term = f"{analysis.color_name} {analysis.category}"
        
        logger.info(f"🔍 Searching with term: '{search_term}'")
        
        product_filter = ProductFilter(
            name=search_term,
            brand=brand if brand else None,
            category=analysis.category,
            color=analysis.color_name,
            max_price=max_price if max_price else None,
            gender='women'
        )
        
        # Search across stores
        scraper = FashionPriceScraper()
        results = await scraper.scrape_all_stores(product_filter)
        serializable_results = [asdict(result) for result in results]
        
        await scraper.close()
        
        logger.info(f"✅ Search complete: Found {len(serializable_results)} products")
        logger.info(f"=" * 70)
        
        return {
            "success": True,
            "ai_analysis": {
                "category": analysis.category,
                "color": analysis.color_name,
                "dominant_colors": analysis.dominant_colors,
                "pattern": analysis.pattern,
                "style": analysis.style,
                "confidence": round(analysis.confidence, 3),
                "description": analysis.description,
                "search_term": search_term
            },
            "products": serializable_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Image search error: {str(e)}", exc_info=True)
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
        "stores": ["Myntra", "Amazon", "Flipkart", "Ajio", "Meesho"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")