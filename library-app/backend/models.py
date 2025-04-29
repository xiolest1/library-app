# models.py
"""
Contains the SQLAlchemy models for Users, Books, and any other database tables.
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """
    Represents a user of the system (admin, librarian, or regular user).
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='user')  # 'user', 'librarian', or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to any books they've added (if they're a librarian or admin)
    books_added = db.relationship('Book', backref='added_by', lazy=True)

    def set_password(self, password):
        """
        Hashes the plaintext password and stores it.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifies a plaintext password against the stored hash.
        """
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create_default_users():
        # Check if default admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@library.com',
                role='admin'
            )
            admin.set_password('password123')
            db.session.add(admin)

        # Check if default librarian exists
        librarian = User.query.filter_by(username='librarian').first()
        if not librarian:
            librarian = User(
                username='librarian',
                email='librarian@library.com',
                role='librarian'
            )
            librarian.set_password('password123')
            db.session.add(librarian)

        try:
            db.session.commit()
        except:
            db.session.rollback()


class Book(db.Model):
    """
    Represents a local book record that librarians or admins can add to the system.
    """
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13))
    description = db.Column(db.Text)
    publication_year = db.Column(db.Integer)
    genre = db.Column(db.String(50))
    language = db.Column(db.String(20))
    publisher = db.Column(db.String(200))
    page_count = db.Column(db.Integer)
    added_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Book {self.title} by {self.author}>"


class List(db.Model):
    """
    Represents a custom list (like "Favorites", "Reading Now", etc.) 
    belonging to a specific user.
    """
    __tablename__ = 'lists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Each list belongs to one user
    user = db.relationship('User', backref=db.backref('lists', lazy=True))

    # Relationship to list items
    items = db.relationship('ListItem', backref='list', lazy=True, cascade='all, delete-orphan')

class ListItem(db.Model):
    """
    Represents a book (from Open Library or otherwise) 
    that is attached to a specific user-created List.
    """
    __tablename__ = 'list_items'

    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('lists.id'), nullable=False)
    book_key = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    cover_i = db.Column(db.String(20))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
