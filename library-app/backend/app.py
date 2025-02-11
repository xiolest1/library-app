from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# In-memory user store (for demonstration purposes only)
# Format: { username: { 'email': ..., 'password': ... } }
users = {}

# Open Library API endpoint
OPEN_LIBRARY_API_URL = "https://openlibrary.org/search.json"

def perform_search(query, criteria):
    allowed_criteria = ['title', 'author', 'subject', 'isbn']
    if criteria not in allowed_criteria:
        criteria = 'title'
    params = {
        criteria: query,
        "fields": "title,author_name,first_publish_year,cover_i",
        "limit": 20
    }
    response = requests.get(OPEN_LIBRARY_API_URL, params=params)
    if response.status_code == 200:
        return process_api_response(response.json())
    else:
        return []

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

@app.route('/')
def index():
    # The index page does NOT rely on a form submission;
    # the search is handled in real time by client-side JavaScript.
    return render_template('index.html')

@app.route('/search')
def search():
    # This endpoint returns JSON results for the real-time search.
    query = request.args.get('q', '')
    if not query:
        return jsonify([])  # Return an empty list if query is empty
    criteria = request.args.get('criteria', 'title')
    results = perform_search(query, criteria)
    return jsonify(results)

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
        # Save the new user
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

# (Optional) Admin route to view all users—use with caution!
@app.route('/admin/users')
def admin_users():
    # In a real application, restrict access to this route.
    return jsonify(users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
