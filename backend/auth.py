"""Authentication and user management"""
import os
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from passlib.hash import pbkdf2_sha256
from contextlib import contextmanager

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        """Verify password"""
        return pbkdf2_sha256.verify(password, self.password_hash)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin
        }


class AuthManager:
    """Manage user authentication and registration"""

    def __init__(self, data_folder='data', db_name='users.db'):
        """Initialize authentication manager"""
        self.data_folder = data_folder
        self.db_path = os.path.join(data_folder, db_name)

        # Create engine
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=False
        )

        # Create tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def register_user(self, email, username, password):
        """Register a new user"""
        with self.session_scope() as session:
            # Check if user exists
            existing = session.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()

            if existing:
                if existing.email == email:
                    raise ValueError("Email already registered")
                else:
                    raise ValueError("Username already taken")

            # Create new user
            user = User(
                email=email,
                username=username
            )
            user.set_password(password)

            session.add(user)
            session.flush()

            return user.to_dict()

    def authenticate_user(self, email_or_username, password):
        """Authenticate a user and return user dict if successful"""
        with self.session_scope() as session:
            # Find user by email or username
            user = session.query(User).filter(
                (User.email == email_or_username) | (User.username == email_or_username)
            ).first()

            if not user:
                return None

            if not user.is_active:
                raise ValueError("Account is deactivated")

            if not user.check_password(password):
                return None

            return user.to_dict()

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            return user.to_dict() if user else None

    def get_user_by_email(self, email):
        """Get user by email"""
        with self.session_scope() as session:
            user = session.query(User).filter(User.email == email).first()
            return user.to_dict() if user else None

    def get_user_by_username(self, username):
        """Get user by username"""
        with self.session_scope() as session:
            user = session.query(User).filter(User.username == username).first()
            return user.to_dict() if user else None

    def update_password(self, user_id, new_password):
        """Update user password"""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            user.set_password(new_password)
            return True

    def deactivate_user(self, user_id):
        """Deactivate a user account"""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            user.is_active = False
            return True

    def activate_user(self, user_id):
        """Activate a user account"""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            user.is_active = True
            return True

    def list_users(self):
        """List all users"""
        with self.session_scope() as session:
            users = session.query(User).all()
            return [user.to_dict() for user in users]

    def get_user_count(self):
        """Get total number of users"""
        with self.session_scope() as session:
            return session.query(User).count()
