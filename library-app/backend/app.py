from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import requests
from datetime import datetime
from models import db, User, Book, List, ListItem
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote
from functools import wraps

###############################################################################
# FLASK APP + DB CONFIG
###############################################################################
app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Replace with your own secret

db_url = os.getenv('DATABASE_URL', 'postgresql://library_user:password123@db:5432/library_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

###############################################################################
# HELPER FUNCTIONS & DECORATORS
###############################################################################
def current_user():
    """Return the logged-in User object, or None."""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user or user.role not in roles:
                flash('Access denied.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

###############################################################################
# OPEN LIBRARY SEARCH LOGIC
###############################################################################
OPEN_LIBRARY_API_URL = "https://openlibrary.org/search.json"

def perform_search(query, criteria):
    allowed = ['title','author','subject','isbn']
    if criteria not in allowed:
        criteria = 'title'
    params = {
        criteria: query,
        "fields": "title,author_name,first_publish_year,cover_i,"
                  "number_of_pages_median,edition_count,ratings_average,key",
        "limit": 100
    }
    r = requests.get(OPEN_LIBRARY_API_URL, params=params)
    if r.status_code == 200:
        return process_api_response(r.json())
    return []

def process_api_response(data):
    results = []
    for book in data.get("docs", []):
        year = book.get("first_publish_year") or 0
        pages = book.get("number_of_pages_median") or 0
        edition_count = book.get("edition_count") or 0
        ratings = book.get("ratings_average") or 0
        key = book.get("key") or ""
        results.append({
            "title": book.get("title","Unknown Title"),
            "author": ", ".join(book.get("author_name",["Unknown Author"])),
            "year": year,
            "cover_i": book.get("cover_i"),
            "pages": pages,
            "edition_count": edition_count,
            "ratings_average": ratings,
            "key": key
        })
    return results

def clean_subjects(subjects):
    if not subjects:
        return []
    
    # Remove duplicates and sort
    unique_subjects = list(set(subjects))
    
    # Filter out unwanted prefixes and specific terms
    unwanted_prefixes = ['nyt:', 'SOCIAL SCIENCE /', 'BIOGRAPHY & AUTOBIOGRAPHY /', 'PSYCHOLOGY /']
    filtered_subjects = []
    
    for subject in unique_subjects:
        # Skip if subject starts with unwanted prefix
        if any(subject.startswith(prefix) for prefix in unwanted_prefixes):
            continue
        
        # Skip specific unwanted terms
        if subject in ['NEW LIST 20110630', 'New York Times bestseller', 'New York Times reviewed']:
            continue
        
        # Capitalize first letter of each word and add to filtered list
        filtered_subjects.append(subject.title())
    
    # Sort alphabetically
    return sorted(filtered_subjects)

###############################################################################
# ROUTES
###############################################################################

@app.route('/')
def index():
    query = request.args.get('q', '')
    criteria = request.args.get('criteria', 'title')
    results = None

    if query:
        encoded_query = quote(query)
        search_url = f"https://openlibrary.org/search.json?q={encoded_query}"
        
        if criteria == 'author':
            search_url += "&type=author"
        elif criteria == 'subject':
            search_url += "&subject="
        
        try:
            r = requests.get(search_url)
            r.raise_for_status()
            results = r.json()
            
            # Process and organize the results
            processed_results = []
            
            for doc in results.get('docs', []):
                book = {
                    'key': doc.get('key', ''),
                    'title': doc.get('title', 'Unknown Title'),
                    'author_name': doc.get('author_name', ['Unknown Author'])[0] if doc.get('author_name') else 'Unknown Author',
                    'first_publish_year': doc.get('first_publish_year', 'Year unknown'),
                    'cover_i': doc.get('cover_i')
                }
                processed_results.append(book)
            
            # Sort results: books with covers first
            books_with_covers = [book for book in processed_results if book['cover_i']]
            books_without_covers = [book for book in processed_results if not book['cover_i']]
            results = {'docs': books_with_covers + books_without_covers}
            
        except requests.RequestException as e:
            print(f"Search API error: {e}")
            results = {'docs': []}

    return render_template('index.html', results=results)

@app.route('/about')
def about():
    return render_template('about.html')


# ------------------------------
# AUTH
# ------------------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        password = request.form.get('password','').strip()

        if not username or not email or not password:
            flash('All fields required.', 'error')
            return redirect(url_for('register'))

        # check if user or email is taken
        existing = User.query.filter((User.username==username)|(User.email==email)).first()
        if existing:
            flash('Username or email already exists.', 'error')
            return redirect(url_for('register'))

        # create user
        new_user = User(username=username, email=email, role='user')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Set up session for new user
        session['user_id'] = new_user.id
        session['is_admin'] = False  # Explicitly set is_admin to False for new users
        flash('Registration successful! You are logged in.', 'success')
        return redirect(url_for('user_dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_admin'] = (user.role == 'admin')
            
            # Redirect based on user type
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
                
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id',None)
    flash('Logged out.', 'success')
    return redirect(url_for('index'))


# ------------------------------
# SEARCH
# ------------------------------
@app.route('/search')
def search():
    query = request.args.get('q', '')
    criteria = request.args.get('criteria', 'title')
    
    if not query:
        return jsonify([])

    # URL encode the query for the API request
    encoded_query = quote(query)
    search_url = f"https://openlibrary.org/search.json?q={encoded_query}"
    
    # Add criteria to search URL
    if criteria == 'author':
        search_url += "&type=author"
    elif criteria == 'subject':
        search_url += "&subject="
    elif criteria == 'isbn':
        search_url += "&type=isbn"
    
    try:
        r = requests.get(search_url)
        r.raise_for_status()
        results = r.json()
        
        # Process and organize the results
        processed_results = []
        
        for doc in results.get('docs', []):
            book = {
                'key': doc.get('key', ''),
                'title': doc.get('title', 'Unknown Title'),
                'author': ", ".join(doc.get('author_name', ['Unknown Author'])) if doc.get('author_name') else 'Unknown Author',
                'year': doc.get('first_publish_year'),
                'cover_i': doc.get('cover_i'),
                'pages': doc.get('number_of_pages_median'),
                'edition_count': doc.get('edition_count'),
                'ratings_average': doc.get('ratings_average')
            }
            processed_results.append(book)
        
        # Sort results: books with covers first
        books_with_covers = [book for book in processed_results if book['cover_i']]
        books_without_covers = [book for book in processed_results if not book['cover_i']]
        sorted_results = books_with_covers + books_without_covers
        
        return jsonify(sorted_results)
    
    except requests.RequestException as e:
        print(f"Search API error: {e}")
        return jsonify([])


# ------------------------------
# DASHBOARD
# ------------------------------
@app.route('/dashboard')
@login_required
def user_dashboard():  # Regular user dashboard
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get(session['user_id'])
    user_lists = List.query.filter_by(user_id=session['user_id']).all()
    
    # Get the active tab from query parameter
    active_tab = request.args.get('tab', 'overview')
    
    return render_template('dashboard.html', 
                          user=user, 
                          lists=user_lists, 
                          active_tab=active_tab)


# CREATE A NEW LIST
@app.route('/lists/create', methods=['POST'])
@login_required
def create_list():
    name = request.form.get('list_name','').strip()
    if not name:
        flash('List name required.', 'error')
        return redirect(url_for('user_dashboard', tab='create-list'))

    new_list = List(name=name, user_id=current_user().id)
    db.session.add(new_list)
    db.session.commit()

    flash(f"List '{name}' created!", 'success')
    return redirect(url_for('user_dashboard', tab='custom-lists'))  # Show in the lists tab after creation


# RENAME A LIST
@app.route('/lists/<int:list_id>/rename', methods=['POST'])
@login_required
def rename_list(list_id):
    the_list = List.query.get_or_404(list_id)
    if the_list.user_id != current_user().id:
        flash("You don't own this list!", 'error')
        return redirect(url_for('user_dashboard', tab='custom-lists'))

    new_name = request.form.get('new_name','').strip()
    if not new_name:
        flash("List name can't be empty.", 'error')
        return redirect(url_for('user_dashboard', tab='custom-lists'))

    the_list.name = new_name
    db.session.commit()
    flash("List renamed.", 'success')
    return redirect(url_for('user_dashboard', tab='custom-lists'))


# DELETE AN ENTIRE LIST
@app.route('/lists/<int:list_id>/delete', methods=['POST'])
@login_required
def delete_list(list_id):
    the_list = List.query.get_or_404(list_id)
    if the_list.user_id != current_user().id:
        flash("You don't own this list!", 'error')
        return redirect(url_for('user_dashboard', tab='custom-lists'))

    db.session.delete(the_list)
    db.session.commit()
    flash("List deleted.", 'success')
    return redirect(url_for('user_dashboard', tab='custom-lists'))


# REMOVE A SINGLE ITEM (BOOK) FROM A LIST
@app.route('/lists/<int:list_id>/remove_item/<int:item_id>', methods=['POST'])
@login_required
def remove_list_item(list_id, item_id):
    the_list = List.query.get_or_404(list_id)
    if the_list.user_id != current_user().id:
        flash("You don't own this list!", 'error')
        return redirect(url_for('user_dashboard', tab='custom-lists'))

    item = ListItem.query.get_or_404(item_id)
    if item.list_id != list_id:
        flash("That item is not in this list!", 'error')
        return redirect(url_for('user_dashboard', tab='custom-lists'))

    db.session.delete(item)
    db.session.commit()
    flash("Removed book from list.", 'success')
    return redirect(url_for('user_dashboard', tab='custom-lists'))


# ADD A BOOK TO A LIST
@app.route('/add_to_list', methods=['POST'])
@login_required
def add_to_list():
    """
    User picks which list_id to add the book to, from 'book.html'.
    """
    list_id = request.form.get('list_id','')
    book_key = request.form.get('book_key','')
    title = request.form.get('book_title','')
    cover_i = request.form.get('cover_i','')
    author = request.form.get('author','')

    the_list = List.query.get_or_404(list_id)
    if the_list.user_id != current_user().id:
        flash("You do not own that list!", 'error')
        return redirect(url_for('dashboard'))

    new_item = ListItem(
        list_id = the_list.id,
        book_key = book_key,
        title = title,
        author = author,
        cover_i = cover_i
    )
    db.session.add(new_item)
    db.session.commit()

    flash(f"'{title}' added to '{the_list.name}'!", 'success')
    return redirect(url_for('book_detail', work_key=book_key))


# ------------------------------
# BOOK DETAIL
# ------------------------------
@app.route('/book/works/<work_key>')
def book_detail(work_key):
    work_url = f"https://openlibrary.org/works/{work_key}.json"
    r = requests.get(work_url)
    if r.status_code != 200:
        return "Book details not found", 404

    book = r.json()
    
    # Get author details including photo
    author_data = None
    if 'authors' in book and book['authors']:
        author_key = book['authors'][0]['author']['key']
        author_url = f"https://openlibrary.org{author_key}.json"
        author_response = requests.get(author_url)
        if author_response.status_code == 200:
            author_data = author_response.json()
            if 'bio' in author_data:
                author_data['bio'] = author_data['bio']['value'] if isinstance(author_data['bio'], dict) else author_data['bio']

    # Clean up book description
    if 'description' in book:
        book['description'] = book['description']['value'] if isinstance(book['description'], dict) else book['description']

    # Get author's other works
    author_works = []
    if 'authors' in book and book['authors']:
        author_works_url = f"https://openlibrary.org{author_key}/works.json"
        author_works_response = requests.get(author_works_url)
        
        if author_works_response.status_code == 200:
            works_data = author_works_response.json().get('entries', [])
            author_works = [
                {
                    'key': w['key'].replace('/works/', ''),
                    'title': w.get('title', ''),
                    'cover_id': w.get('covers', [None])[0]
                }
                for w in works_data 
                if w['key'] != f"/works/{work_key}" and 'covers' in w and w['covers']
            ][:12]  # Limit to 12 related works

    # Only get user lists if the user is logged in and is not an admin
    user_lists = None
    if 'user_id' in session and not session.get('is_admin'):
        user_lists = List.query.filter_by(user_id=session['user_id']).all()

    return render_template(
        'book.html',
        book=book,
        author=author_data,
        author_works=author_works,
        user_lists=user_lists
    )

# ------------------------------
# ADMIN
# ------------------------------
@app.route('/admin/books')
@login_required
@role_required('admin')
def admin_books():
    books = Book.query.all()
    return render_template('admin/admin_books.html', books=books)

@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    users = User.query.all()
    return render_template('admin/admin_users.html', users=users)

@app.route('/admin/books/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form.get('title', '').strip()
        book.author = request.form.get('author', '').strip()
        book.isbn = request.form.get('isbn', '').strip()
        
        if not book.title or not book.author:
            flash('Title and author are required.', 'error')
            return render_template('admin/admin_edit_book.html', book=book)
        
        db.session.commit()
        flash('Book updated successfully.', 'success')
        return redirect(url_for('admin_books'))
    return render_template('admin/admin_edit_book.html', book=book)

@app.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form.get('username', user.username)
        user.email = request.form.get('email', user.email)
        user.role = request.form.get('role', user.role)
        
        # Handle password change
        new_password = request.form.get('new_password')
        if new_password:
            confirm_password = request.form.get('confirm_password')
            if new_password != confirm_password:
                flash('Passwords do not match!', 'error')
                return render_template('admin/admin_edit_user.html', user=user)
            user.set_password(new_password)
            flash('Password updated successfully.', 'success')
        
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/admin_edit_user.html', user=user)

@app.route('/admin/books/add', methods=['POST'])
@login_required
@role_required('admin')
def add_book():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    isbn = request.form.get('isbn', '').strip()
    
    if not title or not author:
        flash('Title and author are required.', 'error')
        return redirect(url_for('admin_books'))
    
    new_book = Book(
        title=title,
        author=author,
        isbn=isbn,
        added_by_id=current_user().id
    )
    db.session.add(new_book)
    db.session.commit()
    
    flash('Book added successfully.', 'success')
    return redirect(url_for('admin_books'))

@app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully.', 'success')
    return redirect(url_for('admin_books'))

# ------------------------------
# ADMIN AUTH
# ------------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username, role='admin').first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_admin'] = True
            flash('Logged in as administrator.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'error')
            return redirect(url_for('admin_login'))
    return render_template('admin/admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Get counts for admin dashboard
    total_users = User.query.count()
    total_books = Book.query.count()
    total_lists = List.query.count()
    
    return render_template('admin/admin_dashboard.html', 
                         total_users=total_users,
                         total_books=total_books,
                         total_lists=total_lists)

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_user(id):
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('user_dashboard'))
    
    user = User.query.get_or_404(id)
    
    # Prevent admin from deleting themselves
    if user.id == session['user_id']:
        flash('Cannot delete your own admin account.', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        # Delete user's lists first (due to foreign key constraints)
        List.query.filter_by(user_id=user.id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user. Please try again.', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    
    # Get form data
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    # Verify current password
    if not user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('user_dashboard', tab='overview'))
    
    # Check if username or email is changed and if they're already taken
    if (username != user.username or email != user.email):
        existing = User.query.filter(
            ((User.username == username) | (User.email == email)) & 
            (User.id != user.id)
        ).first()
        
        if existing:
            flash('Username or email already exists.', 'error')
            return redirect(url_for('user_dashboard', tab='overview'))
    
    # Update user details
    user.username = username
    user.email = email
    
    # Update password if provided
    if new_password:
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('user_dashboard', tab='overview'))
        
        user.set_password(new_password)
    
    # Save changes
    db.session.commit()
    flash('Your profile has been updated.', 'success')
    return redirect(url_for('user_dashboard', tab='overview'))

###############################################################################
# MAIN
###############################################################################
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This creates all tables
    app.run(host='0.0.0.0', port=5000)
