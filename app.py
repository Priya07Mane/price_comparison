from flask import Flask, render_template, request, jsonify
import random
import time
from datetime import datetime

app = Flask(__name__)

# Mock data to simulate scraped results
mock_stores = [
    {"name": "Amazon", "base_url": "https://www.amazon.in", "color": "bg-orange-500"},
    {"name": "Flipkart", "base_url": "https://www.flipkart.com", "color": "bg-yellow-500"},
    {"name": "Myntra", "base_url": "https://www.myntra.com", "color": "bg-pink-500"},
    {"name": "Ajio", "base_url": "https://www.ajio.com", "color": "bg-indigo-500"},
]

def simulate_price_scraping(product):
    results = []
    base_price = random.randint(50, 550)
    
    # Randomly select 3-4 stores
    selected_stores = random.sample(mock_stores, k=random.randint(3, 4))
    
    for store in selected_stores:
        price_variation = random.uniform(-50, 50)
        price = max(20, base_price + price_variation)
        rating = round(random.uniform(3.0, 5.0), 1)
        reviews = random.randint(100, 5000)
        
        results.append({
            "id": f"{store['name']}-{random.randint(1000, 9999)}",
            "store": store["name"],
            "price": round(price, 2),
            "original_price": round(price * 1.2, 2),
            "rating": rating,
            "reviews": reviews,
            "url": f"{store['base_url']}/search?q={product.replace(' ', '+')}",
            "image": f"https://via.placeholder.com/150x150/f0f0f0/666666?text={store['name']}",
            "in_stock": random.random() > 0.1,
            "shipping": "Free Shipping" if random.random() > 0.5 else f"${random.uniform(5, 20):.2f}",
            "store_color": store["color"]
        })
    
    return sorted(results, key=lambda x: x["price"])

def calculate_savings(results):
    if len(results) < 2:
        return 0
    highest = max(result["price"] for result in results)
    lowest = min(result["price"] for result in results)
    return round(highest - lowest, 2)

@app.route('/')
def index():
    return render_template('index.html', stores=mock_stores, year=datetime.now().year)

@app.route('/search', methods=['POST'])
def search():
    product = request.form.get('product')
    if not product or not product.strip():
        return jsonify({"error": "Please enter a product name"})
    
    # Simulate processing delay
    time.sleep(2)
    
    try:
        results = simulate_price_scraping(product)
        savings = calculate_savings(results)
        return render_template('results.html', results=results, product=product, savings=savings)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch prices. Please try again."})

if __name__ == '__main__':
    app.run(debug=True)