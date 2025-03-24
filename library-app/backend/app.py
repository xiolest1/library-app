from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import requests
from datetime import datetime
from models import db, User, Book, List, ListItem
from werkzeug.security import generate_password_hash, check_password_hash

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
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    from functools import wraps
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


###############################################################################
# ROUTES
###############################################################################

@app.route('/')
def index():
    return render_template('index.html')

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

        session['user_id'] = new_user.id
        flash('Registration successful! You are logged in.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
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
    q = request.args.get('q','')
    if not q:
        return jsonify([])
    criteria = request.args.get('criteria','title')
    results = perform_search(q, criteria)
    return jsonify(results)


# ------------------------------
# DASHBOARD
# ------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    """
    Show user's lists. Each list can show its items (books).
    """
    user = current_user()
    user_lists = List.query.filter_by(user_id=user.id).all()
    active_tab = request.args.get('tab', 'overview')
    # pass 'lists' and any other data
    return render_template(
        'dashboard.html',
        username=user.username,
        user_info=user,
        lists=user_lists,
        active_tab=active_tab
    )


# CREATE A NEW LIST
@app.route('/lists/create', methods=['POST'])
@login_required
def create_list():
    """
    Create new list, then redirect to 'create-list' tab.
    """
    name = request.form.get('list_name','').strip()
    if not name:
        flash('List name required.', 'error')
        return redirect(url_for('dashboard', tab='create-list'))

    new_list = List(name=name, user_id=current_user().id)
    db.session.add(new_list)
    db.session.commit()

    flash(f"List '{name}' created!", 'success')
    return redirect(url_for('dashboard', tab='create-list'))


# RENAME A LIST
@app.route('/lists/<int:list_id>/rename', methods=['POST'])
@login_required
def rename_list(list_id):
    the_list = List.query.get_or_404(list_id)
    if the_list.user_id != current_user().id:
        flash("You don't own this list!", 'error')
        return redirect(url_for('dashboard', tab='custom-lists'))

    new_name = request.form.get('new_name','').strip()
    if not new_name:
        flash("List name can't be empty.", 'error')
        return redirect(url_for('dashboard', tab='custom-lists'))

    the_list.name = new_name
    db.session.commit()
    flash("List renamed.", 'success')
    return redirect(url_for('dashboard', tab='custom-lists'))


# DELETE AN ENTIRE LIST
@app.route('/lists/<int:list_id>/delete', methods=['POST'])
@login_required
def delete_list(list_id):
    the_list = List.query.get_or_404(list_id)
    if the_list.user_id != current_user().id:
        flash("You don't own this list!", 'error')
        return redirect(url_for('dashboard', tab='custom-lists'))

    db.session.delete(the_list)
    db.session.commit()
    flash("List deleted.", 'success')
    return redirect(url_for('dashboard', tab='custom-lists'))


# REMOVE A SINGLE ITEM (BOOK) FROM A LIST
@app.route('/lists/<int:list_id>/remove_item/<int:item_id>', methods=['POST'])
@login_required
def remove_list_item(list_id, item_id):
    the_list = List.query.get_or_404(list_id)
    if the_list.user_id != current_user().id:
        flash("You don't own this list!", 'error')
        return redirect(url_for('dashboard', tab='custom-lists'))

    item = ListItem.query.get_or_404(item_id)
    if item.list_id != list_id:
        flash("That item is not in this list!", 'error')
        return redirect(url_for('dashboard', tab='custom-lists'))

    db.session.delete(item)
    db.session.commit()
    flash("Removed book from list.", 'success')
    return redirect(url_for('dashboard', tab='custom-lists'))


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
@app.route('/book/<path:work_key>')
def book_detail(work_key):
    """
    Display a single Open Library book detail with 'Add to list' if logged in.
    """
    work_url = f"https://openlibrary.org/{work_key}.json"
    r = requests.get(work_url)
    if r.status_code != 200:
        return "Book details not found", 404

    work_data = r.json()

    # fetch authors
    authors = []
    other_works = []
    if "authors" in work_data:
        for author_obj in work_data["authors"]:
            author_key = author_obj["author"]["key"]
            author_url = f"https://openlibrary.org{author_key}.json"
            ra = requests.get(author_url)
            if ra.status_code == 200:
                authors.append(ra.json())

        # fetch other works by the first author
        if authors:
            first_author_key = authors[0]["key"].split("/")[-1]
            works_url = f"https://openlibrary.org/authors/{first_author_key}/works.json"
            wr = requests.get(works_url)
            if wr.status_code == 200:
                data = wr.json()
                other_works = data.get("entries", [])

    # if user is logged in, pass their lists so they can pick which list to add
    user_lists = []
    if current_user():
        user_lists = List.query.filter_by(user_id=current_user().id).all()

    return render_template(
        'book.html',
        work=work_data,
        authors=authors,
        other_works=other_works,
        user_lists=user_lists  # so the template can show a dropdown
    )

# ------------------------------
# ADMIN
# ------------------------------
@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET','POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    the_user = User.query.get_or_404(user_id)
    if request.method=='POST':
        the_user.username = request.form.get('username', the_user.username)
        the_user.email = request.form.get('email', the_user.email)
        the_user.role = request.form.get('role', the_user.role)
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/edit_user.html', user=the_user)

@app.route('/admin/users/delete/<int:user_id>')
@login_required
@role_required('admin')
def delete_user(user_id):
    the_user = User.query.get_or_404(user_id)
    db.session.delete(the_user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/books')
@login_required
@role_required('admin')
def admin_books():
    all_books = Book.query.all()
    return render_template('admin/books.html', books=all_books)

@app.route('/admin/books/edit/<int:book_id>', methods=['GET','POST'])
@login_required
@role_required('admin')
def edit_book(book_id):
    the_book = Book.query.get_or_404(book_id)
    if request.method=='POST':
        the_book.title = request.form.get('title', the_book.title)
        the_book.author = request.form.get('author', the_book.author)
        db.session.commit()
        flash('Book updated.', 'success')
        return redirect(url_for('admin_books'))
    return render_template('admin/edit_book.html', book=the_book)

###############################################################################
# MAIN
###############################################################################
if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
