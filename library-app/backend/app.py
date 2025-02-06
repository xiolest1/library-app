from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Open Library API endpoint
OPEN_LIBRARY_API_URL = "https://openlibrary.org/search.json"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    # Retrieve the search query from the request parameters
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Search query is required"}), 400 
    
    # Get the chosen search criteria (default to 'title' if not provided or invalid)
    criteria = request.args.get('criteria', 'title').lower()
    allowed_criteria = ['title', 'author', 'subject', 'isbn']
    if criteria not in allowed_criteria:
        criteria = 'title'
    
    # Build the API request parameters using the selected criteria as the key
    params = {
        criteria: query,
        "fields": "title,author_name,first_publish_year,cover_i",
        "limit": 20
    }
    
    # Make the API request to Open Library
    response = requests.get(OPEN_LIBRARY_API_URL, params=params)
    if response.status_code == 200:
        results = process_api_response(response.json())
        return jsonify(results)
    else:
        return jsonify({"error": "API request failed"}), 500

def process_api_response(data):
    processed = []
    for book in data.get("docs", []):
        processed.append({
            "title": book.get("title", "Unknown Title"),
            "author": ", ".join(book.get("author_name", ["Unknown Author"])),
            "year": book.get("first_publish_year", "Unknown Year"),
            "cover_i": book.get("cover_i")
        })
    return processed

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
