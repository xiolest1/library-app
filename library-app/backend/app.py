from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)
API_KEY = os.getenv('NYPL_API_KEY')
NYPL_API_URL = "https://api.repo.nypl.org/api/v2/items/search"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q')
    headers = {
        "Authorization": f"Token token={API_KEY}"
    }
    params = {
        "q": f'{query}~',  # Use fuzzy search
        "filters[materialType]": "Text",
        "publicDomainOnly": True,
        "per_page": 20,
        "field": "title,creator,note,dateStart"
    }
    
    response = requests.get(NYPL_API_URL, headers=headers, params=params)
    
    # Temporary debug output
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"API Error: {response.text}")
    
    if response.status_code == 200:
        results = process_api_response(response.json())
        return jsonify(results)
    else:
        return jsonify({"error": "API request failed"}), 500

def process_api_response(data):
    processed = []
    results = data.get("nyplAPI", {}).get("response", {}).get("result", [])
    
    # Debug output
    print(f"Found {len(results)} results")
    
    for item in results:
        # Title handling
        title = item.get("title", "Untitled")
        if isinstance(title, list):
            title = title[0]

        # Author handling
        author = "Unknown Author"
        creator = item.get('creator', [{}])
        if isinstance(creator, list) and len(creator) > 0:
            if isinstance(creator[0], dict):
                author = creator[0].get('namePart', author)
            else:
                author = str(creator[0])

        # Description handling
        description = next(
            (note.get('text', [''])[0] 
             for note in item.get('note', []) 
             if isinstance(note, dict) and note.get('type') == 'content'),
            "No description available"
        )

        # Year handling
        year = item.get('dateStart', 'Unknown year')

        processed.append({
            "title": title,
            "author": author,
            "year": year,
            "description": description
        })
    
    return processed

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)