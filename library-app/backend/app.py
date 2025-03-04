from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = 'default'  # Ignore this as not integrated with a database

# In-memory user store (Not integrated with a database, just for demonstration purposes)
users = {
    # An example would be:
    # 'alice': {
    #   'email': 'alice@example.com',
    #   'password': 'secret',
    #   'lists': {
    #       'favorites': [
    #           { 'key': '/works/OL12345W', 'title': 'Alice in Wonderland', 'cover_i': '12345', 'author': 'Lewis Carroll' }
    #       ]
    #   }
    # }
}

# This the url endpoint for searching Open Library
OPEN_LIBRARY_API_URL = "https://openlibrary.org/search.json"

# This performs a search, can be filtered by given criteria
def perform_search(query, criteria):
    allowed_criteria = ['title', 'author', 'subject', 'isbn']
    if criteria not in allowed_criteria:
        criteria = 'title'
    params = {
        criteria: query,
        "fields": "title,author_name,first_publish_year,cover_i,number_of_pages_median,edition_count,ratings_average,key",
        "limit": 100 # This to allow pagination (Page 1, 2... and so on)
    }
    response = requests.get(OPEN_LIBRARY_API_URL, params=params)
    if response.status_code == 200:
        return process_api_response(response.json())
    else:
        return []

# Processes the JSON response from Open Library. Returns a list of dicts, representing a book with multiple data 
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
            "key": key  # e.g. "/works/OL12345W"
        })
    return processed

# Routes

@app.route('/')
def index():
    # Home page with real-time search
    return render_template('index.html')

# About page
@app.route('/about')
def about():
    return render_template('about.html')

# Login route, attempts to validate user credentials. 
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

# Registration route. Create a new user account in the in-memory store. Has a default "favorites" list
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
        users[username] = {
            'email': email,
            'password': password,
            'lists': {"favorites": []}
        }
        session['user'] = username
        flash('Registration successful.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# Endpoint used by index.html for real-time searching. Expects query and criteria. Returns JSON list of books.
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    criteria = request.args.get('criteria', 'title')
    results = perform_search(query, criteria)
    return jsonify(results)

# User dashboard. Requires a logged-in user. 
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))

    username = session['user']
    user_info = users.get(username, {})
    custom_lists = user_info.get('lists', {"favorites": []})

    # In userdashboard, shows overview tab by default
    active_tab = request.args.get('tab', 'overview')
    # Indicates which list is currently in "edit mode"
    edit_list_name = request.args.get('editList', '')

    return render_template('dashboard.html',
                           username=username,
                           user_info=user_info,
                           custom_lists=custom_lists,
                           active_tab=active_tab,
                           edit_list_name=edit_list_name)

# Create new list for logged in user. 
@app.route('/create_list', methods=['POST'])
def create_list():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    list_name = request.form.get('list_name', '').strip()
    if list_name:
        user = users.get(username)
        if user:
            if 'lists' not in user:
                user['lists'] = {"favorites": []}
            if list_name not in user['lists']:
                user['lists'][list_name] = []
                flash(f"New list '{list_name}' created!", 'success')
            else:
                flash(f"List '{list_name}' already exists.", 'error')
    else:
        flash("List name cannot be empty.", 'error')
    return redirect(url_for('dashboard', tab='create-list'))

# Delete a book from a specific list
@app.route('/delete_book', methods=['POST'])
def delete_book():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    list_name = request.form.get('list_name', '')
    book_key = request.form.get('book_key', '')

    user = users.get(username, {})
    user_lists = user.get('lists', {})
    if list_name in user_lists:
        old_length = len(user_lists[list_name])
        user_lists[list_name] = [b for b in user_lists[list_name] if b.get('key') != book_key]
        new_length = len(user_lists[list_name])
        if new_length < old_length:
            flash("Successfully removed book from list.", "success")
        else:
            flash("No matching book found to remove.", "error")
    else:
        flash(f"List '{list_name}' not found.", "error")
    return redirect(url_for('dashboard', tab='custom-lists', editList=list_name))

# This displays the detail page for a given book. Fetches from Open Library, plus author and other works.
# If user is logged in, provides additional "Add to list" option
@app.route('/book/<path:work_key>')
def book_detail(work_key):
    # e.g. /book/works/OL12345W
    work_url = f"https://openlibrary.org/{work_key}.json"
    work_response = requests.get(work_url)
    if work_response.status_code != 200:
        return "Book details not found", 404

    work_data = work_response.json()
    # Fetches authors detail
    authors = []
    other_works = []
    if "authors" in work_data:
        for author_obj in work_data["authors"]:
            author_key = author_obj["author"]["key"]
            author_url = f"https://openlibrary.org{author_key}.json"
            author_response = requests.get(author_url)
            if author_response.status_code == 200:
                authors.append(author_response.json())

        # fetch other works by the author
        if authors:
            first_author_key = authors[0]["key"].split("/")[-1]
            works_url = f"https://openlibrary.org/authors/{first_author_key}/works.json"
            works_response = requests.get(works_url)
            if works_response.status_code == 200:
                works_data = works_response.json()
                other_works = works_data.get("entries", [])

    # If user is logged in, retrieve their custom lists for the "Add to List" form
    custom_lists = {}
    if 'user' in session:
        user = users.get(session['user'], {})
        custom_lists = user.get('lists', {"favorites": []})

    return render_template('book.html',
                           work=work_data,
                           authors=authors,
                           other_works=other_works,
                           custom_lists=custom_lists)

# Adds a book to chosen list
@app.route('/add_to_list', methods=['POST'])
def add_to_list():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    list_name = request.form.get('list_name', 'favorites')
    book_key = request.form.get('book_key')
    book_title = request.form.get('book_title', '')
    cover_i = request.form.get('cover_i', '')
    author = request.form.get('author', '')

    user = users.get(username)
    if user:
        if 'lists' not in user:
            user['lists'] = {"favorites": []}
        if list_name not in user['lists']:
            user['lists'][list_name] = []

        # Checks if book is already in the list
        if not any(b.get('key') == book_key for b in user['lists'][list_name]):
            user['lists'][list_name].append({
                "key": book_key,
                "title": book_title,
                "cover_i": cover_i,
                "author": author
            })
            flash(f"Book added to '{list_name}'!", "success")
        else:
            flash("That book is already in your list.", "error")

    return redirect(request.referrer or url_for('dashboard'))

# Admin route(Ignore, will be used later on)
@app.route('/admin/users')
def admin_users():
    return jsonify(users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
