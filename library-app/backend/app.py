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
        "q": query,
        "publicDomainOnly": True
    }
    
    response = requests.get(NYPL_API_URL, headers=headers, params=params)
    if response.status_code == 200:
        results = process_api_response(response.json())
        return jsonify(results)
    else:
        return jsonify({"error": "API request failed"}), 500

def process_api_response(data):
    processed = []
    for item in data.get("nyplAPI", {}).get("response", {}).get("result", []):
        processed.append({
            "title": item.get("title"),
            "author": item.get("name", [{}])[0].get("namePart", "Unknown"),
            "year": item.get("dateStart")
        })
    return processed

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
