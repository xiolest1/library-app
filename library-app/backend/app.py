from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key' 

# In-memory user store , need to switch to a dedicated base later on
users = {}

# Open Library API endpoint for search
OPEN_LIBRARY_API_URL = "https://openlibrary.org/search.json"

def perform_search(query, criteria):
    allowed_criteria = ['title', 'author', 'subject', 'isbn']
    if criteria not in allowed_criteria:
        criteria = 'title'
    params = {
        criteria: query,
        "fields": "title,author_name,first_publish_year,cover_i,number_of_pages_median,edition_count,ratings_average,key",
        "limit": 100  # fetch enough results for pagination and sorting
    }
    response = requests.get(OPEN_LIBRARY_API_URL, params=params)
    if response.status_code == 200:
        return process_api_response(response.json())
    else:
        return []

def process_api_response(data):
    processed = []
    for book in data.get("docs", []):
        year = book.get("first_publish_year") or 0
        pages = book.get("number_of_pages_median") or 0
        edition_count = book.get("edition_count") or 0
        ratings = book.get("ratings_average") or 0
        key = book.get("key") or ""
        processed.append({
            "title": book.get("title", "Unknown Title"),
            "author": ", ".join(book.get("author_name", ["Unknown Author"])),
            "year": year,
            "cover_i": book.get("cover_i"),
            "pages": pages,
            "edition_count": edition_count,
            "ratings_average": ratings,
            "key": key  
        })
    return processed

@app.route('/')
def index():
    # The index page uses real-time search 
    return render_template('index.html')

@app.route('/search')
def search():
    # Returns JSON results for real-time search.
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    criteria = request.args.get('criteria', 'title')
    results = perform_search(query, criteria)
    return jsonify(results)

@app.route('/book/<path:work_key>')
def book_detail(work_key):
    work_url = f"https://openlibrary.org/{work_key}.json"
    work_response = requests.get(work_url)
    if work_response.status_code != 200:
        return "Book details not found", 404
    work_data = work_response.json()
    
    # Fetch author details if available
    authors = []
    other_works = []
    if "authors" in work_data:
        for author_obj in work_data["authors"]:
            author_key = author_obj["author"]["key"]  
            author_url = f"https://openlibrary.org{author_key}.json"
            author_response = requests.get(author_url)
            if author_response.status_code == 200:
                author_data = author_response.json()
                authors.append(author_data)
    
        if authors:
            first_author_key = authors[0]["key"].split("/")[-1] 
            works_url = f"https://openlibrary.org/authors/{first_author_key}/works.json"
            works_response = requests.get(works_url)
            if works_response.status_code == 200:
                works_data = works_response.json()
                other_works = works_data.get("entries", [])
    return render_template('book.html', work=work_data, authors=authors, other_works=other_works)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username in users and users[username]['password'] == password:
            session['user'] = username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))
        if username in users:
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
        users[username] = {'email': email, 'password': password}
        session['user'] = username
        flash('Registration successful.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))
    username = session['user']
    user_info = users.get(username, {})
    return render_template('dashboard.html', username=username, user_info=user_info)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# Admin route to view all users
@app.route('/admin/users')
def admin_users():
    return jsonify(users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
