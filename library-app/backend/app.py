from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Open Library API endpoint
OPEN_LIBRARY_API_URL = "https://openlibrary.org/search.json"

# Routes
@app.route('/')
def index():

    # Shows main search page
    return render_template('index.html')

@app.route('/search')
def search():

    # Gets search results from API
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error" : "Search query is required"}), 400 

    # API request parameters
    params = {
        "q": query,
        "fields": "title,author_name,first_publish_year",
        "limit": 20 
    }
    
    # Make API request to Open Library
    response = requests.get(OPEN_LIBRARY_API_URL, params=params)
    if response.status_code == 200: # Successfully processed
        results = process_api_response(response.json())
        return jsonify(results)
    else:
        return jsonify({"error": "API request failed"}), 500 # return error for failed API request

# Function processes the API data to a cleaner format
# Iterates through books, gets title, joined with authors name and publication year
def process_api_response(data):
    processed = []
    for book in data.get("docs", []):
        processed.append({
            "title": book.get("title", "Unknown Title"),
            "author": ", ".join(book.get("author_name", ["Unknown Author"])),
            "year": book.get("first_publish_year", "Unknown Year")
        })
    return processed

# Runs flask and server on localhost
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
